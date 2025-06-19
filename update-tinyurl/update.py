import asyncio
import aiohttp
import os
import logging

# Configuration - set these as environment variables
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID', 'appYaT73RTzmoKIrq')
AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME', 'Applications')
AIRTABLE_VIEW_NAME = os.getenv('AIRTABLE_VIEW_NAME', 'Grid view')
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
TINYURL_API_TOKEN = os.getenv('TINYURL_API_TOKEN')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def fetch_airtable_records(session):
    """Fetch records from Airtable view"""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }
    params = {
        'view': AIRTABLE_VIEW_NAME,
        'fields': ['Name', 'rec-id', 'big-url']
    }

    logging.info(f"Fetching from URL: {url}")
    logging.info(f"Using base ID: {AIRTABLE_BASE_ID}")
    logging.info(f"Using table: {AIRTABLE_TABLE_NAME}")
    logging.info(f"Using view: {AIRTABLE_VIEW_NAME}")

    async with session.get(url, headers=headers, params=params) as response:
        if response.status == 200:
            data = await response.json()
            return data.get('records', [])
        else:
            response_text = await response.text()
            logging.error(f"Failed to fetch Airtable records: {response.status}")
            logging.error(f"Response body: {response_text}")
            logging.error(f"Request URL: {url}")
            logging.error(f"Request headers: {headers}")
            logging.error(f"Request params: {params}")
            return []

async def create_tinyurl(session, url, alias):
    """Create a TinyURL"""
    tinyurl_api = f"https://api.tinyurl.com/create?api_token={TINYURL_API_TOKEN}"
    payload = {
        "url": url,
        "domain": "tinyurl.com",
        "alias": f"kb-{alias}"
    }
    headers = {'Content-Type': 'application/json'}

    logging.info(f"Creating TinyURL for {url} with alias kb-{alias}")

    async with session.post(tinyurl_api, json=payload, headers=headers) as response:
        if response.status == 200:
            response_data = await response.json()
            logging.info(f"TinyURL created successfully: {response_data}")
            return True
        else:
            response_text = await response.text()
            logging.error(f"TinyURL creation failed: {response.status}")
            logging.error(f"Response body: {response_text}")
            logging.error(f"Request payload: {payload}")
            return False

async def update_airtable_script_field(session, record_id, status_message):
    """Update Airtable record script field with status"""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}/{record_id}"
    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {
        'fields': {
            'script': status_message
        }
    }

    logging.info(f"Updating record {record_id} with status: {status_message}")

    async with session.patch(url, json=payload, headers=headers) as response:
        if response.status == 200:
            logging.info(f"Successfully updated record {record_id}")
            return True
        else:
            response_text = await response.text()
            logging.error(f"Failed to update record {record_id}: {response.status}")
            logging.error(f"Response body: {response_text}")
            return False

async def main():
    logging.info("Starting TinyURL cron job")

    if not AIRTABLE_API_KEY:
        logging.error("AIRTABLE_API_KEY environment variable not set")
        return
    else:
        logging.info(f"AIRTABLE_API_KEY is set (length: {len(AIRTABLE_API_KEY)})")

    if not TINYURL_API_TOKEN:
        logging.error("TINYURL_API_TOKEN environment variable not set")
        return
    else:
        logging.info(f"TINYURL_API_TOKEN is set (length: {len(TINYURL_API_TOKEN)})")

    async with aiohttp.ClientSession() as session:
        records = await fetch_airtable_records(session)
        logging.info(f"Fetched {len(records)} records from Airtable")

        for i, record in enumerate(records):
            fields = record.get('fields', {})
            record_id = record.get('id')
            name = fields.get('Name', 'Unknown')
            rec_id = fields.get('rec-id')
            url_to_send = fields.get('big-url')

            logging.info(f"Processing {i+1}/{len(records)}: {name}")

            if not rec_id or not url_to_send:
                await update_airtable_script_field(session, record_id, "error - missing rec-id or big-url")
                continue

            try:
                success = await create_tinyurl(session, url_to_send, rec_id)
                if success:
                    await update_airtable_script_field(session, record_id, "tinyurl valid")
                    logging.info(f"Successfully created TinyURL for {name}")
                else:
                    await update_airtable_script_field(session, record_id, "error - tinyurl creation failed")
                    logging.error(f"TinyURL creation failed for {name}")

                await asyncio.sleep(3)

            except Exception as e:
                error_msg = f"error - {str(e)}"
                await update_airtable_script_field(session, record_id, error_msg)
                logging.error(f"Error processing {name}: {e}")

        logging.info("Cron job completed")

if __name__ == "__main__":
    asyncio.run(main())