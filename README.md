# 🎤 Concert Digest Bot

A Telegram bot that checks every day for **newly announced concerts** by
artists you care about — anywhere in the world — and sends you **one tidy
digest message**. Shows in the **UK or Spain** are flagged as **PRIORITY**
and put at the top, since those are the easiest for you to attend. Whenever
Ticketmaster knows about a **presale**, it's shown so you can buy before
the general public.

This README is written for someone who has **never used a terminal or
written code before**. Every technical word is explained the first time
it's used. Follow the steps in order — each one is small.

> These instructions are for **Mac**. (If you're on Windows, the steps are
> very similar but the commands and folder paths look slightly different —
> ask for the Windows version of this guide if you need it.)

---

## What this bot does, in plain terms

Once a day, at a time you choose (default 7:00 PM UK time), the bot:

1. Checks **Ticketmaster** and **Bandsintown** for every artist on your
   three lists (`must_see`, `legends`, `blockbusters`).
2. Works out which of those shows are **brand new** (it remembers what it
   already told you about).
3. Sends you **one Telegram message** listing the new shows — UK/Spain
   shows first, marked with a ⭐ **PRIORITY** label — including dates,
   venues, ticket links, and any **presale windows** it knows about.
4. If nothing new was found, it can optionally send "nothing new today" so
   you know it's still alive (this is off by default).

---

## Part 1 — What you need to install

### "Terminal" — what is it?

The **Terminal** is an app already on your Mac where you type commands
instead of clicking buttons. You'll use it for a few steps below. To open
it: press `Cmd + Space`, type `Terminal`, press `Enter`.

### Step 1.1 — Install Python

**Python** is the programming language this bot is written in — your Mac
needs it installed to run the bot's code.

1. Open Terminal and type:
   ```
   python3 --version
   ```
2. If you see something like `Python 3.11.x` or higher, you already have
   it — skip to Step 1.2.
3. If not, go to https://www.python.org/downloads/ in your browser, click
   the big yellow **"Download Python"** button, open the downloaded file,
   and follow the installer (clicking "Continue"/"Install" through each
   screen).

### Step 1.2 — Download this project

If you already have this project's folder on your computer, skip to
Step 1.3. Otherwise:

1. Go to this project's page on GitHub.
2. Click the green **Code** button → **Download ZIP**.
3. Find the downloaded `.zip` file (usually in your **Downloads** folder)
   and double-click it to unzip it. Move the resulting folder somewhere
   easy to find, like your **Desktop**.

### Step 1.3 — Open the project folder in Terminal

In Terminal, type `cd ` (with a space after it), then drag the project
folder from Finder into the Terminal window — this fills in the folder's
path automatically — then press `Enter`. You should now be "inside" the
project folder.

### Step 1.4 — Create a virtual environment

A **virtual environment** is a private, clean space for this project's
extra bits of code, so they don't interfere with anything else on your Mac.

```bash
python3 -m venv venv
source venv/bin/activate
```

After the second command, you should see `(venv)` appear at the start of
your Terminal line. That means it worked. **You'll need to run
`source venv/bin/activate` again every time you open a new Terminal window
to work on this bot.**

### Step 1.5 — Install the bot's dependencies

**Dependencies** are extra bits of code this bot relies on (for example,
code that talks to Telegram). Install them all with one command:

```bash
pip install -r requirements.txt
```

This will print a lot of text and take a minute or two — that's normal.

---

## Part 2 — Get your three secret credentials

The bot needs three secret pieces of information. **Never share these with
anyone** — they're like passwords. They go into a file called `.env`
(Part 3 explains how).

### 2.1 — Telegram bot token

**What it is, in plain English:** a Telegram bot token is the secret
password that lets *this program* (not you) send messages through a bot
account on Telegram.

**How to get one:**

1. Open Telegram (on your phone or computer) and search for **`BotFather`**
   — it has a blue verified checkmark.
2. Tap **Start** (or send the message `/start`).
3. Send the message `/newbot`.
4. BotFather asks for a **name** for your bot — type anything, e.g.
   `My Concert Alerts`.
