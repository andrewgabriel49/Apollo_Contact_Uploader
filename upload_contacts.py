'''
### **Credit Usage Analysis**

**Total Credits Used:** **0 Email Credits / 0 Mobile Credits**

When using the `/v1/contacts` endpoint to upload **data you already possess** (emails, names, companies), Apollo.io treats this as a "Push" or "Import" action, not an "Enrichment" action.

* **Email Credits:** You are **providing** the email address (as the key), not asking Apollo to find it. Therefore, **0 email credits** are consumed.
* **Enrichment:** By default, the `/v1/contacts` endpoint does **not** automatically enrich (reveal phone numbers or personal emails) unless you explicitly set flags to `true`.
* **Deduplication:** The `run_dedupe=True` flag simply checks if the contact exists to avoid duplicates. It does not trigger a "Credit Charge" unless you also ask it to *fetch* missing info.

**Note:** While this costs 0 *credits*, the contacts will count towards your **"Saved Contacts"** limit (which varies by plan, e.g., 10k, unlimited, etc.).


### **Updated Code (Explicitly preventing credit usage)**
'''

import os
import sys
import csv
import time
import json
import logging
import argparse
import requests
from typing import List, Dict, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class ApolloBatchUploader:
    def __init__(self, api_key: str):
        self.base_url = "https://api.apollo.io/v1"
        self.headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "X-Api-Key": api_key
        }

    def _handle_response(self, response: requests.Response) -> Optional[Dict]:
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                logger.warning("Rate limit hit (429).")
                raise
            elif response.status_code == 401:
                logger.error("Authentication failed. Check your APOLLO_API_KEY.")
                sys.exit(1)
            else:
                logger.error(f"HTTP Error {response.status_code}: {response.text}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise

    def wait_for_enrichment(self, minutes: int = 15):
        """Wait for Apollo to process and potentially enrich contacts."""
        logger.info(f"Waiting {minutes} minutes for Apollo to process contacts...")
        
        total_seconds = minutes * 60
        for remaining in range(total_seconds, 0, -30):  # Update every 30 seconds
            mins, secs = divmod(remaining, 60)
            logger.info(f"Time remaining: {mins}m {secs}s")
            time.sleep(30)
        
        logger.info("Wait complete! Starting cleanup...")

    def get_label_by_name(self, list_name: str) -> Optional[str]:
        """Get label ID by name if it exists."""
        url = f"{self.base_url}/labels"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            # The API might return labels as a list directly or in a dict
            labels = data if isinstance(data, list) else data.get('labels', [])
            
            # Search through labels for matching name
            for label in labels:
                if isinstance(label, dict):
                    if label.get('name') == list_name and label.get('modality') == 'contacts':
                        label_id = label.get('id')
                        if label_id:
                            return label_id
            
            return None
        except Exception as e:
            logger.warning(f"Failed to fetch labels: {e}")
            return None

    def create_list(self, list_name: str) -> Tuple[str, str]:
        """Creates a new Label (List) in Apollo and returns (ID, name). If list exists, fetches existing ID."""
        url = f"{self.base_url}/labels"
        payload = {
            "name": list_name,
            "modality": "contacts"  # Required: "contacts", "accounts", or "both"
        }

        logger.info(f"Creating list (Label) named: '{list_name}'...")
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            
            # Check if list already exists
            if response.status_code == 422:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', '')
                    
                    if 'already exists' in error_msg.lower():
                        logger.info(f"List '{list_name}' already exists. Fetching existing list ID...")
                        label_id = self.get_label_by_name(list_name)
                        
                        if label_id:
                            logger.info(f"Found existing List ID: {label_id}")
                            return (label_id, list_name)
                        else:
                            logger.error(f"List exists but could not find ID for '{list_name}'")
                            sys.exit(1)
                except:
                    pass
                
                # If it's a 422 but not "already exists", raise the error
                response.raise_for_status()
            
            # Normal success case
            data = self._handle_response(response)
            label_id = data.get('label', {}).get('id')
            if not label_id:
                raise ValueError("API returned success but no label ID was found.")
            logger.info(f"Successfully created List ID: {label_id}")
            return (label_id, list_name)
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Failed to create list: {e}")
            logger.error(f"Request payload: {json.dumps(payload, indent=2)}")
            if hasattr(e.response, 'text'):
                logger.error(f"API response: {e.response.text}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to create list: {e}")
            sys.exit(1)

    def upload_leads(self, leads: List[Dict], list_name: str):
        """
        Uploads leads one at a time (Apollo API requires single contact per request).
        Uses official API fields only - no enrichment triggering.
        Adds contacts to list using label_names during creation.
        """
        url = f"{self.base_url}/contacts"
        total_leads = len(leads)
        
        logger.info(f"Starting upload of {total_leads} leads...")
        
        successful = 0
        failed = 0
        
        for i, lead in enumerate(leads, 1):
            # CRITICAL: Email is required - validate it exists
            email = lead.get("email") or lead.get("Email") or lead.get("EMAIL")
            if not email:
                logger.warning(f"Lead {i}: Skipping - no email found")
                failed += 1
                continue
            
            # Log first lead's raw data for debugging
            if i == 1:
                logger.info(f"First lead raw data: {json.dumps(lead, indent=2)}")
            
            contact_data = {
                "email": email.strip(),
                "first_name": lead.get("first_name") or lead.get("First Name") or lead.get("First_Name"),
                "last_name": lead.get("last_name") or lead.get("Last Name") or lead.get("Last_Name"),
                "organization_name": lead.get("company") or lead.get("Company") or lead.get("organization_name") or lead.get("Organization Name"),
                "title": lead.get("title") or lead.get("Title") or lead.get("Job Title"),
                "linkedin_url": lead.get("linkedin_url") or lead.get("LinkedIn URL") or lead.get("linkedin"),
                "website_url": lead.get("website") or lead.get("Website") or lead.get("Company Website"),
                
                # Add to list using label_names (per API docs)
                "label_names": [list_name],
                "run_dedupe": True  # Enable deduplication per official docs
            }
            
            # Remove empty keys
            contact_data = {k: v for k, v in contact_data.items() if v is not None and v != ""}
            
            # Ensure email is still present
            if "email" not in contact_data:
                logger.error(f"Lead {i}: Email removed during filtering! Original: {email}")
                failed += 1
                continue
            
            # Warn if only email
            data_fields = [k for k in contact_data.keys() if k not in ['run_dedupe', 'label_names']]
            if len(data_fields) == 1:
                logger.warning(f"Lead {i}: Only has email, no additional data: {email}")
                logger.warning(f"  Available CSV columns: {list(lead.keys())}")
            
            # Show first contact payload
            if i == 1:
                logger.info(f"Sample contact payload: {json.dumps(contact_data, indent=2)}")
            
            # Send single contact
            success = self._send_contact_with_retry(url, contact_data, i, email)
            if success:
                successful += 1
            else:
                failed += 1
            
            # Rate limiting - be nice to Apollo API
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{total_leads} processed ({successful} successful, {failed} failed)")
                time.sleep(2)  # Longer pause every 10 contacts
            else:
                time.sleep(1.2)
        
        logger.info(f"Upload complete: {successful} successful, {failed} failed out of {total_leads} total")

    def get_contacts_in_label(self, label_id: str) -> List[Dict]:
        """Fetch all contacts in a specific label."""
        url = f"{self.base_url}/contacts/search"
        all_contacts = []
        page = 1
        
        logger.info(f"Fetching contacts from label {label_id}...")
        
        while True:
            payload = {
                "label_ids": [label_id],
                "page": page,
                "per_page": 100  # Max per page
            }
            
            try:
                response = requests.post(url, headers=self.headers, json=payload)
                data = self._handle_response(response)
                
                contacts = data.get('contacts', [])
                if not contacts:
                    break
                
                all_contacts.extend(contacts)
                logger.info(f"Fetched page {page}: {len(contacts)} contacts")
                
                # Check if there are more pages
                pagination = data.get('pagination', {})
                if not pagination.get('page') or pagination.get('page') >= pagination.get('total_pages', 0):
                    break
                
                page += 1
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error fetching contacts: {e}")
                break
        
        logger.info(f"Total contacts fetched: {len(all_contacts)}")
        return all_contacts

    def delete_unenriched_contacts(self, label_id: str) -> int:
        """Delete contacts without first_name, last_name, OR organization_name."""
        contacts = self.get_contacts_in_label(label_id)
        
        to_delete = []
        to_keep = []
        
        for contact in contacts:
            first_name = contact.get('first_name', '').strip()
            last_name = contact.get('last_name', '').strip()
            org_name = contact.get('organization_name', '').strip()
            
            # Keep if has ANY of: first name, last name, or company
            if first_name or last_name or org_name:
                to_keep.append(contact)
            else:
                to_delete.append(contact)
        
        logger.info(f"Analysis: {len(to_keep)} contacts to keep (enriched), {len(to_delete)} to delete (not enriched)")
        
        if not to_delete:
            logger.info("No unenriched contacts to delete!")
            return 0
        
        # Delete unenriched contacts
        deleted_count = 0
        for i, contact in enumerate(to_delete, 1):
            contact_id = contact.get('id')
            email = contact.get('email', 'unknown')
            
            if self._delete_contact(contact_id):
                deleted_count += 1
                logger.info(f"Deleted {i}/{len(to_delete)}: {email}")
            else:
                logger.warning(f"Failed to delete {i}/{len(to_delete)}: {email}")
            
            time.sleep(0.5)  # Rate limiting
        
        logger.info(f"Deletion complete: {deleted_count} contacts removed")
        return deleted_count

    def _delete_contact(self, contact_id: str) -> bool:
        """Delete a single contact."""
        url = f"{self.base_url}/contacts/{contact_id}"
        
        try:
            response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"Failed to delete contact {contact_id}: {e}")
            return False

    def export_label_to_csv(self, label_id: str, output_file: str):
        """Export all contacts in a label to CSV with all available fields."""
        contacts = self.get_contacts_in_label(label_id)
        
        if not contacts:
            logger.warning("No contacts to export!")
            return
        
        # Determine all unique fields across all contacts
        all_fields = set()
        for contact in contacts:
            all_fields.update(contact.keys())
        
        # Sort fields for consistent output
        fieldnames = sorted(all_fields)
        
        # Write to CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for contact in contacts:
                # Flatten nested objects to JSON strings if needed
                row = {}
                for field in fieldnames:
                    value = contact.get(field)
                    if isinstance(value, (dict, list)):
                        row[field] = json.dumps(value)
                    else:
                        row[field] = value
                writer.writerow(row)
        
        logger.info(f"Exported {len(contacts)} contacts to {output_file}")
        logger.info(f"Fields included: {len(fieldnames)}")

    def _send_contact_with_retry(self, url: str, contact_data: Dict, contact_num: int, email: str) -> bool:
        """Send a single contact with retry logic"""
        max_retries = 3
        retry_delay = 60

        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=self.headers, json=contact_data)
                
                if response.status_code == 429:
                    logger.warning(f"Contact {contact_num}: Rate limit reached. Sleeping {retry_delay}s...")
                    time.sleep(retry_delay)
                    continue 
                
                data = self._handle_response(response)
                
                # Check if contact was created/found
                contact = data.get('contact', {})
                contact_id = contact.get('id')
                
                if contact_id:
                    # Success! Contact created and added to label
                    logger.info(f"Contact {contact_num}: Created/Updated - {email} (ID: {contact_id})")
                    return True
                else:
                    logger.error(f"Contact {contact_num}: No contact ID in response for {email}")
                    logger.error(f"  API Response: {json.dumps(data, indent=2)}")
                    return False

            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    logger.error(f"Contact {contact_num}: Failed after {max_retries} attempts - {email}: {e}")
                    return False
                time.sleep(5)
                continue
        
        return False

