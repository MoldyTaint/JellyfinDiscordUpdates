import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import time
import json
import sqlite3
import logging
from logging.handlers import RotatingFileHandler

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
DB_FILE = os.getenv('DB_FILE', 'jellyfin_items.db')

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS items
                 (id TEXT PRIMARY KEY, name TEXT, year INTEGER, quality TEXT, last_updated TEXT)''')
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
            item_id = item['Id']
            item_name = item['Name']
            item_year = item['ProductionYear']
            item_quality = get_item_quality(item)
            
            c.execute("SELECT id FROM items WHERE id = ?", (item_id,))
            result = c.fetchone()
            
            if result is None:
                logging.debug(f"New item found: {item_name}")
                c.execute("INSERT INTO items VALUES (?, ?, ?, ?, ?)", 
                          (item_id, item_name, item_year, item_quality, datetime.now().isoformat()))
                new_items.append(item)
            else:
                logging.debug(f"Existing item found: {item_name}. Stopping check.")
                break
        
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
            item_message += f"Genres: {', '.join(item['Genres'][:3])}\n"
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

def main():
    conn = init_db()
    new_items = get_new_items(conn)
    
    if not new_items:
        logging.info("No new items found.")
        return

    # Check if this is the first run
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM items")
    item_count = c.fetchone()[0]
    
    if item_count == len(new_items):
        logging.info(f"First run: {len(new_items)} items added to the database. No Discord message sent.")
        conn.close()
        return

    send_discord_message(new_items)

    conn.close()
    logging.info("Script execution completed")

if __name__ == "__main__":
    logging.info("Starting Jellyfin Discord Notifier")
    main()