"""
SAP B1 Service Layer integration for Multiple GRN Creation
Provides methods to interact with SAP B1 APIs for customer, PO, and GRN creation
"""
import logging
import requests
import json
from datetime import datetime
import os

class SAPMultiGRNService:
    """Service class for SAP B1 integration specific to Multiple GRN Creation"""
    
    def __init__(self):
        self.base_url = os.environ.get('SAP_B1_SERVER', '')
        self.username = os.environ.get('SAP_B1_USERNAME', '')
        self.password = os.environ.get('SAP_B1_PASSWORD', '')
        self.company_db = os.environ.get('SAP_B1_COMPANY_DB', '')
        self.session_id = None
        self.session = requests.Session()
        
        # SSL verification enabled by default for security
        # Only disable in development if explicitly set to 'false'
        ssl_verify_env = os.environ.get('SAP_SSL_VERIFY', 'true').lower()
        self.session.verify = ssl_verify_env != 'false'
        
        if not self.session.verify:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            import logging
            logging.warning("⚠️ SAP SSL VERIFICATION DISABLED - This should only be used in development environments!")
    
    def login(self):
        """Login to SAP B1 Service Layer"""
        if not all([self.base_url, self.username, self.password, self.company_db]):
            logging.warning("SAP B1 configuration incomplete")
            return False
        
        login_url = f"{self.base_url}/b1s/v1/Login"
        login_data = {
            "UserName": self.username,
            "Password": self.password,
            "CompanyDB": self.company_db
        }
        
        try:
            response = self.session.post(login_url, json=login_data, timeout=30)
            if response.status_code == 200:
                self.session_id = response.json().get('SessionId')
                logging.info("✅ SAP B1 login successful")
                return True
            else:
                logging.error(f"❌ SAP B1 login failed: {response.text}")
                return False
        except Exception as e:
            logging.error(f"❌ SAP B1 login error: {str(e)}")
            return False
    
    def ensure_logged_in(self):
        """Ensure we have a valid session, login if needed"""
        if not self.session_id:
            return self.login()
        return True
    
    def fetch_business_partners(self, card_type='S'):
        """
        Fetch valid Business Partners (Suppliers/Customers)
        card_type: 'S' for Suppliers, 'C' for Customers
        """
        if not self.ensure_logged_in():
            return {'success': False, 'error': 'SAP login failed'}
        
        try:
            filter_query = f"Valid eq 'tYES' and CardType eq '{card_type}'"
            url = f"{self.base_url}/b1s/v1/BusinessPartners"
            params = {
                '$filter': filter_query,
                '$select': 'CardCode,CardName,Valid,CardType'
            }
            headers = {'Prefer': 'odata.maxpagesize=0'}
            
            response = self.session.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                partners = data.get('value', [])
                logging.info(f"✅ Fetched {len(partners)} business partners")
                return {'success': True, 'partners': partners}
            elif response.status_code == 401:
                self.session_id = None
                if self.login():
                    return self.fetch_business_partners(card_type)
                return {'success': False, 'error': 'Authentication failed'}
            else:
                logging.error(f"❌ Failed to fetch business partners: {response.text}")
                return {'success': False, 'error': response.text}
                
        except Exception as e:
            logging.error(f"❌ Error fetching business partners: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def fetch_all_valid_customers(self):
        """
        Fetch all valid Business Partners for dropdown display
        Uses filter: Valid eq 'tYES' and proper headers as per API spec
        """
        if not self.ensure_logged_in():
            return {'success': False, 'error': 'SAP login failed'}
        
        try:
            filter_query = "Valid eq 'tYES'"
            url = f"{self.base_url}/b1s/v1/BusinessPartners"
            params = {
                '$filter': filter_query,
                '$select': 'CardCode,CardName,Valid'
            }
            headers = {'Prefer': 'odata.maxpagesize=0'}
            
            response = self.session.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                customers = data.get('value', [])
                # Sort by CardName for better dropdown UX
                customers.sort(key=lambda x: x.get('CardName', ''))
                logging.info(f"✅ Fetched {len(customers)} valid customers for dropdown")
                return {'success': True, 'customers': customers}
            elif response.status_code == 401:
                self.session_id = None
                if self.login():
                    return self.fetch_all_valid_customers()
                return {'success': False, 'error': 'Authentication failed'}
            else:
                logging.error(f"❌ Failed to fetch customers: {response.text}")
                return {'success': False, 'error': response.text}
                
        except Exception as e:
            logging.error(f"❌ Error fetching customers: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def fetch_open_purchase_orders(self, card_code):
        """
        Fetch open Purchase Orders for a specific customer/supplier
        Returns only POs with DocumentStatus = 'bost_Open' and open line items
        """
        if not self.ensure_logged_in():
            return {'success': False, 'error': 'SAP login failed'}
        
        try:
            filter_query = f"CardCode eq '{card_code}' and DocumentStatus eq 'bost_Open'"
            url = f"{self.base_url}/b1s/v1/PurchaseOrders"
            params = {
                '$filter': filter_query,
                '$select': 'DocEntry,DocNum,CardCode,CardName,DocDate,DocDueDate,DocTotal,DocumentStatus,DocumentLines'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                pos = data.get('value', [])
                
                open_pos = []
                for po in pos:
                    open_lines = [
                        line for line in po.get('DocumentLines', [])
                        if line.get('LineStatus') == 'bost_Open' and line.get('OpenQuantity', 0) > 0
                    ]
                    
                    if open_lines:
                        po['OpenLines'] = open_lines
                        po['TotalOpenLines'] = len(open_lines)
                        open_pos.append(po)
                
                logging.info(f"✅ Fetched {len(open_pos)} open POs for {card_code}")
                return {'success': True, 'purchase_orders': open_pos}
            elif response.status_code == 401:
                self.session_id = None
                if self.login():
                    return self.fetch_open_purchase_orders(card_code)
                return {'success': False, 'error': 'Authentication failed'}
            else:
                logging.error(f"❌ Failed to fetch POs: {response.text}")
                return {'success': False, 'error': response.text}
                
        except Exception as e:
            logging.error(f"❌ Error fetching POs: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def create_purchase_delivery_note(self, grn_data):
        """
        Create a Purchase Delivery Note (GRN) in SAP B1
        grn_data: Dictionary containing GRN details matching SAP B1 PurchaseDeliveryNotes schema
        """
        if not self.ensure_logged_in():
            return {'success': False, 'error': 'SAP login failed'}
        
        try:
            url = f"{self.base_url}/b1s/v1/PurchaseDeliveryNotes"
            
            response = self.session.post(url, json=grn_data, timeout=60)
            
            if response.status_code == 201:
                result = response.json()
                doc_entry = result.get('DocEntry')
                doc_num = result.get('DocNum')
                logging.info(f"✅ GRN created successfully: DocNum={doc_num}, DocEntry={doc_entry}")
                return {
                    'success': True,
                    'doc_entry': doc_entry,
                    'doc_num': doc_num,
                    'response': result
                }
            elif response.status_code == 401:
                self.session_id = None
                if self.login():
                    return self.create_purchase_delivery_note(grn_data)
                return {'success': False, 'error': 'Authentication failed'}
            else:
                error_msg = response.text
                logging.error(f"❌ Failed to create GRN: {error_msg}")
                return {'success': False, 'error': error_msg, 'status_code': response.status_code}
                
        except Exception as e:
            logging.error(f"❌ Error creating GRN: {str(e)}")
            return {'success': False, 'error': str(e)}
