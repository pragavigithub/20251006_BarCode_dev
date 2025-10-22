"""
GRPO (Goods Receipt PO) Routes
All routes related to goods receipt against purchase orders
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from modules.grpo.models import GRPODocument, GRPOItem, GRPOSerialNumber, GRPOBatchNumber
from models import User
import logging
from datetime import datetime
import qrcode
import io
import base64
import json

grpo_bp = Blueprint('grpo', __name__, url_prefix='/grpo', template_folder='templates')

@grpo_bp.route('/')
@login_required
def index():
    """GRPO main page - list all GRPOs for current user"""
    if not current_user.has_permission('grpo'):
        flash('Access denied - GRPO permissions required', 'error')
        return redirect(url_for('dashboard'))
    
    grpos = GRPODocument.query.filter_by(user_id=current_user.id).order_by(GRPODocument.created_at.desc()).all()
    return render_template('grpo/grpo.html', grpos=grpos)

@grpo_bp.route('/detail/<int:grpo_id>')
@login_required
def detail(grpo_id):
    """GRPO detail page"""
    grpo = GRPODocument.query.get_or_404(grpo_id)
    
    # Check permissions
    if grpo.user_id != current_user.id and current_user.role not in ['admin', 'manager', 'qc']:
        flash('Access denied - You can only view your own GRPOs', 'error')
        return redirect(url_for('grpo.index'))
    
    return render_template('grpo/grpo_detail.html', grpo=grpo)

@grpo_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new GRPO"""
    if not current_user.has_permission('grpo'):
        flash('Access denied - GRPO permissions required', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        po_number = request.form.get('po_number')
        
        if not po_number:
            flash('PO number is required', 'error')
            return redirect(url_for('grpo.create'))
        
        # Check if GRPO already exists for this PO
        existing_grpo = GRPODocument.query.filter_by(po_number=po_number, user_id=current_user.id).first()
        if existing_grpo:
            flash(f'GRPO already exists for PO {po_number}', 'warning')
            return redirect(url_for('grpo.detail', grpo_id=existing_grpo.id))
        
        # Create new GRPO
        grpo = GRPODocument(
            po_number=po_number,
            user_id=current_user.id,
            status='draft'
        )
        
        db.session.add(grpo)
        db.session.commit()
        
        logging.info(f"✅ GRPO created for PO {po_number} by user {current_user.username}")
        flash(f'GRPO created for PO {po_number}', 'success')
        return redirect(url_for('grpo.detail', grpo_id=grpo.id))
    
    return render_template('grpo/create_grpo.html')

@grpo_bp.route('/<int:grpo_id>/submit', methods=['POST'])
@login_required
def submit(grpo_id):
    """Submit GRPO for QC approval"""
    try:
        grpo = GRPODocument.query.get_or_404(grpo_id)
        
        # Check permissions
        if grpo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        if grpo.status != 'draft':
            return jsonify({'success': False, 'error': 'Only draft GRPOs can be submitted'}), 400
        
        if not grpo.items:
            return jsonify({'success': False, 'error': 'Cannot submit GRPO without items'}), 400
        
        # Update status
        grpo.status = 'submitted'
        grpo.updated_at = datetime.utcnow()
        db.session.commit()
        
        logging.info(f"📤 GRPO {grpo_id} submitted for QC approval")
        return jsonify({
            'success': True,
            'message': 'GRPO submitted for QC approval',
            'status': 'submitted'
        })
        
    except Exception as e:
        logging.error(f"Error submitting GRPO: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grpo_bp.route('/<int:grpo_id>/approve', methods=['POST'])
@login_required
def approve(grpo_id):
    """QC approve GRPO and post to SAP B1"""
    try:
        grpo = GRPODocument.query.get_or_404(grpo_id)
        
        # Check QC permissions
        if not current_user.has_permission('qc_dashboard') and current_user.role not in ['admin', 'manager']:
            return jsonify({'success': False, 'error': 'QC permissions required'}), 403
        
        if grpo.status != 'submitted':
            return jsonify({'success': False, 'error': 'Only submitted GRPOs can be approved'}), 400
        
        # Get QC notes
        qc_notes = ''
        if request.form:
            qc_notes = request.form.get('qc_notes', '')
        elif request.json:
            qc_notes = request.json.get('qc_notes', '')
        
        # Mark items as approved
        for item in grpo.items:
            item.qc_status = 'approved'
        
        # Update GRPO status
        grpo.status = 'qc_approved'
        grpo.qc_approver_id = current_user.id
        grpo.qc_approved_at = datetime.utcnow()
        grpo.qc_notes = qc_notes
        
        # Initialize SAP integration and post to SAP B1
        from sap_integration import SAPIntegration
        sap = SAPIntegration()
        
        # Log the posting attempt
        logging.info(f"🚀 Attempting to post GRPO {grpo_id} to SAP B1...")
        logging.info(f"GRPO Items: {len(grpo.items)} items, QC Approved: {len([i for i in grpo.items if i.qc_status == 'approved'])}")
        
        # Post GRPO to SAP B1 as Purchase Delivery Note
        sap_result = sap.post_grpo_to_sap(grpo)
        
        # Log the result
        logging.info(f"📡 SAP B1 posting result: {sap_result}")
        
        if sap_result.get('success'):
            grpo.sap_document_number = sap_result.get('sap_document_number')
            grpo.status = 'posted'
            db.session.commit()
            
            logging.info(f"✅ GRPO {grpo_id} QC approved and posted to SAP B1 as {grpo.sap_document_number}")
            return jsonify({
                'success': True,
                'message': f'GRPO approved and posted to SAP B1 as {grpo.sap_document_number}',
                'sap_document_number': grpo.sap_document_number
            })
        else:
            # If SAP posting fails, still mark as QC approved but not posted
            db.session.commit()
            error_msg = sap_result.get('error', 'Unknown SAP error')
            
            logging.warning(f"⚠️ GRPO {grpo_id} QC approved but SAP posting failed: {error_msg}")
            return jsonify({
                'success': False,
                'error': f'GRPO approved but SAP posting failed: {error_msg}',
                'status': 'qc_approved'
            })
        
    except Exception as e:
        logging.error(f"Error approving GRPO: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grpo_bp.route('/<int:grpo_id>/reject', methods=['POST'])
@login_required
def reject(grpo_id):
    """QC reject GRPO"""
    try:
        grpo = GRPODocument.query.get_or_404(grpo_id)
        
        # Check QC permissions
        if not current_user.has_permission('qc_dashboard') and current_user.role not in ['admin', 'manager']:
            return jsonify({'success': False, 'error': 'QC permissions required'}), 403
        
        if grpo.status != 'submitted':
            return jsonify({'success': False, 'error': 'Only submitted GRPOs can be rejected'}), 400
        
        # Get rejection reason
        qc_notes = ''
        if request.form:
            qc_notes = request.form.get('qc_notes', '')
        elif request.json:
            qc_notes = request.json.get('qc_notes', '')
        
        if not qc_notes:
            return jsonify({'success': False, 'error': 'Rejection reason is required'}), 400
        
        # Mark items as rejected
        for item in grpo.items:
            item.qc_status = 'rejected'
        
        # Update GRPO status
        grpo.status = 'rejected'
        grpo.qc_approver_id = current_user.id
        grpo.qc_approved_at = datetime.utcnow()
        grpo.qc_notes = qc_notes
        
        db.session.commit()
        
        logging.info(f"❌ GRPO {grpo_id} rejected by QC")
        return jsonify({
            'success': True,
            'message': 'GRPO rejected by QC',
            'status': 'rejected'
        })
        
    except Exception as e:
        logging.error(f"Error rejecting GRPO: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grpo_bp.route('/<int:grpo_id>/add_item', methods=['POST'])
@login_required
def add_grpo_item(grpo_id):
    """Add item to GRPO with SAP validation and batch/serial number support"""
    try:
        grpo = GRPODocument.query.get_or_404(grpo_id)
        
        # Check permissions
        if grpo.user_id != current_user.id and current_user.role not in ['admin', 'manager']:
            flash('Access denied - You can only modify your own GRPOs', 'error')
            return redirect(url_for('grpo.detail', grpo_id=grpo_id))
        
        if grpo.status != 'draft':
            flash('Cannot add items to non-draft GRPO', 'error')
            return redirect(url_for('grpo.detail', grpo_id=grpo_id))
        
        # Get form data
        item_code = request.form.get('item_code')
        item_name = request.form.get('item_name')
        quantity = float(request.form.get('quantity', 0))
        unit_of_measure = request.form.get('unit_of_measure')
        warehouse_code = request.form.get('warehouse_code')
        bin_location = request.form.get('bin_location')
        batch_number = request.form.get('batch_number')
        expiry_date = request.form.get('expiry_date')
        serial_numbers_json = request.form.get('serial_numbers_json', '')
        batch_numbers_json = request.form.get('batch_numbers_json', '')
        
        if not all([item_code, item_name, quantity > 0]):
            flash('Item Code, Item Name, and Quantity are required', 'error')
            return redirect(url_for('grpo.detail', grpo_id=grpo_id))
        
        # **DUPLICATE PREVENTION LOGIC**
        existing_item = GRPOItem.query.filter_by(
            grpo_id=grpo_id,
            item_code=item_code
        ).first()
        
        if existing_item:
            flash(f'Item {item_code} has already been added to this GRPO. Each item can only be received once per GRPO to avoid duplication.', 'error')
            return redirect(url_for('grpo.detail', grpo_id=grpo_id))
        
        # **SAP VALIDATION - Determine item management type**
        from sap_integration import SAPIntegration
        sap = SAPIntegration()
        validation_result = sap.validate_item_code(item_code)
        
        is_batch_managed = validation_result.get('batch_required', False)
        is_serial_managed = validation_result.get('serial_required', False)
        
        logging.info(f"🔍 Item {item_code} validation: Batch={is_batch_managed}, Serial={is_serial_managed}")
        
        # **VALIDATION: Enforce serial/batch data for managed items**
        if is_serial_managed and not serial_numbers_json:
            flash(f'Item {item_code} is serial managed - serial numbers are required', 'error')
            return redirect(url_for('grpo.detail', grpo_id=grpo_id))
        
        if is_batch_managed and not batch_numbers_json:
            flash(f'Item {item_code} is batch managed - batch numbers are required', 'error')
            return redirect(url_for('grpo.detail', grpo_id=grpo_id))
        
        # Parse expiry date if provided
        expiry_date_obj = None
        if expiry_date:
            try:
                expiry_date_obj = datetime.strptime(expiry_date, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid expiry date format. Use YYYY-MM-DD', 'error')
                return redirect(url_for('grpo.detail', grpo_id=grpo_id))
        
        # Create new GRPO item
        grpo_item = GRPOItem(
            grpo_id=grpo_id,
            item_code=item_code,
            item_name=item_name,
            quantity=quantity,
            received_quantity=quantity,
            unit_of_measure=unit_of_measure,
            warehouse_code=warehouse_code,
            bin_location=bin_location,
            batch_number=batch_number,
            expiry_date=expiry_date_obj,
            qc_status='pending'
        )
        
        db.session.add(grpo_item)
        db.session.flush()
        
        # **SERIAL NUMBER HANDLING**
        if is_serial_managed and serial_numbers_json:
            try:
                serial_numbers = json.loads(serial_numbers_json)
                
                # Validate quantity matches serial entries
                if len(serial_numbers) != int(quantity):
                    flash(f'Serial managed item requires {int(quantity)} serial numbers, but {len(serial_numbers)} provided', 'error')
                    db.session.rollback()
                    return redirect(url_for('grpo.detail', grpo_id=grpo_id))
                
                # Create serial number records with automatic barcode generation
                for idx, serial_data in enumerate(serial_numbers):
                    # Generate barcode for serial number
                    serial_barcode_data = f"SN:{serial_data.get('internal_serial_number')}"
                    serial_barcode = generate_barcode(serial_barcode_data)
                    
                    serial = GRPOSerialNumber(
                        grpo_item_id=grpo_item.id,
                        manufacturer_serial_number=serial_data.get('manufacturer_serial_number', ''),
                        internal_serial_number=serial_data.get('internal_serial_number'),
                        expiry_date=datetime.strptime(serial_data['expiry_date'], '%Y-%m-%d').date() if serial_data.get('expiry_date') else None,
                        manufacture_date=datetime.strptime(serial_data['manufacture_date'], '%Y-%m-%d').date() if serial_data.get('manufacture_date') else None,
                        notes=serial_data.get('notes', ''),
                        barcode=serial_barcode,
                        quantity=1.0,
                        base_line_number=idx
                    )
                    db.session.add(serial)
                    logging.info(f"✅ Generated barcode for serial: {serial_data.get('internal_serial_number')}")
                
                logging.info(f"✅ Added {len(serial_numbers)} serial numbers for item {item_code}")
                
            except json.JSONDecodeError:
                flash('Invalid serial numbers data format', 'error')
                db.session.rollback()
                return redirect(url_for('grpo.detail', grpo_id=grpo_id))
            except Exception as e:
                flash(f'Error processing serial numbers: {str(e)}', 'error')
                db.session.rollback()
                return redirect(url_for('grpo.detail', grpo_id=grpo_id))
        
        # **BATCH NUMBER HANDLING**
        if is_batch_managed and batch_numbers_json:
            try:
                batch_numbers = json.loads(batch_numbers_json)
                
                # Validate total batch quantity matches item quantity
                total_batch_qty = sum(float(b.get('quantity', 0)) for b in batch_numbers)
                if abs(total_batch_qty - quantity) > 0.001:
                    flash(f'Total batch quantity ({total_batch_qty}) must equal item quantity ({quantity})', 'error')
                    db.session.rollback()
                    return redirect(url_for('grpo.detail', grpo_id=grpo_id))
                
                # Create batch number records with automatic barcode generation
                for idx, batch_data in enumerate(batch_numbers):
                    # Generate barcode for batch number
                    batch_barcode_data = f"BATCH:{batch_data.get('batch_number')}"
                    batch_barcode = generate_barcode(batch_barcode_data)
                    
                    batch = GRPOBatchNumber(
                        grpo_item_id=grpo_item.id,
                        batch_number=batch_data.get('batch_number'),
                        quantity=float(batch_data.get('quantity', 0)),
                        manufacturer_serial_number=batch_data.get('manufacturer_serial_number', ''),
                        internal_serial_number=batch_data.get('internal_serial_number', ''),
                        expiry_date=datetime.strptime(batch_data['expiry_date'], '%Y-%m-%d').date() if batch_data.get('expiry_date') else None,
                        barcode=batch_barcode,
                        base_line_number=idx
                    )
                    db.session.add(batch)
                    logging.info(f"✅ Generated barcode for batch: {batch_data.get('batch_number')}")
                
                logging.info(f"✅ Added {len(batch_numbers)} batch numbers for item {item_code}")
                
            except json.JSONDecodeError:
                flash('Invalid batch numbers data format', 'error')
                db.session.rollback()
                return redirect(url_for('grpo.detail', grpo_id=grpo_id))
            except Exception as e:
                flash(f'Error processing batch numbers: {str(e)}', 'error')
                db.session.rollback()
                return redirect(url_for('grpo.detail', grpo_id=grpo_id))
        
        db.session.commit()
        
        logging.info(f"✅ Item {item_code} added to GRPO {grpo_id} (Batch: {is_batch_managed}, Serial: {is_serial_managed})")
        flash(f'Item {item_code} successfully added to GRPO', 'success')
        
    except Exception as e:
        logging.error(f"Error adding item to GRPO: {str(e)}")
        flash(f'Error adding item: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('grpo.detail', grpo_id=grpo_id))

@grpo_bp.route('/items/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_grpo_item(item_id):
    """Delete GRPO item"""
    try:
        item = GRPOItem.query.get_or_404(item_id)
        grpo = item.grpo_document
        
        # Check permissions
        if grpo.user_id != current_user.id and current_user.role not in ['admin', 'manager']:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        if grpo.status != 'draft':
            return jsonify({'success': False, 'error': 'Cannot delete items from non-draft GRPO'}), 400
        
        grpo_id = grpo.id
        item_code = item.item_code
        
        db.session.delete(item)
        db.session.commit()
        
        logging.info(f"🗑️ Item {item_code} deleted from GRPO {grpo_id}")
        return jsonify({'success': True, 'message': f'Item {item_code} deleted'})
        
    except Exception as e:
        logging.error(f"Error deleting GRPO item: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grpo_bp.route('/validate-item/<string:item_code>', methods=['GET'])
@login_required
def validate_item_code(item_code):
    """Validate ItemCode and return batch/serial requirements"""
    try:
        from sap_integration import SAPIntegration
        
        sap = SAPIntegration()
        validation_result = sap.validate_item_code(item_code)
        
        logging.info(f"🔍 ItemCode validation for {item_code}: {validation_result}")
        
        return jsonify(validation_result)
        
    except Exception as e:
        logging.error(f"Error validating ItemCode {item_code}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'item_code': item_code,
            'batch_required': False,
            'serial_required': False,
            'manage_method': 'N'
        }), 500

def generate_barcode(data):
    """Generate QR code barcode and return base64 encoded image"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        logging.error(f"Error generating barcode: {str(e)}")
        return None

@grpo_bp.route('/items/<int:item_id>/serial-numbers', methods=['GET', 'POST'])
@login_required
def manage_serial_numbers(item_id):
    """Get or add serial numbers for a GRPO item"""
    item = GRPOItem.query.get_or_404(item_id)
    
    # Check permissions
    if item.grpo_document.user_id != current_user.id and current_user.role not in ['admin', 'manager']:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    if request.method == 'GET':
        # Return existing serial numbers
        serials = [{
            'id': sn.id,
            'manufacturer_serial_number': sn.manufacturer_serial_number,
            'internal_serial_number': sn.internal_serial_number,
            'expiry_date': sn.expiry_date.isoformat() if sn.expiry_date else None,
            'manufacture_date': sn.manufacture_date.isoformat() if sn.manufacture_date else None,
            'notes': sn.notes,
            'barcode': sn.barcode,
            'quantity': float(sn.quantity),
            'base_line_number': sn.base_line_number
        } for sn in item.serial_numbers]
        
        return jsonify({'success': True, 'serial_numbers': serials})
    
    elif request.method == 'POST':
        # Add new serial number
        try:
            data = request.json
            
            # Check if internal serial number already exists
            existing = GRPOSerialNumber.query.filter_by(
                internal_serial_number=data['internal_serial_number']
            ).first()
            
            if existing:
                return jsonify({
                    'success': False,
                    'error': f"Serial number '{data['internal_serial_number']}' already exists"
                }), 400
            
            # Generate barcode
            barcode_data = f"SN:{data['internal_serial_number']}"
            barcode = generate_barcode(barcode_data)
            
            # Create serial number entry
            serial = GRPOSerialNumber(
                grpo_item_id=item_id,
                manufacturer_serial_number=data.get('manufacturer_serial_number'),
                internal_serial_number=data['internal_serial_number'],
                expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() if data.get('expiry_date') else None,
                manufacture_date=datetime.strptime(data['manufacture_date'], '%Y-%m-%d').date() if data.get('manufacture_date') else None,
                notes=data.get('notes'),
                barcode=barcode,
                quantity=data.get('quantity', 1.0),
                base_line_number=data.get('base_line_number', 0)
            )
            
            db.session.add(serial)
            db.session.commit()
            
            logging.info(f"✅ Serial number {data['internal_serial_number']} added to item {item_id}")
            
            return jsonify({
                'success': True,
                'serial_number': {
                    'id': serial.id,
                    'manufacturer_serial_number': serial.manufacturer_serial_number,
                    'internal_serial_number': serial.internal_serial_number,
                    'expiry_date': serial.expiry_date.isoformat() if serial.expiry_date else None,
                    'manufacture_date': serial.manufacture_date.isoformat() if serial.manufacture_date else None,
                    'notes': serial.notes,
                    'barcode': serial.barcode,
                    'quantity': float(serial.quantity),
                    'base_line_number': serial.base_line_number
                }
            })
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error adding serial number: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

@grpo_bp.route('/serial-numbers/<int:serial_id>', methods=['DELETE'])
@login_required
def delete_serial_number(serial_id):
    """Delete a serial number"""
    try:
        serial = GRPOSerialNumber.query.get_or_404(serial_id)
        
        # Check permissions
        if serial.grpo_item.grpo_document.user_id != current_user.id and current_user.role not in ['admin', 'manager']:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        db.session.delete(serial)
        db.session.commit()
        
        logging.info(f"🗑️ Serial number {serial.internal_serial_number} deleted")
        return jsonify({'success': True, 'message': 'Serial number deleted'})
        
    except Exception as e:
        logging.error(f"Error deleting serial number: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grpo_bp.route('/items/<int:item_id>/batch-numbers', methods=['GET', 'POST'])
@login_required
def manage_batch_numbers(item_id):
    """Get or add batch numbers for a GRPO item"""
    item = GRPOItem.query.get_or_404(item_id)
    
    # Check permissions
    if item.grpo_document.user_id != current_user.id and current_user.role not in ['admin', 'manager']:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    if request.method == 'GET':
        # Return existing batch numbers
        batches = [{
            'id': bn.id,
            'batch_number': bn.batch_number,
            'quantity': float(bn.quantity),
            'base_line_number': bn.base_line_number,
            'manufacturer_serial_number': bn.manufacturer_serial_number,
            'internal_serial_number': bn.internal_serial_number,
            'expiry_date': bn.expiry_date.isoformat() if bn.expiry_date else None,
            'barcode': bn.barcode
        } for bn in item.batch_numbers]
        
        return jsonify({'success': True, 'batch_numbers': batches})
    
    elif request.method == 'POST':
        # Add new batch number
        try:
            data = request.json
            
            # Generate barcode
            barcode_data = f"BATCH:{data['batch_number']}"
            barcode = generate_barcode(barcode_data)
            
            # Create batch number entry
            batch = GRPOBatchNumber(
                grpo_item_id=item_id,
                batch_number=data['batch_number'],
                quantity=data['quantity'],
                base_line_number=data.get('base_line_number', 0),
                manufacturer_serial_number=data.get('manufacturer_serial_number'),
                internal_serial_number=data.get('internal_serial_number'),
                expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() if data.get('expiry_date') else None,
                barcode=barcode
            )
            
            db.session.add(batch)
            db.session.commit()
            
            logging.info(f"✅ Batch number {data['batch_number']} added to item {item_id}")
            
            return jsonify({
                'success': True,
                'batch_number': {
                    'id': batch.id,
                    'batch_number': batch.batch_number,
                    'quantity': float(batch.quantity),
                    'base_line_number': batch.base_line_number,
                    'manufacturer_serial_number': batch.manufacturer_serial_number,
                    'internal_serial_number': batch.internal_serial_number,
                    'expiry_date': batch.expiry_date.isoformat() if batch.expiry_date else None,
                    'barcode': batch.barcode
                }
            })
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error adding batch number: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

@grpo_bp.route('/batch-numbers/<int:batch_id>', methods=['DELETE'])
@login_required
def delete_batch_number(batch_id):
    """Delete a batch number"""
    try:
        batch = GRPOBatchNumber.query.get_or_404(batch_id)
        
        # Check permissions
        if batch.grpo_item.grpo_document.user_id != current_user.id and current_user.role not in ['admin', 'manager']:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        db.session.delete(batch)
        db.session.commit()
        
        logging.info(f"🗑️ Batch number {batch.batch_number} deleted")
        return jsonify({'success': True, 'message': 'Batch number deleted'})
        
    except Exception as e:
        logging.error(f"Error deleting batch number: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grpo_bp.route('/validate-serial/<string:serial_number>', methods=['GET'])
@login_required
def validate_serial_unique(serial_number):
    """Check if serial number is unique"""
    try:
        existing = GRPOSerialNumber.query.filter_by(
            internal_serial_number=serial_number
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'unique': False,
                'message': f"Serial number '{serial_number}' already exists"
            })
        else:
            return jsonify({
                'success': True,
                'unique': True,
                'message': f"Serial number '{serial_number}' is available"
            })
            
    except Exception as e:
        logging.error(f"Error validating serial number: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500