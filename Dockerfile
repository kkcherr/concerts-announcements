FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Holds the SQLite state database and the Ticketmaster attraction-id cache
# so they survive container restarts when this directory is mounted as a volume.
RUN mkdir -p /app/data

CMD ["python", "main.py"]
