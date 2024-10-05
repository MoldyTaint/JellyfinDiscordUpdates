import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import time
import json
import sqlite3
import logging
from logging.handlers import RotatingFileHandler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone

# Set up logging
log_file = 'jellyfin_discord_notifier.log'
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        RotatingFileHandler(log_file, maxBytes=1000000, backupCount=5),
                        logging.StreamHandler()  # This will keep console output as well
                    ])

# Load environment variables
load_dotenv()

# Jellyfin API configuration
JELLYFIN_URL = os.getenv('JELLYFIN_URL')
JELLYFIN_API_KEY = os.getenv('JELLYFIN_API_KEY')

# Discord webhook configuration
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

if not DISCORD_WEBHOOK_URL:
    print("Error: Discord webhook URL is not set in the .env file.")
    exit(1)

# Database file
DB_FILE = os.getenv('DB_FILE', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jellyfin_items.db'))

# New scheduling configurations
RUN_FREQUENCY = os.getenv('RUN_FREQUENCY', 'daily')
RUN_TIME = os.getenv('RUN_TIME', '09:00')
TIMEZONE = os.getenv('TIMEZONE', 'UTC')
DAYS_OF_WEEK = os.getenv('DAYS_OF_WEEK', 'mon,tue,wed,thu,fri,sat,sun').split(',')

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS items
                 (imdb_id TEXT PRIMARY KEY, name TEXT, year INTEGER, quality TEXT, last_updated TEXT)''')  # Changed 'id' to 'imdb_id'
    conn.commit()
    return conn

def get_item_quality(item):
    if 'MediaSources' in item and item['MediaSources']:
        source = item['MediaSources'][0]
        if 'MediaStreams' in source:
            for stream in source['MediaStreams']:
                if stream['Type'] == 'Video':
                    return f"{stream.get('Width', '')}x{stream.get('Height', '')}"
    return "Unknown"

def get_new_items(conn):
    c = conn.cursor()
    
    url = f"{JELLYFIN_URL}/Items?IncludeItemTypes=Movie,Series&SortBy=DateCreated&SortOrder=Descending&Recursive=true&Fields=Name,ProductionYear,ProviderIds,Overview,Genres,MediaSources,MediaStreams&api_key={JELLYFIN_API_KEY}"

    logging.debug(f"Fetching items from Jellyfin URL: {url}")
    response = requests.get(url)
    if response.status_code == 200:
        items = response.json().get('Items', [])
        logging.debug(f"Received {len(items)} items from Jellyfin")
        new_items = []
        
        for item in items:
            provider_ids = item.get('ProviderIds', {})
            imdb_id = provider_ids.get('Imdb')
            if not imdb_id:
                logging.debug(f"Item {item['Name']} does not have an IMDb ID. Skipping.")
                continue  # Skip items without IMDb ID
            
            c.execute("SELECT imdb_id FROM items WHERE imdb_id = ?", (imdb_id,))
            result = c.fetchone()
            
            if result is None:
                logging.debug(f"New item found: {item['Name']} (IMDb ID: {imdb_id})")
                c.execute("INSERT INTO items VALUES (?, ?, ?, ?, ?)", 
                          (imdb_id, item['Name'], item['ProductionYear'], get_item_quality(item), datetime.now().isoformat()))
                new_items.append(item)
            else:
                logging.debug(f"Existing item found: {item['Name']} (IMDb ID: {imdb_id}). Skipping.")
                # Do not break; allow processing other items
        
        conn.commit()
        logging.info(f"Found {len(new_items)} new items")
        return new_items
    else:
        logging.error(f"Error fetching items from Jellyfin: {response.status_code}")
        return []

def send_discord_message(items):
    MAX_LENGTH = 2000
    messages = []
    current_message = "**New additions to the Jellyfin server:**\n\n"
    
    for item in items:
        item_type = "🎬" if item['Type'] == 'Movie' else "📺"
        title_line = f"{item_type} **{item['Name']}**"
        
        if 'ProviderIds' in item and 'Imdb' in item['ProviderIds']:
            imdb_id = item['ProviderIds']['Imdb']
            title_line += f" ([IMDb](https://www.imdb.com/title/{imdb_id}/))"
        
        item_message = title_line + "\n"
        
        if 'Genres' in item and item['Genres']:
            item_message += f"{', '.join(item['Genres'][:3])}\n"
        if 'Overview' in item and item['Overview']:
            overview = item['Overview'][:100] + "..." if len(item['Overview']) > 100 else item['Overview']
            item_message += f"> {overview}\n"
        item_message += "\n"
        
        if len(current_message) + len(item_message) > MAX_LENGTH:
            messages.append(current_message)
            current_message = "**Continued: New additions to the Jellyfin server:**\n\n" + item_message
        else:
            current_message += item_message
    
    if current_message:
        messages.append(current_message)
    
    for message in messages:
        payload = {"content": message}
        logging.debug(f"Sending Discord message with payload: {json.dumps(payload, indent=2)}")
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            logging.info("Message part sent successfully to Discord")
        else:
            logging.error(f"Error sending message to Discord: {response.status_code}")
            logging.error(f"Response content: {response.text}")
        time.sleep(1)  # Add a small delay between messages to avoid rate limiting

def run_job():
    logging.info("Starting Jellyfin Discord Notifier job")
    conn = init_db()
    new_items = get_new_items(conn)
    
    if not new_items:
        logging.info("No new items found.")
        conn.close()
        return

    send_discord_message(new_items)
    conn.close()
    logging.info("Job execution completed")

if __name__ == "__main__":
    scheduler = BlockingScheduler()
    
    hour, minute = map(int, RUN_TIME.split(':'))
    tz = timezone(TIMEZONE)

    if RUN_FREQUENCY == 'daily':
        scheduler.add_job(run_job, CronTrigger(hour=hour, minute=minute, timezone=tz))
    elif RUN_FREQUENCY == 'weekly':
        scheduler.add_job(run_job, CronTrigger(day_of_week=','.join(DAYS_OF_WEEK), hour=hour, minute=minute, timezone=tz))
    elif RUN_FREQUENCY == 'monthly':
        scheduler.add_job(run_job, CronTrigger(day=1, hour=hour, minute=minute, timezone=tz))
    else:
        logging.error(f"Invalid RUN_FREQUENCY: {RUN_FREQUENCY}")
        exit(1)

    logging.info(f"Scheduler set up with {RUN_FREQUENCY} frequency at {RUN_TIME} {TIMEZONE}")
    scheduler.start()