import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY", "")
BANDSINTOWN_APP_ID = os.getenv("BANDSINTOWN_APP_ID", "")
DIGEST_HOUR = int(os.getenv("DIGEST_HOUR", "9"))
DIGEST_MINUTE = int(os.getenv("DIGEST_MINUTE", "0"))
TIMEZONE = os.getenv("TIMEZONE", "Europe/London")
DB_PATH = os.getenv("DB_PATH", "concerts.db")

WATCHLIST = [
    "Lady Gaga",
    "Taylor Swift",
    "Adele",
    "Harry Styles",
    "30 Seconds to Mars",
    "Maroon 5",
    "OneRepublic",
    "Sabrina Carpenter",
    "Green Day",
    "Olivia Rodrigo",
    "Chappell Roan",
    "Olivia Dean",
    "Pussycat Dolls",
    "Elton John",
    "Ariana Grande",
    "Christina Aguilera",
    "Bad Bunny",
    "Sombr",
]

REQUIRED_VARS = [
    ("TELEGRAM_BOT_TOKEN", "Your Telegram bot token from @BotFather"),
    ("TELEGRAM_CHAT_ID", "Your personal Telegram chat ID"),
    ("TICKETMASTER_API_KEY", "Your Ticketmaster Discovery API key (free)"),
    ("BANDSINTOWN_APP_ID", "Your Bandsintown app ID (can be any string, e.g. your name)"),
]
