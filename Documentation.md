# Apollo Contact Uploader - Complete Documentation

**Version:** 2.0  
**Author:** Apollo Integration Script  
**Last Updated:** January 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Requirements](#requirements)
4. [Installation](#installation)
5. [Quick Start](#quick-start)
6. [Command-Line Interface](#command-line-interface)
7. [Workflows](#workflows)
8. [CSV Format](#csv-format)
9. [API Endpoints Used](#api-endpoints-used)
10. [Credit Usage](#credit-usage)
11. [Examples](#examples)
12. [Advanced Usage](#advanced-usage)
13. [Troubleshooting](#troubleshooting)
14. [FAQ](#faq)
15. [Best Practices](#best-practices)

---

## Overview

The Apollo Contact Uploader is a Python script that enables bulk contact management in Apollo.io through their REST API. It supports uploading contacts, automatic enrichment workflows, smart cleanup of unenriched data, and full data exports.

### Key Capabilities

- **Zero-credit upload** - Upload contact data you already possess without consuming API credits
- **Email-only contacts** - Minimal CSV format supported (just email addresses)
- **Auto-enrichment workflow** - Wait for Apollo to enrich contacts, then cleanup and export
- **Smart deduplication** - Automatically handles existing contacts and lists
- **Full data export** - Download enriched contacts with 40+ fields
- **Production-ready** - Comprehensive logging, error handling, and retry logic

---

## Features

### Core Features

✅ **Email-based contact creation**  
Upload contacts using email as the primary identifier. Additional fields optional.

✅ **Official API compliance**  
Uses only documented Apollo API endpoints and fields.

✅ **Automatic deduplication**  
Prevents duplicate contacts using `run_dedupe` parameter. Updates existing contacts instead of creating duplicates.

✅ **Duplicate list handling**  
Automatically reuses existing lists instead of failing with errors.

✅ **Label assignment**  
Contacts are automatically added to your specified list during creation.

### Auto-Enrichment Features

✅ **Wait timer**  
Configurable wait period for Apollo to enrich contacts in the background.

✅ **Smart cleanup**  
Automatically deletes contacts that weren't enriched (no name or company data).

✅ **Full data export**  
Exports enriched contacts to CSV with all available Apollo fields (40+ columns).

✅ **Complete workflow**  
Upload → Wait → Cleanup → Export in a single command.

### Technical Features

✅ **Comprehensive logging**  
Detailed console output showing every operation and result.

✅ **Error handling**  
Automatic retry logic for rate limits and transient failures.

✅ **Progress tracking**  
Real-time progress indicators for long-running operations.

✅ **Pagination support**  
Handles large contact lists (up to 50,000 contacts per export).

---

## Requirements

### System Requirements

- **Python**: 3.7 or higher
- **Operating System**: Linux, macOS, or Windows
- **Internet**: Required for API communication

### Python Dependencies

```
requests>=2.25.0
```

Install with:
```bash
pip install requests
```

### Apollo Requirements

- **Apollo.io Account**: Active account required
- **API Key**: Obtainable from Apollo settings
- **API Access**: Varies by Apollo plan tier

---

## Installation

### Step 1: Download the Script

Save `upload_contacts.py` to your working directory.

### Step 2: Install Dependencies

```bash
pip install requests
```

Or if using a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install requests
```

### Step 3: Set Up API Key

**Option A: Environment Variable (Recommended)**
```bash
export APOLLO_API_KEY="your_api_key_here"
```

Add to your shell profile (`.bashrc`, `.zshrc`) to make permanent:
```bash
echo 'export APOLLO_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

**Option B: Command-Line Argument**
```bash
python3 upload_contacts.py "List" file.csv --api-key "your_api_key_here"
```

### Step 4: Verify Installation

```bash
python3 upload_contacts.py --help
```

You should see the help documentation.

---

## Quick Start

### Basic Upload (No Enrichment)

```bash
python3 upload_contacts.py "My List" contacts.csv
```

Uploads all contacts from `contacts.csv` to a new list called "My List".

### Full Auto-Enrichment Workflow

```bash
python3 upload_contacts.py "My List" contacts.csv --cleanup --export enriched.csv
```

1. Uploads contacts (0 credits)
2. Waits 15 minutes for Apollo enrichment
3. Deletes unenriched contacts
4. Exports enriched contacts to `enriched.csv`

### Quick Test

```bash
# Create test file
cat > test.csv << EOF
email
test1@example.com
test2@demo.com
test3@sample.org
EOF

# Run 1-minute test
python3 upload_contacts.py "Test" test.csv --cleanup --wait-minutes 1 --export results.csv
```

---

## Command-Line Interface

### Syntax

```bash
python3 upload_contacts.py <list_name> <input_file> [OPTIONS]
```

### Required Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `list_name` | Name of the list/label to create in Apollo | `"Q1 Prospects"` |
| `input_file` | Path to CSV file containing contact data | `contacts.csv` |

### Optional Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--api-key` | string | (env var) | Apollo API key |
| `--cleanup` | flag | False | Enable auto-cleanup of unenriched contacts |
| `--wait-minutes` | integer | 15 | Minutes to wait before cleanup |
| `--export` | string | None | Export enriched contacts to CSV file |

### Examples

**Simple upload:**
```bash
python3 upload_contacts.py "Sales Leads" leads.csv
```

**With cleanup after 30 minutes:**
```bash
python3 upload_contacts.py "Sales Leads" leads.csv --cleanup --wait-minutes 30
```

**Full workflow with export:**
```bash
python3 upload_contacts.py "Sales Leads" leads.csv --cleanup --export enriched_leads.csv
```

**Provide API key directly:**
```bash
python3 upload_contacts.py "Sales Leads" leads.csv --api-key "abc123xyz"
```

---

## Workflows

### Workflow 1: Simple Upload

**Use case:** Just add contacts to Apollo  
**Credit usage:** 0 credits

```bash
python3 upload_contacts.py "My List" contacts.csv
```

**Process:**
1. Create or find list "My List"
2. Upload each contact
3. Add to list
4. Done

**Time:** ~2 minutes for 100 contacts

---

### Workflow 2: Upload with Immediate Export

**Use case:** Upload and download all data (no enrichment wait)  
**Credit usage:** 0 credits

```bash
python3 upload_contacts.py "My List" contacts.csv --export all_contacts.csv
```

**Process:**
1. Upload contacts
2. Immediately export to CSV
3. Done

**Output:** CSV with whatever data was in your input + any existing Apollo data

**Time:** ~3 minutes for 100 contacts

---

### Workflow 3: Full Auto-Enrichment (Recommended)

**Use case:** Get enriched contact data from email list  
**Credit usage:** 0 credits for script; Apollo may use credits for background enrichment

```bash
python3 upload_contacts.py "My List" contacts.csv --cleanup --export enriched.csv
```

**Process:**
1. Upload contacts (email-only or with data)
2. Wait 15 minutes for Apollo to auto-enrich
3. Fetch all contacts from list
4. Delete contacts without first_name, last_name, OR organization_name
5. Export remaining (enriched) contacts to CSV
6. Done

**Time:** ~20 minutes for 100 contacts

**Expected enrichment rate:**
- B2B emails: 30-50%
- Company emails: 40-60%
- Consumer emails: 10-30%

---

### Workflow 4: Custom Wait Time

**Use case:** Large lists or maximize enrichment  
**Credit usage:** 0 credits for script

```bash
python3 upload_contacts.py "Large List" contacts.csv --cleanup --wait-minutes 30 --export enriched.csv
```

**Process:**
Same as Workflow 3, but waits 30 minutes instead of 15.

**Recommendation:**
- <100 contacts: 15 minutes
- 100-1000 contacts: 20-30 minutes
- 1000+ contacts: 30-60 minutes

---

## CSV Format

### Minimum Format (Email Only)

**Works perfectly!** Apollo accepts email-only contacts.

```csv
email
john@company.com
jane@startup.com
bob@example.org
```

### Standard Format

```csv
email,first_name,last_name,company,title
john@company.com,John,Doe,Acme Corp,CEO
jane@startup.com,Jane,Smith,Startup Inc,Founder
bob@example.org,Bob,Jones,Example LLC,VP Sales
```

### Supported Columns

The script recognizes these column names (case-insensitive):

| Data Field | Recognized Column Names |
|------------|------------------------|
| **Email** (required) | `email`, `Email`, `EMAIL` |
| **First Name** | `first_name`, `First Name`, `First_Name` |
| **Last Name** | `last_name`, `Last Name`, `Last_Name` |
| **Company** | `company`, `Company`, `organization_name`, `Organization Name` |
| **Title** | `title`, `Title`, `Job Title` |
| **LinkedIn** | `linkedin_url`, `LinkedIn URL`, `linkedin` |
| **Website** | `website`, `Website`, `Company Website` |

### CSV Requirements

- **Encoding:** UTF-8 (UTF-8-BOM also supported)
- **Headers:** Required (first row)
- **Email:** Must be present in every row
- **Empty cells:** Allowed (will be skipped)

### Example: Mixed Data

```csv
email,first_name,company
user1@known.com,John,Known Corp
user2@unknown.com,,
user3@partial.com,Jane,
```

All three will be uploaded. The script handles missing data gracefully.

---

## API Endpoints Used

### 1. Create/Find Label
**Endpoint:** `POST /v1/labels`  
**Purpose:** Create new list or find existing list  
**Credits:** 0

**Request:**
```json
{
  "name": "My List",
  "modality": "contacts"
}
```

**Response on success:**
```json
{
  "label": {
    "id": "696b07f26dd0ec0011a10d43",
    "name": "My List",
    "modality": "contacts"
  }
}
```

**Response if exists (422):**
```json
{
  "error": "My List already exists"
}
```

The script automatically fetches the existing list ID in this case.

---

### 2. Get Labels
**Endpoint:** `GET /v1/labels`  
**Purpose:** Fetch all labels (when finding existing list)  
**Credits:** 0

**Response:**
```json
[
  {
    "id": "696b07f26dd0ec0011a10d43",
    "name": "My List",
    "modality": "contacts"
  },
  ...
]
```

---

### 3. Create Contact
**Endpoint:** `POST /v1/contacts`  
**Purpose:** Add contact to Apollo  
**Credits:** 0 (you're providing the email)

**Request:**
```json
{
  "email": "john@company.com",
  "first_name": "John",
  "last_name": "Doe",
  "organization_name": "Acme Corp",
  "title": "CEO",
  "label_names": ["My List"],
  "run_dedupe": true
}
```

**Response:**
```json
{
  "contact": {
    "id": "696b0b98323c5600159c124a",
    "email": "john@company.com",
    "first_name": "John",
    "last_name": "Doe",
    ...
  }
}
```

---

### 4. Search Contacts
**Endpoint:** `POST /v1/contacts/search`  
**Purpose:** Fetch contacts from a list  
**Credits:** 0 (accessing your saved contacts)

**Request:**
```json
{
  "label_ids": ["696b07f26dd0ec0011a10d43"],
  "page": 1,
  "per_page": 100
}
```

**Response:**
```json
{
  "contacts": [
    {
      "id": "696b0b98323c5600159c124a",
      "email": "john@company.com",
      "first_name": "John",
      "last_name": "Doe",
      "organization_name": "Acme Corp",
      ...
    },
    ...
  ],
  "pagination": {
    "page": 1,
    "per_page": 100,
    "total_pages": 5,
    "total_entries": 450
  }
}
```

The script automatically handles pagination to fetch all contacts.

---

### 5. Delete Contact
**Endpoint:** `DELETE /v1/contacts/{contact_id}`  
**Purpose:** Remove contact from Apollo  
**Credits:** 0

**Response:**
```json
{
  "success": true
}
```

---

## Credit Usage

### Script Operations: 0 Credits

| Operation | Endpoint | Credits |
|-----------|----------|---------|
| Create list | `POST /v1/labels` | 0 |
| Get labels | `GET /v1/labels` | 0 |
| Upload contact | `POST /v1/contacts` | 0 |
| Search contacts | `POST /v1/contacts/search` | 0 |
| Delete contact | `DELETE /v1/contacts/{contact_id}` | 0 |
| Export (fetch data) | `POST /v1/contacts/search` | 0 |

**Total script credit usage: 0**

You're uploading data you already have and accessing your saved contacts.

### Apollo Background Enrichment: Variable

**What happens:**
- After you upload email-only contacts, Apollo may automatically enrich them
- This happens in Apollo's background systems (not triggered by the script)
- Apollo searches its database to match emails with profiles
- If found, Apollo adds names, companies, titles, phone numbers, etc.

**Credit usage:**
- Depends on your Apollo plan
- Some plans include auto-enrichment
- Some plans charge credits for enrichment
- Check your Apollo plan details

**Important:** The script itself uses 0 credits. Any credits consumed are from Apollo's background enrichment based on your plan settings.

---

## Examples

### Example 1: Simple B2B Lead Upload

**Goal:** Upload 50 B2B email addresses

**Input CSV (leads.csv):**
```csv
email
ceo@startup1.com
founder@company2.com
director@business3.com
...
```

**Command:**
```bash
python3 upload_contacts.py "B2B Leads Jan 2026" leads.csv
```

**Result:**
- 50 contacts created in Apollo
- All added to list "B2B Leads Jan 2026"
- Ready for manual enrichment or campaigns

**Time:** ~1 minute

---

### Example 2: Auto-Enrichment Workflow

**Goal:** Get enriched contact data from 100 scraped emails

**Input CSV (scraped_emails.csv):**
```csv
email
person1@techco.com
person2@financestart.com
person3@healthcare.org
...
```

**Command:**
```bash
python3 upload_contacts.py "Enriched Prospects" scraped_emails.csv --cleanup --wait-minutes 20 --export enriched_prospects.csv
```

**Process:**
1. Uploads 100 emails (~2 min)
2. Waits 20 minutes
3. Apollo enriches ~40 contacts in background
4. Script deletes 60 unenriched contacts
5. Exports 40 enriched contacts

**Output (enriched_prospects.csv):**
```csv
email,first_name,last_name,organization_name,title,phone_numbers,...
person1@techco.com,John,Smith,TechCo Inc,VP Engineering,"+1-555-0100",...
person2@financestart.com,Jane,Doe,FinanceStart,CEO,"+1-555-0200",...
...
```

**Result:**
- 40 enriched contacts with full data
- 40+ fields per contact
- Ready for import to CRM

**Time:** ~25 minutes total

---

### Example 3: Large List Processing

**Goal:** Process 5000 emails

**Recommendation:** Break into chunks

**Commands:**
```bash
# Split CSV into chunks of 1000
split -l 1000 large_list.csv chunk_

# Process each chunk
python3 upload_contacts.py "Chunk 1" chunk_aa --cleanup --wait-minutes 30 --export chunk1_enriched.csv
python3 upload_contacts.py "Chunk 2" chunk_ab --cleanup --wait-minutes 30 --export chunk2_enriched.csv
# ... etc

# Combine results
cat chunk1_enriched.csv > all_enriched.csv
tail -n +2 chunk2_enriched.csv >> all_enriched.csv
# ... etc
```

**Time:** ~40 minutes per chunk of 1000

---

### Example 4: Existing Customer Enrichment

**Goal:** Enrich existing customer email list

**Input CSV (customers.csv):**
```csv
email,customer_id,purchase_date
john@company.com,CUST001,2024-01-15
jane@startup.com,CUST002,2024-02-20
...
```

**Command:**
```bash
python3 upload_contacts.py "Customer Enrichment" customers.csv --cleanup --export enriched_customers.csv
```

**Result:**
- Enriched customer data
- Original customer_id preserved (in Apollo custom fields if configured)
- Names, companies, titles added where available

**Use case:**
- Personalize customer communications
- Segment by company size/industry
- Build account-based marketing lists

---

## Advanced Usage

### Custom Column Mapping

If your CSV has different column names, you can:

**Option 1:** Rename columns in your CSV to match supported names

**Option 2:** Pre-process with a script:
```python
import pandas as pd

df = pd.read_csv('your_file.csv')
df.rename(columns={
    'Email Address': 'email',
    'Full Name': 'first_name',  # Will need to split
    'Company Name': 'company'
}, inplace=True)
df.to_csv('converted.csv', index=False)
```

### Processing Large Files

**Chunking large CSVs:**
```bash
# Split into 1000-line chunks
split -l 1000 large.csv chunk_

# Process each
for file in chunk_*; do
  python3 upload_contacts.py "Batch $(basename $file)" $file --cleanup --export "enriched_$(basename $file)"
done
```

### Monitoring Progress

**Watch logs in real-time:**
```bash
python3 upload_contacts.py "My List" file.csv --cleanup --export output.csv 2>&1 | tee upload.log
```

**Track in Apollo UI:**
While script runs, log into Apollo.io and watch:
1. Go to Lists/Labels
2. Find your list
3. Watch contacts being added
4. See enrichment happen in real-time

### Scheduling Regular Uploads

**Using cron (Linux/Mac):**
```bash
# Edit crontab
crontab -e

# Add daily upload at 2am
0 2 * * * cd /path/to/script && python3 upload_contacts.py "Daily Upload" /path/to/leads.csv --cleanup --export /path/to/output.csv
```

**Using Windows Task Scheduler:**
Create a batch file and schedule it.

---

## Troubleshooting

### Error: "No API Key found"

**Cause:** API key not set

**Solution:**
```bash
export APOLLO_API_KEY="your_key"
```

Or use `--api-key` flag.

---

### Error: "No valid leads with emails found"

**Cause:** CSV has no valid email addresses or wrong column name

**Solution:**
1. Check CSV has "email" column header
2. Ensure email cells aren't empty
3. Run inspection:
   ```bash
   head -5 your_file.csv
   ```

---

### Warning: "Contact only has email, no additional data"

**Cause:** CSV only has emails (which is fine!)

**Impact:** None - email-only contacts are valid

**Action:** This is just informational. Contacts will be uploaded successfully.

---

### Error: "Failed to add contact to label: 404"

**Cause:** Old version of script

**Solution:** Download latest version. New version uses `label_names` during contact creation, not after.

---

### All contacts deleted during cleanup

**Cause:** Apollo didn't enrich any contacts

**Possible reasons:**
1. Wait time too short
2. Emails not in Apollo's database
3. Auto-enrichment not enabled on your plan

**Solutions:**
- Wait longer: `--wait-minutes 30` or `--wait-minutes 60`
- Check emails are B2B (not consumer)
- Verify auto-enrichment is enabled in Apollo plan
- Run without `--cleanup` to keep all contacts

---

### Export file empty or very small

**Cause:** Few contacts were enriched

**Solutions:**
- Wait longer before cleanup
- Check input email quality
- Verify emails are professional/business emails
- Run without `--cleanup` to export all contacts

---

### Rate limit errors (429)

**Cause:** Hitting Apollo API rate limits

**Solution:** Script automatically handles this with retries. If persistent:
- Reduce batch processing speed
- Wait between runs
- Check your Apollo plan's rate limits

---

### Script hangs during wait

**Cause:** This is normal behavior!

**Explanation:** The `--wait-minutes` flag causes the script to wait intentionally. You'll see countdown messages every 30 seconds.

**To cancel:** Press `Ctrl+C`

---

## FAQ

### Q: Does this use API credits?

**A:** The script itself uses **0 credits**. You're uploading data you already have and accessing your saved contacts. However, Apollo may use credits for background auto-enrichment depending on your plan.

---

### Q: Can I upload email-only contacts?

**A:** Yes! Minimum CSV format is just an "email" column. Apollo accepts email-only contacts.

---

### Q: How does enrichment work?

**A:** After you upload email-only contacts, Apollo's systems automatically search their database to match emails with profiles. If found, they add names, companies, titles, etc. This happens in the background, not triggered by the script.

---

### Q: What enrichment rate should I expect?

**A:** Typical rates:
- B2B emails: 30-50%
- Company emails: 40-60%
- Consumer emails: 10-30%

Varies based on email quality and Apollo's database coverage.

---

### Q: What gets deleted during cleanup?

**A:** Contacts are deleted if they have:
- No first_name AND
- No last_name AND
- No organization_name

If a contact has ANY ONE of these fields, it's kept.

---

### Q: Can I run the same upload multiple times?

**A:** Yes! The script:
- Reuses existing lists (doesn't create duplicates)
- Deduplicates contacts (updates instead of duplicating)
- Safe to run multiple times

---

### Q: What fields are in the export?

**A:** 40+ fields including:
- Basic: email, first_name, last_name, name
- Company: organization_name, title, website_url
- Contact: phone_numbers (array), linkedin_url, twitter_url
- Location: city, state, country, present_raw_address
- Metadata: id, created_at, updated_at, source
- And many more Apollo fields

---

### Q: How long does it take?

**A:** For 100 contacts:
- Upload only: ~2 minutes
- With 15-min wait + cleanup + export: ~20 minutes
- With 30-min wait: ~35 minutes

Upload time scales linearly. Wait time is fixed.

---

### Q: Can I customize what gets deleted?

**A:** Currently, the logic is hardcoded (delete if no first_name, last_name, OR organization_name). To customize, you'd need to modify the `delete_unenriched_contacts()` method in the script.

---

### Q: What's the maximum number of contacts?

**A:** Script limitations:
- Upload: No limit (processes one at a time)
- Export: 50,000 contacts max (Apollo API pagination limit)

For lists >50,000, you'd need to export in batches.

---

### Q: Does this work with non-English names/companies?

**A:** Yes, the script handles UTF-8 encoding. International names and companies work fine.

---

### Q: Can I schedule automatic runs?

**A:** Yes, use cron (Linux/Mac) or Task Scheduler (Windows). See Advanced Usage section.

---

## Best Practices

### 1. Start Small

Test with 10-20 emails first before processing thousands.

```bash
# Create small test
head -21 large_file.csv > test.csv

# Test workflow
python3 upload_contacts.py "Test" test.csv --cleanup --wait-minutes 2 --export test_results.csv

# Check results
cat test_results.csv
```

---

### 2. Use Descriptive List Names

Include date or purpose:
```bash
# Good
python3 upload_contacts.py "Q1 2026 B2B Leads" file.csv

# Better
python3 upload_contacts.py "Jan 2026 Tech Sector Prospects" file.csv
```

---

### 3. Longer Waits for Better Results

More time = more enrichment opportunities:
- Small lists (<100): 15 minutes
- Medium lists (100-500): 20-30 minutes
- Large lists (500+): 30-60 minutes

---

### 4. Validate Email Quality

Before uploading:
- Remove duplicates
- Validate email format
- Remove role emails (info@, sales@)
- Filter for target industries/regions

---

### 5. Monitor Enrichment Rates

Track what percentage gets enriched:
```bash
# Before cleanup
python3 upload_contacts.py "Test" file.csv --export before.csv

# Count
wc -l before.csv

# After cleanup
python3 upload_contacts.py "Test" file.csv --cleanup --export after.csv

# Count
wc -l after.csv

# Calculate rate
```

---

### 6. Backup Exports

Save enriched data:
```bash
# Add timestamp to filename
python3 upload_contacts.py "List" file.csv --cleanup --export "enriched_$(date +%Y%m%d).csv"
```

---

### 7. Chunk Large Lists

For 1000+ contacts:
```bash
split -l 1000 large.csv chunk_

for file in chunk_*; do
  python3 upload_contacts.py "Batch $file" $file --cleanup --export "enriched_$file"
  sleep 60  # Wait between batches
done
```

---

### 8. Keep Logs

```bash
python3 upload_contacts.py "List" file.csv --cleanup --export output.csv 2>&1 | tee upload_$(date +%Y%m%d_%H%M%S).log
```

---

### 9. Verify in Apollo UI

After upload:
1. Log into Apollo.io
2. Check the list was created
3. Verify contact count
4. Spot-check enrichment quality

---

### 10. Plan for API Rate Limits

Apollo has rate limits (e.g., 600 requests/hour for contacts endpoint):
- For large uploads, expect delays
- Script handles retries automatically
- Consider spreading large uploads across multiple hours

---

## Summary

The Apollo Contact Uploader provides a complete solution for:
- **Uploading** contacts with 0 credit usage
- **Auto-enriching** via Apollo's background systems
- **Cleaning** unenriched data automatically
- **Exporting** enriched data with full fields

**Typical workflow:**
```bash
python3 upload_contacts.py "My List" emails.csv --cleanup --export enriched.csv
```

**Result:** Enriched contact data ready for CRM import, campaigns, or analysis.

**Documentation version:** 2.0  
**Last updated:** January 2026

For questions or issues, refer to the Troubleshooting and FAQ sections.
