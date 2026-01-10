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
from typing import List, Dict, Optional

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

    def create_list(self, list_name: str) -> str:
        """Creates a new Label (List) in Apollo and returns its ID."""
        url = f"{self.base_url}/labels"
        payload = {"name": list_name}

        logger.info(f"Creating list (Label) named: '{list_name}'...")
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            data = self._handle_response(response)
            label_id = data.get('label', {}).get('id')
            if not label_id:
                raise ValueError("API returned success but no label ID was found.")
            logger.info(f"Successfully created List ID: {label_id}")
            return label_id
        except Exception as e:
            logger.error(f"Failed to create list: {e}")
            sys.exit(1)

    def upload_leads(self, leads: List[Dict], label_id: str, batch_size: int = 10):
        """
        Uploads leads in batches.
        EXPLICITLY disables enrichment to ensure 0 credits are used.
        """
        url = f"{self.base_url}/contacts"
        total_leads = len(leads)
        
        logger.info(f"Starting upload of {total_leads} leads in batches of {batch_size}...")

        for i in range(0, total_leads, batch_size):
            batch = leads[i : i + batch_size]
            current_batch_num = (i // batch_size) + 1
            
            contacts_payload = []
            for lead in batch:
                contact_data = {
                    "email": lead.get("email"),
                    "first_name": lead.get("first_name"),
                    "last_name": lead.get("last_name"),
                    "organization_name": lead.get("company") or lead.get("organization_name"),
                    "title": lead.get("title"),
                    "linkedin_url": lead.get("linkedin_url"),
                    "website_url": lead.get("website"),
                    
                    # --- SAFETY FLAGS TO PREVENT CREDIT USAGE ---
                    # These fields explicitly tell Apollo NOT to look for new data
                    "reveal_phone_number": False,
                    "reveal_personal_emails": False,
                }
                # Remove empty keys (but keep the False flags)
                contact_data = {k: v for k, v in contact_data.items() if v is not None and v != ""}
                contacts_payload.append(contact_data)

            payload = {
                "contacts": contacts_payload,
                "label_ids": [label_id], 
                "run_dedupe": True  # Updates contact if email matches, no credit cost
            }

            self._send_batch_with_retry(url, payload, current_batch_num, len(batch))

    def _send_batch_with_retry(self, url: str, payload: Dict, batch_num: int, item_count: int):
        max_retries = 3
        retry_delay = 60

        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=self.headers, json=payload)
                
                if response.status_code == 429:
                    logger.warning(f"Batch {batch_num}: Rate limit reached. Sleeping {retry_delay}s...")
                    time.sleep(retry_delay)
                    continue 
                
                data = self._handle_response(response)
                created = len(data.get('contacts', []))
                logger.info(f"Batch {batch_num}: Processed {item_count} leads. (Apollo processed: {created})")
                
                time.sleep(1.2) # Rate limit kindness
                return

            except requests.exceptions.RequestException:
                if attempt == max_retries - 1:
                    logger.error(f"Batch {batch_num}: Failed after {max_retries} attempts. Skipping.")
                continue

def load_leads_from_csv(file_path: str) -> List[Dict]:
    if not os.path.exists(file_path):
        logger.error(f"Input file not found: {file_path}")
        sys.exit(1)
    leads = []
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("email"):
                    leads.append(row)
        return leads
    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Bulk upload contacts to Apollo.io (0 Credits).")
    parser.add_argument("list_name", help="Name of the new list/label to create")
    parser.add_argument("input_file", help="Path to the CSV file")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size (Default: 10)")
    parser.add_argument("--api-key", help="Apollo API Key (optional)")

    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("APOLLO_API_KEY")
    if not api_key:
        logger.error("No API Key found. Set APOLLO_API_KEY env var.")
        sys.exit(1)

    uploader = ApolloBatchUploader(api_key)
    leads = load_leads_from_csv(args.input_file)
    if not leads:
        sys.exit(0)

    list_id = uploader.create_list(args.list_name)
    uploader.upload_leads(leads, list_id, args.batch_size)
    logger.info("Job complete.")

if __name__ == "__main__":
    main()

