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
        'fields': ['Name [Primary]', 'rec-id', 'url-to-send']
    }
    
    async with session.get(url, headers=headers, params=params) as response:
        if response.status == 200:
            data = await response.json()
            return data.get('records', [])
        else:
            logging.error(f"Failed to fetch Airtable records: {response.status}")
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
    
    async with session.post(tinyurl_api, json=payload, headers=headers) as response:
        return response.status == 200

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
    
    async with session.patch(url, json=payload, headers=headers) as response:
        return response.status == 200

async def main():
    logging.info("Starting TinyURL cron job")
    
    if not AIRTABLE_API_KEY:
        logging.error("AIRTABLE_API_KEY environment variable not set")
        return
    
    if not TINYURL_API_TOKEN:
        logging.error("TINYURL_API_TOKEN environment variable not set")
        return
    
    async with aiohttp.ClientSession() as session:
        records = await fetch_airtable_records(session)
        logging.info(f"Fetched {len(records)} records from Airtable")
        
        for i, record in enumerate(records):
            fields = record.get('fields', {})
            record_id = record.get('id')
            name = fields.get('Name [Primary]', 'Unknown')
            rec_id = fields.get('rec-id')
            url_to_send = fields.get('url-to-send')
            
            logging.info(f"Processing {i+1}/{len(records)}: {name}")
            
            if not rec_id or not url_to_send:
                await update_airtable_script_field(session, record_id, "error - missing rec-id or url-to-send")
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