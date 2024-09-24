FROM python:3.9-slim

WORKDIR /app

# Copy requirements.txt first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY jellyfin_discord_notifier.py .

# Create a volume for the database file
VOLUME /app/data

# Set the database file path to the volume
ENV DB_FILE=/app/data/jellyfin_items.db

# Set the timezone
ENV TZ=UTC

CMD ["python", "jellyfin_discord_notifier.py"]