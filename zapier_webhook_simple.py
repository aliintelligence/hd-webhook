#!/usr/bin/env python3
"""
Simple Zapier Webhook Server (No Flask Required!)
Uses only Python standard library - no dependencies needed!

This receives customer data from Zapier and returns the Lead ID.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from homedepot_lead_manager import HomeDepotLeadManager
from datetime import datetime, timedelta

# Credentials
API_KEY = "qkuDNmpbKpWghYAaceIurrv5fr2Jk3HB"
API_SECRET = "HaPnI70Fj2Y2PEGQ"
MVENDOR_ID = "50005308"
REFERRAL_ASSOCIATE = "MXA9PBV"
SALES_REP = "mxa9pbv"  # Sales rep to assign all leads to (user ID)
DEPARTMENT_NUMBER = "59"  # Department number (2-digit code, 59 = Services)
DEFAULT_APPOINTMENT_TIME = "08:00"  # Default appointment time (8:00 AM)

class WebhookHandler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        """Handle GET requests (health check and test endpoint)"""
        if self.path == '/health':
            response = {
                'status': 'healthy',
                'service': 'Home Depot Lead Creation API',
                'version': '1.0'
            }
            self.send_json_response(response, 200)

        elif self.path == '/test':
            response = {
                'status': 'API is working',
                'endpoint': 'POST /create-lead',
                'example': {
                    'first_name': 'John',
                    'last_name': 'Smith',
                    'phone': '3051234567',
                    'address': '123 Main St',
                    'city': 'Miami',
                    'state': 'FL',
                    'zip_code': '33186',
                    'store_id': '0207'
                }
            }
            self.send_json_response(response, 200)

        else:
            response = {'error': 'Not Found'}
            self.send_json_response(response, 404)

    def do_POST(self):
        """Handle POST requests (create lead)"""
        if self.path == '/create-lead':
            try:
                # Read request body
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                data = json.loads(body.decode('utf-8'))

                print(f"\n{'='*60}")
                print("Received lead creation request from Zapier")
                print(f"Customer: {data.get('first_name')} {data.get('last_name')}")
                print(f"{'='*60}")

                # Validate required fields
                required = ['first_name', 'last_name', 'phone', 'address', 'city', 'state', 'zip_code', 'store_id']
                missing = [f for f in required if not data.get(f)]

                if missing:
                    response = {
                        'success': False,
                        'error': f'Missing required fields: {", ".join(missing)}'
                    }
                    self.send_json_response(response, 400)
                    return

                # Get store_id from request
                store_id = data['store_id']

                # Create manager with the provided store_id
                manager = HomeDepotLeadManager(
                    api_key=API_KEY,
                    api_secret=API_SECRET,
                    mvendor_id=MVENDOR_ID,
                    store_id=store_id
                )

                # Parse appointment
                appointment_date = data.get('appointment_date')
                appointment_time = data.get('appointment_time', DEFAULT_APPOINTMENT_TIME)

                if appointment_date:
                    appointment_str = f"{appointment_date} {appointment_time}:00"
                else:
                    appt = datetime.now() + timedelta(days=3)
                    appointment_str = appt.strftime(f"%m/%d/%Y {appointment_time}:00")

                # Clean phone numbers
                phone = data['phone'].replace('-', '').replace('(', '').replace(')', '').replace(' ', '')
                cell = data.get('cell_phone', '').replace('-', '').replace('(', '').replace(')', '').replace(' ', '')
                work = data.get('work_phone', '').replace('-', '').replace('(', '').replace(')', '').replace(' ', '')

                # STEP 1: Check for existing recent leads (within 14 days)
                print(f"\n🔍 Checking for existing leads for phone: {phone}")
                existing_search = manager.search_recent_leads_by_phone(phone, days=14)

                if existing_search.get('found_recent'):
                    # Found existing lead within 2 weeks - return it instead of creating new
                    service_center_id = existing_search['service_center_id']
                    lead_data = existing_search['most_recent_lead']

                    print(f"✓ Found existing recent lead: {service_center_id}")
                    print(f"  Created: {lead_data.get('Created', 'N/A')}")

                    # Parse appointment if it exists
                    appointment_date = data.get('appointment_date')
                    appointment_time = data.get('appointment_time', '14:00')
                    if appointment_date:
                        appointment_str = f"{appointment_date} {appointment_time}:00"
                    else:
                        appt = datetime.now() + timedelta(days=3)
                        appointment_str = appt.strftime(f"%m/%d/%Y {appointment_time}:00")

                    response = {
                        'success': True,
                        'lead_id': service_center_id,
                        'order_number': service_center_id,
                        'service_center_id': service_center_id,
                        'customer_name': f"{data['first_name']} {data['last_name']}",
                        'appointment_date': appointment_str,
                        'message': 'Using existing recent lead (found within 14 days)',
                        'existing_lead': True,
                        'mvendor_id': MVENDOR_ID,
                        'store_id': store_id
                    }
                    self.send_json_response(response, 200)
                    print(f"\n✓ Returned existing Service Center ID: {service_center_id}")
                    print(f"  (No new lead created - duplicate prevention)\\n")
                    return

                # STEP 2: No recent lead found - create new one
                print(f"\n✓ No recent lead found - creating new lead")

                # Create the lead
                result = manager.create_lead(
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    phone=phone,
                    street_address=data['address'],
                    city=data['city'],
                    state=data['state'],
                    zip_code=data['zip_code'],
                    program_group="SF&I Water Treatment",
                    email=data.get('email'),
                    cell_phone=cell if cell else None,
                    work_phone=work if work else None,
                    address_line2=data.get('address_line2'),
                    cross_streets=data.get('cross_streets'),
                    description=data.get('service_description', 'Water treatment service'),
                    site_comments=data.get('site_comments'),
                    appointment_date=appointment_str,
                    preferred_appointment_date=appointment_str,
                    workflow_status="Confirmed",
                    referral_associate_login=REFERRAL_ASSOCIATE
                )

                if result['success']:
                    lead_id = result['lead_id']

                    # Now lookup the Service Center ID (F-number)
                    print(f"\n⏳ Looking up Service Center ID for {lead_id}...")

                    # Try lookup with 10 second wait (balance between speed and reliability)
                    lookup_result = manager.lookup_lead_by_order_number(lead_id, wait_seconds=10)

                    if lookup_result['success']:
                        service_center_id = lookup_result['service_center_id']
                        print(f"✓ Service Center ID retrieved: {service_center_id}")
                    else:
                        # If not found yet, try once more with another 10 seconds
                        print(f"⚠ Not found yet, trying again...")
                        lookup_result = manager.lookup_lead_by_order_number(lead_id, wait_seconds=10)
                        if lookup_result['success']:
                            service_center_id = lookup_result['service_center_id']
                            print(f"✓ Service Center ID retrieved: {service_center_id}")
                        else:
                            service_center_id = lead_id  # Fallback to order number
                            print(f"⚠ Service Center ID not available yet. Using order number as fallback.")

                    # Assign sales rep to the lead (converts to consultation)
                    print(f"\n👤 Assigning sales rep {SALES_REP} to lead...")
                    assignment_result = manager.create_job_assignment(
                        order_id=service_center_id,
                        user_id=SALES_REP,
                        contact_first_name=data['first_name'],
                        contact_last_name=data['last_name'],
                        assign_type="L",
                        store_number=store_id,
                        department_number=DEPARTMENT_NUMBER
                    )

                    if assignment_result['success']:
                        print(f"✓ Sales rep assigned successfully!")
                        assignment_status = "assigned"
                    else:
                        print(f"⚠ Sales rep assignment failed: {assignment_result.get('error')}")
                        assignment_status = "failed"

                    response = {
                        'success': True,
                        'lead_id': lead_id,
                        'order_number': lead_id,
                        'service_center_id': service_center_id,
                        'customer_name': f"{data['first_name']} {data['last_name']}",
                        'appointment_date': appointment_str,
                        'message': 'Lead created successfully',
                        'sales_rep_assigned': assignment_status,
                        'sales_rep': SALES_REP,
                        'mvendor_id': MVENDOR_ID,
                        'store_id': store_id
                    }
                    self.send_json_response(response, 200)
                    print(f"\n✓ Lead created: {lead_id}")
                    print(f"✓ Service Center ID: {service_center_id}")
                    print(f"✓ Sales Rep: {SALES_REP} ({assignment_status})\n")
                else:
                    response = {
                        'success': False,
                        'error': result.get('error', 'Unknown error'),
                        'message': 'Failed to create lead'
                    }
                    self.send_json_response(response, 500)
                    print(f"\n✗ Lead creation failed: {result.get('error')}\n")

            except json.JSONDecodeError:
                response = {'success': False, 'error': 'Invalid JSON'}
                self.send_json_response(response, 400)

            except Exception as e:
                response = {'success': False, 'error': str(e)}
                self.send_json_response(response, 500)
                print(f"\n✗ Error: {str(e)}\n")

        else:
            response = {'error': 'Not Found'}
            self.send_json_response(response, 404)

    def send_json_response(self, data, status_code):
        """Send JSON response with CORS headers"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def log_message(self, format, *args):
        """Custom log format"""
        return  # Suppress default logging

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 5000))

    print("=" * 80)
    print("HOME DEPOT LEAD CREATION - ZAPIER WEBHOOK SERVER")
    print("=" * 80)
    print(f"\n✓ Server starting on http://0.0.0.0:{PORT}")
    print(f"✓ MVendor ID: {MVENDOR_ID}")
    print(f"✓ Store ID: Dynamic (from request)")
    print(f"\nEndpoints:")
    print(f"  POST http://localhost:{PORT}/create-lead - Create lead")
    print(f"  GET  http://localhost:{PORT}/health      - Health check")
    print(f"  GET  http://localhost:{PORT}/test        - Test endpoint")
    print(f"\n✓ Ready for Zapier webhooks!")
    print("=" * 80)
    print("\nPress Ctrl+C to stop the server\n")

    server = HTTPServer(('0.0.0.0', PORT), WebhookHandler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        server.shutdown()
        print("Server stopped.")
