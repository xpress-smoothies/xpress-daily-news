# Xpress Daily News Script

A simple Python script that fetches Google News RSS results for hemp/THC-ban–related search topics and emails a structured daily digest.

## Setup

1. Clone the repo

    git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
    cd YOUR_REPO

2. Install dependencies

    pip install -r requirements.txt

3. Create your `.env`

    cp .env.example .env
    # then edit .env with your SMTP credentials + queries

4. Run the script

    python3 digest.py

## Cron Job (Optional)

Run every day at 8am:

    crontab -e

Add this line:

    0 8 * * * /usr/bin/python3 /full/path/to/digest.py

