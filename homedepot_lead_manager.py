#!/usr/bin/env python3
"""
Home Depot IconX Lead Management API Client
Version: 1.0
Based on IconX Lead Management Services API Specification v1.52

This script provides functionality to:
- Create new leads in the HDSC system
- Update lead status through the workflow
- Schedule appointments/consultations
- Add notes to leads
"""

import requests
import json
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid


class HomeDepotLeadManager:
    """Client for interacting with Home Depot IconX Lead Management API"""

    def __init__(self, api_key: str, api_secret: str, mvendor_id: str, store_id: str, referral_store: str = None):
        """
        Initialize the Lead Manager

        Args:
            api_key: Your API key (appToken)
            api_secret: Your API secret
            mvendor_id: Your MVendor ID
            store_id: Your store ID
            referral_store: Referral store ID (defaults to store_id if not provided)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.mvendor_id = mvendor_id
        self.store_id = store_id
        self.referral_store = referral_store if referral_store else store_id
        self.base_url = "https://api.hs.homedepot.com/iconx/v1"

        # Create Base64 encoded credentials for Basic auth
        credentials = f"{api_key}:{api_secret}"
        self.credentials_base64 = base64.b64encode(credentials.encode()).decode()

        # OAuth token management (tokens expire in 30 minutes, cache for 25)
        self.access_token = None
        self.token_expiry = None

    def _get_access_token(self) -> Optional[str]:
        """
        Obtain an OAuth 2.0 access token using client credentials grant
        Uses Home Depot's /auth/accesstoken endpoint with Basic authentication

        Returns:
            Access token string or None if failed
        """
        # Check if we have a valid token already
        if self.access_token and self.token_expiry:
            if datetime.now() < self.token_expiry:
                return self.access_token

        print("Obtaining new access token from Home Depot...")

        # Home Depot OAuth endpoint (under the same base URL)
        oauth_url = f"{self.base_url}/auth/accesstoken?grant_type=client_credentials"

        # Use Basic authentication with base64 encoded credentials
        headers = {
            "Authorization": f"Basic {self.credentials_base64}",
            "Accept": "application/json"
        }

        try:
            # GET request (not POST) per Home Depot API spec
            response = requests.get(
                oauth_url,
                headers=headers,
                timeout=30
            )

            response.raise_for_status()
            token_data = response.json()

            self.access_token = token_data.get("access_token")
            # Token expires in 30 minutes (1800 seconds), cache for 25 minutes
            expires_in = int(token_data.get("expires_in", 1800))

            # Set expiry time with 5-minute safety margin
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 300)

            print(f"✓ Access token obtained (expires in {expires_in} seconds)")
            return self.access_token

        except requests.exceptions.RequestException as e:
            print(f"✗ Error obtaining access token: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            return None

    def _get_headers(self) -> Dict[str, str]:
        """
        Generate required headers for API requests
        IMPORTANT: Home Depot uses 'appToken' header (not Authorization: Bearer)
        """
        # Get valid access token
        access_token = self._get_access_token()

        if not access_token:
            raise Exception("Failed to obtain access token")

        return {
            "appToken": access_token,  # CRITICAL: Token goes in appToken header!
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def create_lead(
        self,
        first_name: str,
        last_name: str,
        phone: str,
        street_address: str,
        city: str,
        state: str,
        zip_code: str,
        program_group: str,
        email: Optional[str] = None,
        lead_id: Optional[str] = None,
        appointment_date: Optional[str] = None,
        preferred_appointment_date: Optional[str] = None,
        workflow_status: str = "Acknowledged",
        referral_associate_login: Optional[str] = None,
        description: Optional[str] = None,
        cross_streets: Optional[str] = None,
        address_line2: Optional[str] = None,
        cell_phone: Optional[str] = None,
        work_phone: Optional[str] = None,
        home_phone: Optional[str] = None,
        site_comments: Optional[str] = None,
        sp_appointment_id: Optional[str] = None
    ) -> Dict:
        """
        Create a new lead in the HDSC system with optional appointment

        Args:
            first_name: Customer first name
            last_name: Customer last name
            phone: Customer phone number (10 digits)
            street_address: Street address
            city: City
            state: State (2-letter code)
            zip_code: ZIP code
            program_group: SF&I Program Group Name (e.g., 'SF&I Water Treatment', 'SF&I HVAC')
            email: Customer email (optional)
            lead_id: Custom lead ID (optional, will be generated if not provided)
            appointment_date: Scheduled appointment date in "MM/DD/YYYY HH:MM:SS" format (optional)
            preferred_appointment_date: Customer preferred date in "MM/DD/YYYY HH:MM:SS" format (optional)
            workflow_status: Lead status - "Acknowledged" (default) or "Confirmed"
            referral_associate_login: LDAP ID of referring store associate (optional)
            description: Description of the lead (optional)
            cross_streets: Nearest cross streets (optional)
            address_line2: Additional address info (optional)
            cell_phone: Customer cell phone (optional)
            work_phone: Customer work phone (optional)
            home_phone: Customer home phone (optional)
            site_comments: Additional comments about the site (optional)
            sp_appointment_id: Your CRM's appointment ID (optional)

        Returns:
            API response dictionary
        """
        if not lead_id:
            lead_id = f"ORD{int(datetime.now().timestamp())}"

        # Build POBatch payload according to Home Depot API spec (section 3.7.1)
        lead_header = {
            "Id": lead_id,
            "ContactFirstName": first_name,
            "ContactLastName": last_name,
            "Description": description or f"{program_group} Service Request",
            "MMSVCSServiceProviderOrderNumber": lead_id,
            "MMSVPreferredContactPhoneNumber": phone.replace("-", "").replace("(", "").replace(")", "").replace(" ", ""),
            "MMSVSiteAddress": street_address,
            "MMSVSiteCity": city,
            "MMSVSiteState": state,
            "MMSVSitePostalCode": zip_code,
            "MMSVSiteCountry": "US",
            "MMSVStoreNumber": self.store_id,
            "SFIMVendor": int(self.mvendor_id),
            "SFIProgramGroupNameUnconstrained": program_group,
            "SFIReferralStore": self.referral_store,
            "SFIWorkflowOnlyStatus": workflow_status,
            "MMSVCSNeedAck": "N",
            "MMSVCSSubmitLeadFlag": "N",  # N = not ready for settlement yet
            "MMSVCSSVSTypeCode": 10,  # 10 = Service Provider
            "SFIContractDate": datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
            "MMSVCSLeadBatchNumber": f"BATCH{int(datetime.now().timestamp())}"
        }

        # Add optional contact fields
        if email:
            lead_header["MainEmailAddress"] = email
        if cell_phone:
            lead_header["CellularPhone"] = cell_phone.replace("-", "").replace("(", "").replace(")", "").replace(" ", "")
        if work_phone:
            lead_header["ContactWorkPhone"] = work_phone.replace("-", "").replace("(", "").replace(")", "").replace(" ", "")
        if home_phone:
            lead_header["SFIContactHomePhone"] = home_phone.replace("-", "").replace("(", "").replace(")", "").replace(" ", "")

        # Add optional address fields
        if address_line2:
            lead_header["MMSVSiteAddressLine2"] = address_line2
        if cross_streets:
            lead_header["MMSVCrossStreets"] = cross_streets

        # Add optional site fields
        if site_comments:
            lead_header["MMSVSiteComments"] = site_comments

        # Add referral associate if provided
        if referral_associate_login:
            lead_header["SFIReferralAssociateLogin"] = referral_associate_login

        # Add appointment if provided
        if appointment_date:
            appt_date = appointment_date if " " in appointment_date else f"{appointment_date} 09:00:00"
            pref_date = preferred_appointment_date if preferred_appointment_date else appt_date
            if " " not in pref_date:
                pref_date = f"{pref_date} 09:00:00"

            appointment = {
                "Id": "APPT1",
                "OriginalApptDate": "",  # NULL for new appointments (required by HD API spec)
                "ScheduleDate": appt_date,
                "RescheduledFlag": "N",
                "PreferredScheduleDate": pref_date
            }

            if sp_appointment_id:
                appointment["MMSVCSApptField1"] = sp_appointment_id

            lead_header["ListOfMmSvCsServiceProviderAppointment"] = {
                "MmSvCsServiceProviderAppointment": [appointment]
            }

        # Wrap in POBatch format
        payload = {
            "SFILEADPOBATCHICONX_Input": {
                "ListOfMmSvCsServiceProviderLeadInbound": {
                    "MmSvCsServiceProviderLeadHeaderInbound": [lead_header]
                }
            }
        }

        print(f"Creating new lead: {lead_id}")
        print(f"Customer: {first_name} {last_name}")
        print(f"Program: {program_group}")
        print(f"Status: {workflow_status}")
        if appointment_date:
            print(f"Appointment: {appt_date}")

        try:
            response = requests.post(
                f"{self.base_url}/leads/pobatch",
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )

            response_text = response.text

            if not response.ok:
                print(f"✗ API Error - Status: {response.status_code}")
                print(f"Response: {response_text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response_text}",
                    "lead_id": lead_id
                }

            # Try to parse JSON response
            if response_text:
                try:
                    result = json.loads(response_text)
                except json.JSONDecodeError:
                    print(f"✗ Invalid JSON response")
                    print(f"Response: {response_text[:500]}")
                    return {
                        "success": False,
                        "error": "Invalid JSON response from API",
                        "lead_id": lead_id,
                        "raw_response": response_text
                    }
            else:
                print(f"✗ Empty response from API")
                return {
                    "success": False,
                    "error": "Empty response from API",
                    "lead_id": lead_id
                }

            # Check POBatch response format
            output = result.get("SFILEADPOBATCHICONX_Output")

            if output and output.get("Status") == "Success":
                print(f"✓ Lead created successfully!")
                print(f"Order ID: {lead_id}")
                return {
                    "success": True,
                    "lead_id": lead_id,
                    "response": result
                }
            else:
                error_msg = output.get("Error_spcMessage") if output else "Unknown error"
                error_code = output.get("Error_spcCode") if output else "N/A"
                print(f"✗ Lead creation failed: {error_msg}")
                print(f"Error Code: {error_code}")
                return {
                    "success": False,
                    "error": error_msg,
                    "error_code": error_code,
                    "lead_id": lead_id,
                    "response": result
                }

        except requests.exceptions.RequestException as e:
            print(f"✗ Error creating lead: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            return {
                "success": False,
                "error": str(e),
                "lead_id": lead_id
            }

    def update_lead_status(
        self,
        lead_id: str,
        status: str,
        note: Optional[str] = None
    ) -> Dict:
        """
        Update lead status through the workflow

        Status values:
        - "Acknowledged": New lead created
        - "Confirmed": Lead follow-up completed, consultation scheduled
        - "RTS": Ready to sell (quoted)
        - "Cancelled": Lead cancelled

        Args:
            lead_id: The SF&I Lead ID
            status: New workflow status
            note: Optional note to add with the update

        Returns:
            API response dictionary
        """
        update_payload = {
            "SFILeadID": lead_id,
            "SFIWorkflowOnlyStatus": status
        }

        # Wrap in batch request format
        payload = {
            "leads": [update_payload]
        }

        print(f"Updating lead {lead_id} to status: {status}")

        try:
            response = requests.post(
                f"{self.base_url}/leads/pobatch",
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            print(f"✓ Lead status updated successfully!")

            # If note provided, add it separately
            if note:
                self.add_note(lead_id, note)

            return {
                "success": True,
                "lead_id": lead_id,
                "status": status,
                "response": result
            }

        except requests.exceptions.RequestException as e:
            print(f"✗ Error updating lead: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return {
                "success": False,
                "error": str(e),
                "lead_id": lead_id
            }

    def schedule_appointment(
        self,
        lead_id: str,
        appointment_date: str,
        appointment_type: str = "Consultation",
        notes: Optional[str] = None
    ) -> Dict:
        """
        Schedule a consultation/appointment for a lead

        Args:
            lead_id: The SF&I Lead ID
            appointment_date: Appointment date in YYYY-MM-DD format
            appointment_type: Type of appointment (default: "Consultation")
            notes: Optional notes about the appointment

        Returns:
            API response dictionary
        """
        # When scheduling an appointment, update status to "Confirmed"
        # and include appointment details
        appointment_payload = {
            "SFILeadID": lead_id,
            "SFIWorkflowOnlyStatus": "Confirmed",
            "appointments": [{
                "SFIAppointmentDate": appointment_date,
                "SFIAppointmentType": appointment_type,
                "SFIAppointmentStatus": "Scheduled"
            }]
        }

        if notes:
            appointment_payload["appointments"][0]["SFIAppointmentNotes"] = notes

        # Wrap in batch request format
        payload = {
            "leads": [appointment_payload]
        }

        print(f"Scheduling appointment for lead {lead_id}")
        print(f"Date: {appointment_date}")
        print(f"Type: {appointment_type}")

        try:
            response = requests.post(
                f"{self.base_url}/leads/pobatch",
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            print(f"✓ Appointment scheduled successfully!")

            return {
                "success": True,
                "lead_id": lead_id,
                "appointment_date": appointment_date,
                "response": result
            }

        except requests.exceptions.RequestException as e:
            print(f"✗ Error scheduling appointment: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return {
                "success": False,
                "error": str(e),
                "lead_id": lead_id
            }

    def book_consultation(
        self,
        lead_id: str,
        schedule_date: str,
        preferred_schedule_date: Optional[str] = None,
        reschedule: bool = False,
        original_appt_date: Optional[str] = None,
        store_number: Optional[str] = None
    ) -> Dict:
        """
        Book a consultation appointment for a lead using the official HD API format.
        This uses the pobatch endpoint with ListOfMmSvCsServiceProviderAppointment.

        Args:
            lead_id: The F-number lead ID (e.g., "F12345678")
            schedule_date: Appointment date/time in "MM/DD/YYYY HH:MM:SS" format
            preferred_schedule_date: Preferred date/time (defaults to schedule_date)
            reschedule: Set to True if rescheduling an existing appointment
            original_appt_date: Original appointment date (required if reschedule=True)
            store_number: Store number for referral store (e.g., "0207")

        Returns:
            API response dictionary
        """
        if preferred_schedule_date is None:
            preferred_schedule_date = schedule_date

        # Build appointment object per HD API spec
        appointment = {
            "Id": f"APPT-{lead_id}",
            "ScheduleDate": schedule_date,
            "RescheduledFlag": "Y" if reschedule else "N",
            "PreferredScheduleDate": preferred_schedule_date
        }

        if reschedule and original_appt_date:
            appointment["OriginalApptDate"] = original_appt_date

        # Build the payload per HD ICONX API format
        lead_header = {
            "Id": lead_id,
            "SFIMVendor": int(self.mvendor_id),
            "SFIWorkflowOnlyStatus": "Confirmed",
            "MMSVCSNeedAck": "N",
            "MMSVCSSubmitLeadFlag": "Z",
            "ListOfMmSvCsServiceProviderAppointment": {
                "MmSvCsServiceProviderAppointment": [appointment]
            }
        }

        # Add referral store if provided
        if store_number:
            lead_header["SFIReferralStore"] = store_number

        payload = {
            "SFILEADPOBATCHICONX_Input": {
                "ListOfMmSvCsServiceProviderLeadInbound": {
                    "MmSvCsServiceProviderLeadHeaderInbound": lead_header
                }
            }
        }

        print(f"Booking consultation for lead {lead_id}")
        print(f"Schedule Date: {schedule_date}")

        try:
            response = requests.post(
                f"{self.base_url}/leads/pobatch",
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )

            response_text = response.text

            if not response.ok:
                print(f"✗ API Error - Status: {response.status_code}")
                print(f"Response: {response_text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response_text}"
                }

            # Parse response
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Invalid JSON response",
                    "raw_response": response_text
                }

            # Check response - HD API returns Status/Code at top level of output
            output = result.get("SFILEADPOBATCHICONX_Output", {})
            status = output.get("Status", "")
            code = output.get("Code", "")

            if status == "Success" or code == "200":
                print(f"✓ Consultation booked successfully!")
                return {
                    "success": True,
                    "lead_id": lead_id,
                    "schedule_date": schedule_date,
                    "response": result
                }
            else:
                error_msg = output.get("Error_spcMessage") or output.get("Message") or "Unknown error"
                print(f"✗ Consultation booking failed: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "response": result
                }

        except requests.exceptions.RequestException as e:
            print(f"✗ Error booking consultation: {e}")
            return {
                "success": False,
                "error": str(e),
                "lead_id": lead_id
            }

    def add_note(
        self,
        lead_id: str,
        note_text: str,
        note_type: str = "General"
    ) -> Dict:
        """
        Add a note to a lead

        Args:
            lead_id: The SF&I Lead ID
            note_text: The note content
            note_type: Type of note (default: "General")

        Returns:
            API response dictionary
        """
        note_payload = {
            "SFILeadID": lead_id,
            "notes": [{
                "SFINoteText": note_text,
                "SFINoteType": note_type,
                "SFINoteDate": datetime.now().strftime("%Y-%m-%d")
            }]
        }

        # Wrap in batch request format
        payload = {
            "leads": [note_payload]
        }

        print(f"Adding note to lead {lead_id}")

        try:
            response = requests.post(
                f"{self.base_url}/leads/pobatch",
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            print(f"✓ Note added successfully!")

            return {
                "success": True,
                "lead_id": lead_id,
                "response": result
            }

        except requests.exceptions.RequestException as e:
            print(f"✗ Error adding note: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return {
                "success": False,
                "error": str(e),
                "lead_id": lead_id
            }

    def lookup_lead(self, lead_id: str) -> Dict:
        """
        Look up lead by Service Center F-number (Siebel ID)

        Args:
            lead_id: The Service Center ID (F-number)

        Returns:
            Lead information dictionary
        """
        print(f"Looking up lead by F-number: {lead_id}")

        payload = {
            "SFILEADLOOKUPWS_Input": {
                "PageSize": "10",
                "ListOfSfileadbows": {
                    "Sfileadheaderws": [
                        {
                            "Id": lead_id
                        }
                    ]
                },
                "StartRowNum": "0"
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/leads/lookup",
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )

            if not response.ok:
                print(f"✗ API Error - Status: {response.status_code}")
                print(f"Response: {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "lead_id": lead_id
                }

            result = response.json()

            # Extract lead data
            leads = result.get("SFILEADLOOKUPWS_Output", {}).get("ListOfSfileadbows", {}).get("Sfileadheaderws", [])

            if leads and len(leads) > 0:
                print(f"✓ Lead found!")
                return {
                    "success": True,
                    "lead_id": lead_id,
                    "data": leads[0],
                    "full_response": result
                }
            else:
                print(f"✗ Lead not found")
                return {
                    "success": False,
                    "error": "Lead not found in response",
                    "lead_id": lead_id,
                    "full_response": result
                }

        except requests.exceptions.RequestException as e:
            print(f"✗ Error looking up lead: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            return {
                "success": False,
                "error": str(e),
                "lead_id": lead_id
            }

    def search_recent_leads_by_phone(self, phone: str, days: int = 14) -> Dict:
        """
        Search for recent leads by phone number

        Args:
            phone: Customer phone number (will be cleaned of formatting)
            days: How many days back to consider "recent" (default: 14)

        Returns:
            Dict with list of matching leads
        """
        # Clean phone number
        clean_phone = phone.replace("-", "").replace("(", "").replace(")", "").replace(" ", "")

        print(f"Searching for recent leads by phone: {clean_phone} (last {days} days)")

        payload = {
            "SFILEADLOOKUPWS_Input": {
                "PageSize": "50",  # Get up to 50 results
                "ListOfSfileadbows": {
                    "Sfileadheaderws": [
                        {
                            "MMSVPreferredContactPhoneNumber": clean_phone
                        }
                    ]
                },
                "StartRowNum": "0"
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/leads/lookup",
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )

            if not response.ok:
                print(f"✗ API Error - Status: {response.status_code}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "leads": []
                }

            result = response.json()
            leads = result.get("SFILEADLOOKUPWS_Output", {}).get("ListOfSfileadbows", {}).get("Sfileadheaderws", [])

            if not leads:
                print(f"✓ No existing leads found for this phone number")
                return {
                    "success": True,
                    "leads": [],
                    "found_recent": False
                }

            # Filter for recent leads (within specified days)
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_leads = []

            for lead in leads:
                # Try to parse the creation date
                created_date_str = lead.get("Created")  # Or whatever field has the creation date
                if created_date_str:
                    try:
                        # Try common date formats
                        for fmt in ["%m/%d/%Y", "%Y-%m-%d", "%m/%d/%Y %H:%M:%S"]:
                            try:
                                created_date = datetime.strptime(created_date_str.split()[0], fmt)
                                if created_date >= cutoff_date:
                                    recent_leads.append(lead)
                                break
                            except ValueError:
                                continue
                    except:
                        # If we can't parse the date, include it to be safe
                        recent_leads.append(lead)

            if recent_leads:
                print(f"✓ Found {len(recent_leads)} recent lead(s) for this phone number")
                # Return the most recent one
                most_recent = recent_leads[0]
                service_center_id = most_recent.get("Id")
                print(f"  Most recent Service Center ID: {service_center_id}")

                return {
                    "success": True,
                    "found_recent": True,
                    "leads": recent_leads,
                    "most_recent_lead": most_recent,
                    "service_center_id": service_center_id
                }
            else:
                print(f"✓ Found {len(leads)} lead(s) but none within last {days} days")
                return {
                    "success": True,
                    "found_recent": False,
                    "leads": leads
                }

        except requests.exceptions.RequestException as e:
            print(f"✗ Error searching leads: {e}")
            return {
                "success": False,
                "error": str(e),
                "leads": []
            }

    def lookup_lead_by_order_number(self, order_number: str, wait_seconds: int = 30) -> Dict:
        """
        Look up lead by Order Number (ORD...) to get Service Center ID (F-number)

        IMPORTANT: Home Depot processes leads asynchronously. The F-number may not be
        available immediately after creation. This method waits before querying.

        Args:
            order_number: Your order number (e.g., "ORD1760448942")
            wait_seconds: Seconds to wait for HD processing (default: 30)

        Returns:
            Dict with service_center_id (F-number) if found
        """
        import time

        print(f"Looking up Service Center ID for order: {order_number}")

        if wait_seconds > 0:
            print(f"⏳ Waiting {wait_seconds} seconds for Home Depot to process...")
            time.sleep(wait_seconds)

        payload = {
            "SFILEADLOOKUPWS_Input": {
                "PageSize": "10",
                "ListOfSfileadbows": {
                    "Sfileadheaderws": [
                        {
                            "MMSVCSServiceProviderOrderNumber": order_number
                        }
                    ]
                },
                "StartRowNum": "0"
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/leads/lookup",
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )

            if not response.ok:
                print(f"✗ API Error - Status: {response.status_code}")
                print(f"Response: {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "order_number": order_number
                }

            result = response.json()

            # Extract Service Center ID (F-number)
            leads = result.get("SFILEADLOOKUPWS_Output", {}).get("ListOfSfileadbows", {}).get("Sfileadheaderws", [])

            if leads and len(leads) > 0:
                service_center_id = leads[0].get("Id")
                if service_center_id:
                    print(f"✓ Service Center ID found: {service_center_id}")
                    return {
                        "success": True,
                        "order_number": order_number,
                        "service_center_id": service_center_id,
                        "lead_data": leads[0],
                        "full_response": result
                    }
                else:
                    print(f"✗ Service Center ID not in response")
                    return {
                        "success": False,
                        "error": "Service Center ID (Id field) not found in response",
                        "order_number": order_number,
                        "full_response": result
                    }
            else:
                print(f"⚠ Lead not found yet. It may still be processing.")
                return {
                    "success": False,
                    "error": "Lead not found. May still be processing (try waiting longer).",
                    "order_number": order_number,
                    "full_response": result
                }

        except requests.exceptions.RequestException as e:
            print(f"✗ Error looking up lead: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            return {
                "success": False,
                "error": str(e),
                "order_number": order_number
            }

    def complete_workflow(
        self,
        first_name: str,
        last_name: str,
        phone: str,
        street_address: str,
        city: str,
        state: str,
        zip_code: str,
        program_group: str,
        appointment_date: str,
        email: Optional[str] = None
    ) -> Dict:
        """
        Complete workflow: Create lead → Follow up → Open → Schedule

        This is a convenience method that executes your entire business process:
        1. Create new lead (Status: Acknowledged/New)
        2. Add follow-up note (Status: Open)
        3. Schedule consultation (Status: Confirmed/Scheduled)

        Args:
            first_name: Customer first name
            last_name: Customer last name
            phone: Customer phone number
            street_address: Street address
            city: City
            state: State code
            zip_code: ZIP code
            program_group: SF&I Program Group
            appointment_date: Appointment date (YYYY-MM-DD)
            email: Customer email (optional)

        Returns:
            Dictionary with all workflow results
        """
        print("=" * 60)
        print("STARTING COMPLETE LEAD WORKFLOW")
        print("=" * 60)

        results = {
            "workflow_steps": []
        }

        # Step 1: Create new lead
        print("\n[STEP 1] Creating new lead...")
        create_result = self.create_lead(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            street_address=street_address,
            city=city,
            state=state,
            zip_code=zip_code,
            program_group=program_group,
            email=email
        )
        results["workflow_steps"].append({"step": "create", "result": create_result})

        if not create_result["success"]:
            print("\n✗ Workflow failed at lead creation")
            return results

        lead_id = create_result["lead_id"]

        # Step 2: Add follow-up note (moves to "Open" status)
        print("\n[STEP 2] Adding follow-up note...")
        print("Status: Open")
        followup_result = self.add_note(
            lead_id=lead_id,
            note_text=f"Customer contacted for consultation scheduling. Customer: {first_name} {last_name}, Phone: {phone}",
            note_type="Follow-up"
        )
        results["workflow_steps"].append({"step": "followup", "result": followup_result})

        # Step 3: Schedule appointment (moves to "Scheduled" status)
        print("\n[STEP 3] Scheduling consultation...")
        print("Status: Scheduled")
        schedule_result = self.schedule_appointment(
            lead_id=lead_id,
            appointment_date=appointment_date,
            appointment_type="Consultation",
            notes=f"Initial consultation scheduled with {first_name} {last_name}"
        )
        results["workflow_steps"].append({"step": "schedule", "result": schedule_result})

        print("\n" + "=" * 60)
        if schedule_result["success"]:
            print("✓ WORKFLOW COMPLETED SUCCESSFULLY!")
            print(f"Lead ID: {lead_id}")
            print(f"Customer: {first_name} {last_name}")
            print(f"Appointment: {appointment_date}")
        else:
            print("✗ WORKFLOW PARTIALLY COMPLETED")
            print(f"Lead ID: {lead_id}")
        print("=" * 60)

        results["lead_id"] = lead_id
        results["success"] = schedule_result["success"]

        return results

    def create_job_assignment(
        self,
        order_id: str,
        user_id: str,
        contact_first_name: str,
        contact_last_name: str,
        assign_type: str = "L",
        store_number: Optional[str] = None,
        order_number: Optional[str] = None,
        department_number: Optional[str] = None,
        appt_date: Optional[str] = None,
        appt_time: Optional[str] = None
    ) -> Dict:
        """
        Create a new job assignment for a lead or PO (converts lead to consultation)

        Args:
            order_id: The order/lead ID (externalRefNumber)
            user_id: User ID to assign (e.g., "axp8993")
            contact_first_name: Customer first name
            contact_last_name: Customer last name
            assign_type: "L" for Lead, "P" for PO (default: "L")
            store_number: Store number (required for POs)
            order_number: Customer order number (required for POs)
            department_number: Department number
            appt_date: Appointment date in MM/DD/YYYY format
            appt_time: Appointment time in HH:MM format (24-hour)

        Returns:
            API response dictionary
        """
        payload = {
            "assignType": assign_type,
            "externalRefNumber": order_id,
            "mvndrNumber": self.mvendor_id,
            "users": {
                "user": [{
                    "userId": user_id
                }]
            },
            "contactFirstName": contact_first_name,
            "contactLastName": contact_last_name
        }

        # Add optional fields
        if store_number:
            payload["storeNumber"] = store_number
        if order_number:
            payload["orderNumber"] = order_number
        if department_number:
            payload["departmentNumber"] = department_number
        if appt_date:
            payload["apptDate"] = appt_date
        if appt_time:
            payload["apptTime"] = appt_time

        print(f"Creating job assignment for {assign_type} {order_id}")
        print(f"Assigning to user: {user_id}")

        try:
            response = requests.post(
                f"{self.base_url}/jobassignment/new",
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )

            response_text = response.text

            if not response.ok:
                print(f"✗ API Error - Status: {response.status_code}")
                print(f"Response: {response_text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response_text}"
                }

            # Parse response
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Invalid JSON response",
                    "raw_response": response_text
                }

            # Check response status
            header = result.get("header", {})
            if header.get("status") == 200:
                print(f"✓ Job assignment created successfully!")
                return {
                    "success": True,
                    "message": header.get("message"),
                    "response": result
                }
            else:
                print(f"✗ Job assignment failed: {header.get('message')}")
                return {
                    "success": False,
                    "error": header.get("message"),
                    "developer_message": header.get("developerMessage"),
                    "response": result
                }

        except requests.exceptions.RequestException as e:
            print(f"✗ Error creating job assignment: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            return {
                "success": False,
                "error": str(e)
            }

    def add_job_assignment(
        self,
        order_id: str,
        user_id: str,
        contact_first_name: str,
        contact_last_name: str,
        assign_type: str = "L",
        store_number: Optional[str] = None,
        order_number: Optional[str] = None,
        department_number: Optional[str] = None
    ) -> Dict:
        """
        Add an additional user to an existing job assignment

        Args:
            order_id: The order/lead ID (externalRefNumber)
            user_id: User ID to add (e.g., "axp8993")
            contact_first_name: Customer first name
            contact_last_name: Customer last name
            assign_type: "L" for Lead, "P" for PO (default: "L")
            store_number: Store number (required for POs)
            order_number: Customer order number (required for POs)
            department_number: Department number

        Returns:
            API response dictionary
        """
        payload = {
            "assignType": assign_type,
            "externalRefNumber": order_id,
            "mvndrNumber": self.mvendor_id,
            "users": {
                "user": {
                    "userId": user_id
                }
            },
            "contactFirstName": contact_first_name,
            "contactLastName": contact_last_name
        }

        # Add optional fields
        if store_number:
            payload["storeNumber"] = store_number
        if order_number:
            payload["orderNumber"] = order_number
        if department_number:
            payload["departmentNumber"] = department_number

        print(f"Adding job assignment for {assign_type} {order_id}")
        print(f"Adding user: {user_id}")

        try:
            response = requests.post(
                f"{self.base_url}/jobassignment/add",
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )

            response_text = response.text

            if not response.ok:
                print(f"✗ API Error - Status: {response.status_code}")
                print(f"Response: {response_text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response_text}"
                }

            # Parse response
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Invalid JSON response",
                    "raw_response": response_text
                }

            # Check response status
            header = result.get("header", {})
            if header.get("status") == 200:
                print(f"✓ Job assignment added successfully!")
                return {
                    "success": True,
                    "message": header.get("message"),
                    "response": result
                }
            else:
                print(f"✗ Job assignment add failed: {header.get('message')}")
                return {
                    "success": False,
                    "error": header.get("message"),
                    "developer_message": header.get("developerMessage"),
                    "response": result
                }

        except requests.exceptions.RequestException as e:
            print(f"✗ Error adding job assignment: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            return {
                "success": False,
                "error": str(e)
            }

    def complete_job_assignment(
        self,
        order_id: str,
        user_id: str,
        assign_type: str = "L",
        store_number: Optional[str] = None,
        order_number: Optional[str] = None
    ) -> Dict:
        """
        Complete a job assignment for a specific user

        Args:
            order_id: The order/lead ID (externalRefNumber)
            user_id: User ID who completed the job
            assign_type: "L" for Lead, "P" for PO (default: "L")
            store_number: Store number (required for POs)
            order_number: Customer order number (required for POs)

        Returns:
            API response dictionary
        """
        payload = {
            "assignType": assign_type,
            "externalRefNumber": order_id,
            "userId": user_id
        }

        # Add optional fields
        if store_number:
            payload["storeNumber"] = store_number
        if order_number:
            payload["orderNumber"] = order_number

        print(f"Completing job assignment for {assign_type} {order_id}")
        print(f"User: {user_id}")

        try:
            response = requests.post(
                f"{self.base_url}/jobassignment/complete",
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )

            response_text = response.text

            if not response.ok:
                print(f"✗ API Error - Status: {response.status_code}")
                print(f"Response: {response_text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response_text}"
                }

            # Parse response
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "Invalid JSON response",
                    "raw_response": response_text
                }

            # Check response status
            header = result.get("header", {})
            if header.get("status") == 200:
                print(f"✓ Job assignment completed successfully!")
                return {
                    "success": True,
                    "message": header.get("message"),
                    "response": result
                }
            else:
                print(f"✗ Job assignment completion failed: {header.get('message')}")
                return {
                    "success": False,
                    "error": header.get("message"),
                    "developer_message": header.get("developerMessage"),
                    "response": result
                }

        except requests.exceptions.RequestException as e:
            print(f"✗ Error completing job assignment: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            return {
                "success": False,
                "error": str(e)
            }


def main():
    """Example usage of the Home Depot Lead Manager"""

    # Your credentials
    API_KEY = "qkuDNmpbKpWghYAaceIurrv5fr2Jk3HB"
    API_SECRET = "HaPnI70Fj2Y2PEGQ"
    MVENDOR_ID = "50005308"
    STORE_ID = "0207"

    # Initialize the manager
    manager = HomeDepotLeadManager(
        api_key=API_KEY,
        api_secret=API_SECRET,
        mvendor_id=MVENDOR_ID,
        store_id=STORE_ID
    )

    # Example 1: Complete workflow (recommended approach)
    print("\n### EXAMPLE 1: Complete Workflow ###\n")

    # Calculate appointment date (5 days from now)
    appointment_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")

    workflow_result = manager.complete_workflow(
        first_name="John",
        last_name="Smith",
        phone="5551234567",
        street_address="123 Main Street",
        city="Atlanta",
        state="GA",
        zip_code="30301",
        program_group="Flooring",
        appointment_date=appointment_date,
        email="john.smith@example.com"
    )

    # Example 2: Step-by-step approach
    print("\n\n### EXAMPLE 2: Step-by-Step Approach ###\n")

    # Create a lead
    lead_result = manager.create_lead(
        first_name="Jane",
        last_name="Doe",
        phone="5559876543",
        street_address="456 Oak Avenue",
        city="Atlanta",
        state="GA",
        zip_code="30302",
        program_group="Kitchen",
        email="jane.doe@example.com"
    )

    if lead_result["success"]:
        lead_id = lead_result["lead_id"]

        # Add a follow-up note
        manager.add_note(
            lead_id=lead_id,
            note_text="Customer contacted, interested in kitchen remodel",
            note_type="Follow-up"
        )

        # Schedule appointment
        appointment_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        manager.schedule_appointment(
            lead_id=lead_id,
            appointment_date=appointment_date,
            appointment_type="Consultation"
        )

        # Look up the lead
        manager.lookup_lead(lead_id=lead_id)


if __name__ == "__main__":
    main()
