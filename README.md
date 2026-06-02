# 🎤 Concert Announcement Bot

A Telegram bot that checks multiple sources every day and sends you a digest of new concert announcements for your favourite artists — worldwide, every morning at 9 AM London time.

---

## What you'll need before you start

- A computer running Windows, Mac, or Linux
- An internet connection
- A Telegram account (free — telegram.org)
- About 20–30 minutes

---

## Step 1 — Install Python

Python is the programming language this bot is written in. You need version 3.11 or newer.

### Check if you already have it

Open a **Terminal** (Mac/Linux) or **Command Prompt** (Windows — press Win+R, type `cmd`, press Enter) and type:

```
python --version
```

or

```
python3 --version
```

If you see something like `Python 3.11.x` or higher, skip to Step 2.

### Installing Python (if you don't have it)

**Mac:**
1. Go to https://www.python.org/downloads/
2. Click the big yellow "Download Python 3.x.x" button
3. Open the downloaded `.pkg` file and follow the installer

**Windows:**
1. Go to https://www.python.org/downloads/
2. Click the big yellow "Download Python 3.x.x" button
3. Run the installer — **important:** tick the box that says "Add Python to PATH" before clicking Install

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install python3 python3-pip python3-venv
```

---

## Step 2 — Download this project

### Option A — Download as a ZIP (easiest)

1. Go to the GitHub page for this project
2. Click the green **Code** button → **Download ZIP**
3. Unzip the file somewhere easy to find, like your Desktop

### Option B — Use Git (if you know what that is)

```bash
git clone https://github.com/kkcherr/concerts-announcements.git
cd concerts-announcements
```

---

## Step 3 — Create a virtual environment

A virtual environment is like a clean, isolated box for this project's dependencies. It stops packages from clashing with other things on your computer.

Open your terminal, navigate to the project folder (e.g. `cd Desktop/concerts-announcements`), then run:

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

You'll know it worked when you see `(venv)` at the start of your terminal prompt.

---

## Step 4 — Install dependencies

"Dependencies" are the extra libraries this bot uses. Install them with one command (make sure your virtual environment is active first):

```bash
pip install -r requirements.txt
```

This will take a minute or two. You'll see a lot of text scrolling past — that's normal.

---

## Step 5 — Get your credentials

The bot needs four pieces of information. The setup wizard will ask for them automatically when you first run it, but here's how to get each one:

---

### 5a — Create a Telegram bot and get its token

1. Open Telegram and search for **@BotFather** (it has a blue tick)
2. Tap **Start** or send `/start`
3. Send `/newbot`
4. BotFather will ask for a name — type something like `My Concert Bot`
5. It will ask for a username — must end in `bot`, e.g. `myconcerts_bot`
6. BotFather will reply with a **token** that looks like:
   ```
   123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
   ```
7. Copy this token — you'll paste it into the setup wizard

---

### 5b — Get your personal Telegram chat ID

1. In Telegram, search for **@userinfobot**
2. Tap **Start** or send `/start`
3. It will immediately reply with your numeric ID, e.g. `123456789`
4. Copy this number

---

### 5c — Get a free Ticketmaster API key

1. Go to https://developer.ticketmaster.com/
2. Click **Get Your API Key** (top right)
3. Create a free account (no credit card needed)
4. After signing in, click **My Apps** in the top menu
5. Click **Create a New App**
6. Fill in any name and description — click **Save**
7. Your **Consumer Key** is your API key — copy it

---

### 5d — Get a Bandsintown app ID

Bandsintown just needs any short identifier string — it doesn't need a real registration.

You can use anything: your name, a made-up word, your email, etc.

Example: `jane_concert_bot`

---

## Step 6 — Run the bot for the first time

With your virtual environment active, run:

```bash
python main.py
```

The setup wizard will start automatically. It will ask for each credential one at a time and save your answers to a file called `.env`.

At the end, it will offer to send a **test message** to your Telegram. Say yes — this confirms everything is connected correctly.

---

## Step 7 — Verify it's working

After the test message:
- Check your Telegram — you should see a message from your bot saying it's connected
- Back in the terminal, you'll see something like:
  ```
  ✅ Bot is running! Daily digest scheduled for 09:00 (Europe/London).
  Press Ctrl+C to stop.
  ```

To send a digest right now (without waiting until 9 AM), run:

```bash
python main.py --run-now
```

To just test the Telegram connection:

```bash
python main.py --test
```

---

## Step 8 — Your .env file (what it looks like)

After the wizard runs, you'll find a `.env` file in the project folder. It looks like this:

```
TELEGRAM_BOT_TOKEN="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
TELEGRAM_CHAT_ID="987654321"
TICKETMASTER_API_KEY="AbCdEfGhIjKlMnOpQrStUvWx"
BANDSINTOWN_APP_ID="my_concert_bot"

DIGEST_HOUR="9"
DIGEST_MINUTE="0"
TIMEZONE="Europe/London"
DB_PATH="concerts.db"
```

You can edit this file manually with any text editor if you need to change something. **Never share this file with anyone** — it contains your private credentials.

---

## Step 9 — Deploy so it runs 24/7 (without your laptop)

If you close your laptop, the bot stops. To keep it running all the time, deploy it to **Railway** — a beginner-friendly cloud platform with a free tier that requires no credit card.

### Deploy on Railway

1. Go to https://railway.app and sign up with your GitHub account (free)
2. Click **New Project** → **Deploy from GitHub repo**
3. Select this repository
4. Railway will detect it's a Python project and build it automatically
5. Go to **Variables** in your Railway project and add each value from your `.env` file:
   - `TELEGRAM_BOT_TOKEN` → your token
   - `TELEGRAM_CHAT_ID` → your chat ID
   - `TICKETMASTER_API_KEY` → your key
   - `BANDSINTOWN_APP_ID` → your app ID
6. Railway will restart the app — your bot is now running 24/7 in the cloud!

> **Tip:** Railway's free tier gives you 500 hours/month, which is enough for this bot.

---

## Troubleshooting

### "python: command not found" or "python3: command not found"
Python is not installed or not on your PATH. Re-do Step 1. On Windows, make sure you ticked "Add Python to PATH" during installation.

### "ModuleNotFoundError: No module named 'requests'" (or any other module)
Your virtual environment is not active, or you haven't installed dependencies yet. Run:
```bash
source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

### "Telegram test message failed"
- Double-check your bot token — copy it again from BotFather
- Double-check your chat ID — try @userinfobot again
- Make sure you have started a conversation with your bot (search for it in Telegram and press Start)

### "Ticketmaster: API key not configured" in the digest
Your Ticketmaster key is missing or wrong in the `.env` file. Open the file in a text editor and check the `TICKETMASTER_API_KEY` line has no extra spaces or quotes.

### The bot runs but sends no events
This is normal on the first run — all events get marked as "already seen" so you don't get flooded. The next day's digest will only show genuinely new announcements. To reset and see everything again, delete the `concerts.db` file and re-run.

---

## Customising your artist watchlist

Open `config.py` in any text editor and find the `WATCHLIST` list. Add or remove artists exactly as shown:

```python
WATCHLIST = [
    "Lady Gaga",
    "Your New Artist Here",  # ← add a line like this
    ...
]
```

Save the file and restart the bot.

---

## Changing the digest time

Open your `.env` file and change:
```
DIGEST_HOUR="9"     # 9 = 9 AM, 20 = 8 PM, etc.
DIGEST_MINUTE="0"
TIMEZONE="Europe/London"
```

Save and restart the bot.