def load_leads_from_csv(file_path: str) -> List[Dict]:
    if not os.path.exists(file_path):
        logger.error(f"Input file not found: {file_path}")
        sys.exit(1)
    leads = []
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            # Log the column names found in CSV
            if reader.fieldnames:
                logger.info(f"CSV columns found: {', '.join(reader.fieldnames)}")
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                # Check for email in common column name variations
                email = row.get("email") or row.get("Email") or row.get("EMAIL")
                
                if email and email.strip():
                    leads.append(row)
                else:
                    logger.warning(f"Row {row_num}: No email found, skipping: {dict(row)}")
            
            logger.info(f"Loaded {len(leads)} leads with valid emails from {file_path}")
        return leads
    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Bulk upload contacts to Apollo.io (0 Credits).")
    parser.add_argument("list_name", help="Name of the new list/label to create")
    parser.add_argument("input_file", help="Path to the CSV file")
    parser.add_argument("--api-key", help="Apollo API Key (optional)")
    parser.add_argument("--cleanup", action="store_true", 
                       help="Wait 15 min, then delete contacts without name/company enrichment")
    parser.add_argument("--wait-minutes", type=int, default=15,
                       help="Minutes to wait before cleanup (default: 15)")
    parser.add_argument("--export", help="Export enriched contacts to CSV file (e.g., output.csv)")

    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("APOLLO_API_KEY")
    if not api_key:
        logger.error("No API Key found. Set APOLLO_API_KEY env var.")
        sys.exit(1)

    uploader = ApolloBatchUploader(api_key)
    leads = load_leads_from_csv(args.input_file)
    
    if not leads:
        logger.error("No valid leads with emails found in the input file. Cannot proceed.")
        sys.exit(1)

    # Step 1: Upload contacts
    label_id, list_name = uploader.create_list(args.list_name)
    uploader.upload_leads(leads, list_name)
    logger.info("Upload complete.")
    
    # Step 2: Optional cleanup (delete unenriched contacts)
    if args.cleanup:
        uploader.wait_for_enrichment(args.wait_minutes)
        deleted = uploader.delete_unenriched_contacts(label_id)
        logger.info(f"Cleanup complete: {deleted} unenriched contacts removed")
    
    # Step 3: Optional export
    if args.export:
        output_path = args.export
        uploader.export_label_to_csv(label_id, output_path)
        logger.info(f"Export complete: {output_path}")
    
    logger.info("Job complete.")

if __name__ == "__main__":
    main()