5. BotFather asks for a **username** — it must end in `bot`, e.g.
   `kk_concert_alerts_bot`. If it's taken, try adding numbers.
6. BotFather replies with a message containing a long code that looks like:
   ```
   123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
   ```
   That whole code is your **bot token**. Copy it (tap and hold to copy on
   mobile, or select and `Cmd+C` on desktop).

### 2.2 — Telegram chat id

**What it is, in plain English:** your chat id is a number that tells the
bot *which conversation* to send messages to — i.e., which Telegram account
is "you".

**How to get one:** we'll use the bot itself to find this out.

1. In Telegram, find the bot you just created (search for the username you
   chose, e.g. `kk_concert_alerts_bot`) and tap **Start** so it can message
   you.
2. We'll come back to actually fetching the chat id in Part 4, after your
   `.env` file has the bot token in it (Part 3). For now, just remember
   you've started a chat with your bot.

### 2.3 — Ticketmaster API key

**What it is, in plain English:** a Ticketmaster API key is a password that
lets this program ask Ticketmaster's website for concert listings —
including presale dates, which Ticketmaster doesn't show anywhere else for
free.

**How to get one:**

1. Go to https://developer.ticketmaster.com/ in your browser.
2. Click **"Get Your API Key"** (top right).
3. Create a free account (no credit card needed) and verify your email if
   asked.
4. Once logged in, click **"My Apps"** in the top menu.
5. Click **"+ New App"** (or similar), fill in any name/description, and
   save.
6. You'll see a field called **"Consumer Key"** — that long string is your
   **Ticketmaster API key**. Copy it.

---

## Part 3 — Create your `.env` file (where secrets live)

1. In the project folder, find the file called **`.env.example`**.
2. Make a copy of it and rename the copy to **`.env`** (note: it starts with
   a dot and has no other extension).
   - In Finder: right-click `.env.example` → **Duplicate**, then rename the
     duplicate to `.env`. If Finder won't let you start a filename with a
     dot, do it in Terminal instead:
     ```bash
     cp .env.example .env
     ```
3. Open `.env` in any plain text editor (TextEdit works — right-click →
   **Open With → TextEdit**).
4. Replace the placeholder text with your real values from Part 2, keeping
   the quote marks, e.g.:
   ```
   TELEGRAM_BOT_TOKEN="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
   TELEGRAM_CHAT_ID="your_numeric_chat_id"
   TICKETMASTER_API_KEY="AbCdEfGhIjKlMnOpQrStUvWx"
   ```
   You don't have your chat id yet — leave that line as-is for now, we'll
   fill it in next (Part 4, Step 4.1).
5. Save the file.

**This `.env` file is never uploaded anywhere** — it's listed in
`.gitignore`, which tells the project to ignore it when sharing code.

---

## Part 4 — Test the bot locally

Make sure Terminal shows `(venv)` at the start of the line (if not, run
`source venv/bin/activate` again from inside the project folder).

### Step 4.1 — Get your chat id

Run:

```bash
python main.py --get-chat-id
```

You'll see a message saying it's waiting. Now, in Telegram, open the chat
with **your bot** and send the message `/start`. Within a few seconds,
Terminal will print your numeric chat id, e.g.:

```
Your Telegram chat id is: 987654321
Add this to your .env file as TELEGRAM_CHAT_ID
```

Copy that number, open `.env` again, and set:

```
TELEGRAM_CHAT_ID="987654321"
```

Save the file.

### Step 4.2 — Send a test alert

This sends one made-up sample message to your Telegram, to confirm
everything is wired up correctly:

```bash
python main.py --test-alert
```

**What you should see:** Terminal prints `Test alert sent! Check your
Telegram.`, and within a few seconds a message appears in your chat with
the bot — a sample concert entry showing what a real digest entry looks
like (artist name, venue, presale info, etc.).

If it fails, double-check your `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`
in `.env` for typos or missing quote marks.

### Step 4.3 — Do a dry run

A **dry run** fetches real concert data and shows you what the digest
*would* say — without actually sending it to Telegram or marking anything
as "seen". This is the safest way to check everything works.

```bash
python main.py --dry-run
```

**What you should see:** log lines showing it checking Ticketmaster and
Bandsintown for each artist, followed by either:

- A printed digest with real upcoming shows for your tracked artists, or
- `(Nothing new today — no message would be sent...)` if there's nothing to
  report yet — this is normal and not an error.

This first run can take a few minutes, since it has to look up every artist.
After the first run, Ticketmaster lookups are cached, so future runs are
faster.

---

## Part 5 — Customising your artist lists

Open the file **`config.yaml`** in a plain text editor (TextEdit is fine).

Near the top you'll see three lists: `must_see`, `legends`, and
`blockbusters`. Each one is a simple list of artist names, like:

```yaml
artist_lists:
  must_see:
    artists:
      - Taylor Swift
      - Adele
      - Lady Gaga
```

**To add an artist:** add a new line with a dash, a space, and the artist's
name, matching the indentation of the lines around it:

```yaml
      - Taylor Swift
      - Adele
      - Lady Gaga
      - My New Favourite Artist
```

**To remove an artist:** delete their line entirely.

Use the artist's name exactly as it appears on Ticketmaster (e.g.
`"Florence + The Machine"`, `"P!nk"`) for the best results. Save the file
and restart the bot (or just run `--dry-run` again) to pick up the change.

### Other settings in `config.yaml`

- `priority_countries: [GB, ES]` — country codes that get the ⭐ PRIORITY
  flag (GB = United Kingdom, ES = Spain). Add more two-letter codes if you
  want, e.g. `[GB, ES, FR]`.
- `daily_run_time: "19:00"` — when the daily digest is sent (24-hour clock,
  UK time).
- `send_when_empty: false` — change to `true` if you'd like a
  "nothing new today" message every day, even when there's nothing to
  report.
- `sources: {ticketmaster: true, bandsintown: true}` — turn a source off by
  changing `true` to `false`.

---

## Part 6 — Running the bot

### Run it once right now (and send a real digest)

```bash
python main.py --run-now
```

This checks everything and, if there's something new, **sends a real
message to your Telegram**. Anything it sends gets remembered, so it won't
be sent again tomorrow.

### Run it continuously (so it sends a digest every day automatically)

```bash
python main.py
```

This starts the bot and leaves it running, sending a digest once a day at
the time set by `daily_run_time`. It only keeps running while this Terminal
window stays open and your Mac is awake — for a bot that runs **all the
time**, even when your laptop is closed, see Part 7 (deployment).

Press `Ctrl + C` in Terminal to stop it.

### Debugging a single source

If you want to check just one source (useful if one of them seems broken):

```bash
python main.py --dry-run --source ticketmaster
python main.py --dry-run --source bandsintown
```

---

## Part 7 — Deploying so it runs 24/7 (Railway)

If you close your laptop, the bot stops. To have it running **all the
time** without your computer, deploy it to **Railway** — a beginner-
friendly cloud hosting service with a free tier and no credit card required
to start.

Railway will run this project using the included `Dockerfile`, which is
just a recipe telling Railway how to set up and run the bot — you don't
need to understand it.

### 7.1 — Push this project to GitHub

Railway deploys from a GitHub repository. If this project isn't already on
GitHub, create a new repository on https://github.com and upload this
project's folder to it (GitHub's website lets you drag-and-drop files if
you're not comfortable with Git commands).

### 7.2 — Create a Railway project

1. Go to https://railway.app and click **Login**, then **sign up with
   GitHub** (free).
2. Click **New Project** → **Deploy from GitHub repo**.
3. Select this project's repository. Railway will detect the `Dockerfile`
   and start building automatically.

### 7.3 — Add your secret keys to Railway

Your `.env` file stays on your computer — you never upload it. Instead, you
type the same values into Railway's settings:

1. In your new Railway project, click on the service (it'll have the
   project's name), then click the **Variables** tab.
2. Click **+ New Variable** and add each of these one at a time (the names
   must match exactly):
   - `TELEGRAM_BOT_TOKEN` → paste your bot token
   - `TELEGRAM_CHAT_ID` → paste your chat id
   - `TICKETMASTER_API_KEY` → paste your Ticketmaster key
3. Railway will automatically restart the bot with these values. Your bot
   is now running 24/7 — check your Telegram around your scheduled time
   (default 7:00 PM UK time) the next day.

> **Tip:** Railway's free tier includes enough hours per month to run this
> small bot continuously. If you ever see it stop, check the **Usage** tab
> in Railway.

### 7.4 — Keeping the "already seen" memory

The bot remembers what it's already told you about in a small database file
inside the `data/` folder. On Railway, this folder lives inside the
container and normally persists across restarts of the same deployment. If
you ever redeploy from scratch and get a flood of "new" announcements you've
already seen, that's expected — it just means the memory was reset.

---

## Part 8 — Maintenance: what to do later

### Adding or removing artists later

Edit `config.yaml` as described in Part 5, then either:

- **Locally:** just run `python main.py --dry-run` to check it, then
  `python main.py --run-now` if you want.
- **On Railway:** edit `config.yaml`, upload the change to GitHub (Railway
  will redeploy automatically), or edit the file directly in GitHub's web
  editor and Railway will pick it up.

### If the Bandsintown scraper stops working

Bandsintown doesn't offer an official way for this bot to read many
artists' pages, so this part of the bot reads the same data your web
browser would load when you visit an artist's Bandsintown page. If
Bandsintown redesigns their website, this can stop working.

**This is designed to fail safely** — if it breaks, you'll see warning
messages in the logs like:

```
Bandsintown: __NEXT_DATA__ block not found in page (site layout may have changed)
```

but the rest of the bot (including Ticketmaster, which is the only source
with presale info) **will keep working normally**. You won't lose your
digest — you'll just temporarily miss Bandsintown-only listings.

If you see this warning every day for a while:

1. You (or a developer) can turn Bandsintown off entirely by setting
   `bandsintown: false` under `sources:` in `config.yaml`, until it's fixed.
2. Fixing it means updating the code in
   `concert_bot/sources/bandsintown.py` to match Bandsintown's new page
   structure — this requires a developer, but the rest of the bot is
   unaffected in the meantime.

### Resetting "already seen" history

If you ever want the bot to re-report everything as if it were brand new
(for testing), delete the file `data/state.db` and run the bot again.

---

## Troubleshooting

**"command not found: python3"**
Python isn't installed — see Step 1.1.

**"No module named 'requests'" (or any other module)**
Your virtual environment isn't active, or dependencies aren't installed.
Run:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Test alert fails**
Double-check `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env` — no
extra spaces, and the quote marks are still there. Make sure you've sent
`/start` to your bot at least once.

**"Ticketmaster: TICKETMASTER_API_KEY not set"**
Your `.env` file is missing the key, or it has a typo. Re-check Part 2.3
and Part 3.

**The first run sends nothing**
This is normal — the very first run only *records* what's currently
out there as "already seen" so you don't get flooded with shows you've
known about for ages. From the next run onward, you'll only see genuinely
new announcements.

---

## For developers: project structure

```
concert_bot/
  config.py            # loads config.yaml + secrets from environment variables
  models.py             # Event / MergedEvent / Presale data models, normalization helpers
  aggregator.py          # dedupe + fuzzy venue matching + priority sorting
  state.py               # SQLite "already seen" store
  telegram_sender.py     # digest formatting + Telegram Bot API calls
  scheduler.py           # APScheduler daily job
  sources/
    base.py              # abstract Source interface
    ticketmaster.py       # Ticketmaster Discovery API v2 (attractions + events + presales)
    bandsintown.py        # Bandsintown artist-page scraper
main.py                  # CLI: --run-now / --dry-run / --test-alert / --get-chat-id / --source
tests/                    # pytest tests + fixtures for each source and the aggregator
```

Run the tests with:

```bash
pip install -r requirements-dev.txt
pytest
```
