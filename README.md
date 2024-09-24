# Jellyfin Discord Notifier

This project notifies a Discord channel about new additions to a Jellyfin server.

## Setup

1. Clone this repository
2. Copy the `.env.example` file to `.env` and update it with your configuration (see Configuration section below)
3. Install the required packages:

   ```
   pip install -r requirements.txt
   ```

4. Run the script:

   ```
   python jellyfin_discord_notifier.py
   ```

## Using the Docker Image

To use the Docker image:

1. Pull the image:
   ```
   docker pull ghcr.io/moldytaint/jellyfindiscordupdates:main
   ```

2. Create a `.env` file based on the `.env.example` template and fill in your configuration.

3. Run the container:
   ```
   docker run -d --name jellyfin-notifier \
     -v /path/to/your/.env:/app/.env:ro \
     -v /path/to/your/data:/app/data \
     ghcr.io/moldytaint/jellyfindiscordupdates:main
   ```

   Replace `/path/to/your/.env` with the actual path to your `.env` file, and `/path/to/your/data` with the path where you want to store the database file.

4. The container will now run with your configuration.

## Configuration

Copy the `.env.example` file to `.env` and update it with your Jellyfin and Discord configuration:
