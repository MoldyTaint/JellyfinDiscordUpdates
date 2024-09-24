# Jellyfin Discord Notifier

This project notifies a Discord channel about new additions to a Jellyfin server.

## Setup

1. Clone this repository
2. Create a `.env` file with your Jellyfin and Discord configuration:

   ```
   JELLYFIN_URL=YOUR_JELLYFIN_URL
   JELLYFIN_API_KEY=YOUR_JELLYFIN_API_KEY
   DISCORD_WEBHOOK_URL=YOUR_DISCORD_WEBHOOK_URL
   ```

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
   docker pull ghcr.io/YOUR-GITHUB-USERNAME/YOUR-REPO-NAME:main
   ```

2. Run the container:
   ```
   docker run -d --name jellyfin-notifier \
     -v /path/to/your/.env:/app/.env \
     -v /path/to/your/data:/app/data \
     ghcr.io/YOUR-GITHUB-USERNAME/YOUR-REPO-NAME:main
   ```

   Replace `/path/to/your/.env` with the actual path to your `.env` file, and `/path/to/your/data` with the path where you want to store the database file.

3. The container will now run with your configuration.