# Kernel TinyURL Script

Python script to automatically create TinyURLs for Airtable records and update their status.

## Setup

1. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set required environment variables:
```bash
export AIRTABLE_API_KEY=your_airtable_api_key
export TINYURL_API_TOKEN=your_tinyurl_api_token
```

4. Optional configuration (defaults provided):
```bash
export AIRTABLE_BASE_ID=your_base_id
export AIRTABLE_TABLE_NAME=your_table_name
export AIRTABLE_VIEW_NAME=your_view_name
```

## Usage

Run the script:
```bash
python3 update.py
```

## What it does

1. Fetches records from specified Airtable view
2. Creates TinyURLs using format `kb-{rec-id}`
3. Updates Airtable `script` field with:
   - "tinyurl valid" (success)
   - "error - [message]" (failure)

## Cron Job

To run periodically, add to crontab:
```bash
# Run every hour
0 * * * * cd /path/to/script && python3 update.py
```