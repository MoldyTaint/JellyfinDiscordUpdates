# Jellyfin Discord Notifier

This project automatically notifies a Discord channel about new media additions to your Jellyfin server.

## Features

- Monitors Jellyfin server for new media additions
- Sends customizable notifications to a Discord channel
- Supports both movies and TV shows
- Runs as a standalone Python script or in a Docker container

## Setup

### Prerequisites

- Python 3.7+
- Jellyfin server
- Discord server with webhook access

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/JellyfinDiscordUpdates.git
   cd JellyfinDiscordUpdates
   ```

2. Copy the `.env.example` file to `.env`:
   ```
   cp .env.example .env
   ```

3. Update the `.env` file with your configuration (see [Configuration](#configuration) section below)

4. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

### Running the Script

To run the script directly:

```
python jellyfin_discord_notifier.py
```

## Docker Setup

### Using Pre-built Image

1. Pull the image:
   ```
   docker pull ghcr.io/moldytaint/jellyfindiscordupdates:main
   ```

2. Create and configure your `.env` file as described in the [Configuration](#configuration) section.

3. Run the container:
   ```
   docker run -d --name jellyfin-notifier \
     -v /path/to/your/.env:/app/.env:ro \
     -v /path/to/your/data:/app/data \
     ghcr.io/moldytaint/jellyfindiscordupdates:main
   ```

   Replace `/path/to/your/.env` with the actual path to your `.env` file, and `/path/to/your/data` with the path where you want to store the database file.

### Building Your Own Image

If you prefer to build your own Docker image:

1. Build the image:
   ```
   docker build -t jellyfin-discord-notifier .
   ```

2. Run the container:
   ```
   docker run -d --name jellyfin-notifier \
     -v /path/to/your/.env:/app/.env:ro \
     -v /path/to/your/data:/app/data \
     jellyfin-discord-notifier
   ```

## Configuration

Copy the `.env.example` file to `.env` and update it with your Jellyfin and Discord configuration:

```
JELLYFIN_URL=http://your-jellyfin-server:8096
JELLYFIN_API_KEY=your_jellyfin_api_key
DISCORD_WEBHOOK_URL=your_discord_webhook_url
CHECK_INTERVAL=300
```

- `JELLYFIN_URL`: The URL of your Jellyfin server
- `JELLYFIN_API_KEY`: Your Jellyfin API key
- `DISCORD_WEBHOOK_URL`: The Discord webhook URL for the channel you want to send notifications to
- `CHECK_INTERVAL`: The interval (in seconds) between checks for new media (default: 300)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Jellyfin](https://jellyfin.org/) for their amazing media server
- [Discord](https://discord.com/) for their communication platform
