FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY jellyfin_discord_notifier.py .
COPY .env .

# Create a volume for the database file
VOLUME /app/data

# Set the database file path to the volume
ENV DB_FILE=/app/data/jellyfin_items.db

CMD ["python", "jellyfin_discord_notifier.py"]