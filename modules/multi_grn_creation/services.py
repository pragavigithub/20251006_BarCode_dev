"""
SAP B1 Service Layer integration for Multiple GRN Creation
Provides methods to interact with SAP B1 APIs for customer, PO, and GRN creation
"""
import logging
import requests
import json
from datetime import datetime
import os
from flask import current_app

class SAPMultiGRNService:
    """Service class for SAP B1 integration specific to Multiple GRN Creation"""
    
    def __init__(self):
        self.base_url = os.environ.get('SAP_B1_SERVER', '')
        self.username = os.environ.get('SAP_B1_USERNAME', '')
        self.password = os.environ.get('SAP_B1_PASSWORD', '')
        self.company_db = os.environ.get('SAP_B1_COMPANY_DB', '')
        self.session_id = None
        self.session = requests.Session()
        self.session.verify = False  # For development, in production use proper SSL
        self.is_offline = False
        # SSL verification enabled by default for security
        # Only disable if explicitly set to 'false' in environment
        # ssl_verify_env = os.environ.get('SAP_SSL_VERIFY', 'true').lower()
        # self.session.verify = ssl_verify_env == 'true'
        #
        if not self.session.verify:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            logging.warning("⚠️ SAP SSL verification disabled - only use in development with self-signed certificates")
    
    def login(self):
        """Login to SAP B1 Service Layer"""
        if not all([self.base_url, self.username, self.password, self.company_db]):
            logging.warning("⚠️ SAP B1 configuration incomplete. Please check environment variables.")
            logging.warning(f"   SAP_B1_SERVER: {'✓' if self.base_url else '✗'}")
            logging.warning(f"   SAP_B1_USERNAME: {'✓' if self.username else '✗'}")
            logging.warning(f"   SAP_B1_PASSWORD: {'✓' if self.password else '✗'}")
            logging.warning(f"   SAP_B1_COMPANY_DB: {'✓' if self.company_db else '✗'}")
            return False
        
        login_url = f"{self.base_url}/b1s/v1/Login"
        login_data = {
            "UserName": self.username,
            "Password": self.password,
            "CompanyDB": self.company_db
        }
        
        try:
            logging.info(f"🔐 Attempting SAP login to {self.base_url}...")
            response = self.session.post(login_url, json=login_data, timeout=30)
            if response.status_code == 200:
                self.session_id = response.json().get('SessionId')
                logging.info("✅ SAP B1 login successful")
                return True
            else:
                logging.error(f"❌ SAP B1 login failed (Status {response.status_code}): {response.text}")
                return False
        except requests.exceptions.ConnectionError as e:
            logging.error(f"❌ SAP B1 connection failed: Cannot reach {self.base_url}")
            logging.error(f"   This may be a network issue or the SAP server may not be accessible from Replit")
            logging.error(f"   Error details: {str(e)}")
            return False
        except requests.exceptions.Timeout:
            logging.error(f"❌ SAP B1 login timeout: Server did not respond within 30 seconds")
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
            """Fetch all valid Business Partners for dropdown display"""
            if not self.ensure_logged_in():
                error_msg = 'SAP login failed - check SAP credentials and network connectivity'
                logging.error(f"❌ {error_msg}")
                return {'success': False, 'error': error_msg}

            try:
                url = f"{self.base_url}/b1s/v1/BusinessPartners"
                params = {
                    '$filter': f"Valid eq 'tYES'",
                    '$select': 'CardCode,CardName,Valid'
                }
                headers = {'Prefer': 'odata.maxpagesize=0'}

                logging.info(f"📡 Fetching BusinessPartners from SAP: {url}")
                response = self.session.get(url, params=params, headers=headers, timeout=30)

                logging.info(f"📊 SAP Response Status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    customers = [
                        {
                            'CardCode': c['CardCode'],
                            'CardName': c['CardName']
                        }
                        for c in data.get('value', [])
                        if c.get('Valid') == 'tYES'
                    ]
                    logging.info(f"✅ Successfully loaded {len(customers)} valid customers from SAP")
                    return {'success': True, 'customers': customers}

                elif response.status_code == 401:
                    self.session_id = None
                    logging.warning("⚠️ Session expired, attempting re-login...")
                    if self.login():
                        return self.fetch_all_valid_customers()
                    return {'success': False, 'error': 'SAP authentication failed - invalid credentials'}

                else:
                    error_msg = f"SAP API error (Status {response.status_code}): {response.text}"
                    logging.error(f"❌ {error_msg}")
                    return {'success': False, 'error': error_msg}

            except requests.exceptions.ConnectionError as e:
                error_msg = f"Cannot connect to SAP server at {self.base_url} - server may be unreachable from Replit"
                logging.error(f"❌ {error_msg}")
                return {'success': False, 'error': error_msg}
            except requests.exceptions.Timeout:
                error_msg = "SAP request timeout - server did not respond within 30 seconds"
                logging.error(f"❌ {error_msg}")
                return {'success': False, 'error': error_msg}
            except Exception as e:
                error_msg = f"Unexpected error fetching customers: {str(e)}"
                logging.error(f"❌ {error_msg}")
                return {'success': False, 'error': error_msg}

    # def fetch_all_valid_customers(self):
    #     """
    #     Fetch all valid Business Partners for dropdown display
    #     Uses filter: Valid eq 'tYES' and proper headers as per API spec
    #     """
    #     if not self.ensure_logged_in():
    #         return {'success': False, 'error': 'SAP login failed'}
    #
    #     try:
    #         filter_query = "Valid eq 'tYES'"
    #         url = f"{self.base_url}/b1s/v1/BusinessPartners"
    #         params = {
    #             '$filter': filter_query,
    #             '$select': 'CardCode,CardName,Valid'
    #         }
    #         headers = {'Prefer': 'odata.maxpagesize=0'}
    #
    #         response = self.session.get(url, params=params, headers=headers, timeout=30)
    #
    #         if response.status_code == 200:
    #             data = response.json()
    #             customers = data.get('value', [])
    #             # Sort by CardName for better dropdown UX
    #             #customers.sort(key=lambda x: x.get('CardName', ''))
    #             logging.info(f"✅ Fetched {len(customers)} valid customers for dropdown")
    #             return {'success': True, 'customers': customers}
    #         elif response.status_code == 401:
    #             self.session_id = None
    #             if self.login():
    #                 return self.fetch_all_valid_customers()
    #             return {'success': False, 'error': 'Authentication failed'}
    #         else:
    #             logging.error(f"❌ Failed to fetch customers: {response.text}")
    #             return {'success': False, 'error': response.text}
    #
    #     except Exception as e:
    #         logging.error(f"❌ Error fetching customers: {str(e)}")
    #         return {'success': False, 'error': str(e)}
    
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
