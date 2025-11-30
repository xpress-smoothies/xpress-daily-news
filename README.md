# Xpress Daily News Script

A simple Python script that fetches Google News RSS results for hemp/THC-ban–related search topics and emails a structured daily digest.

## Setup

1. Clone the repo

    git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
    cd YOUR_REPO


2. Setup Your "Virtual Environment"

From your project root:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

You're off to the races.

When you're done working:
```
deactivate
```

And whenever you come back to the project:

```
source .venv/bin/activate
```

2. Install dependencies

    pip install -r requirements.txt

3. Create your `.env`

    ```
    cp .env.example .env
    ```
    # then edit .env with your SMTP credentials + queries

4. Get Email Password 


1️⃣ Make sure you have 2-Step Verification ON

App passwords only show up if you’ve enabled 2FA.

Turn it on here:
https://myaccount.google.com/security
 → “2-Step Verification”

2️⃣ Go to the App Passwords page

Once 2FA is enabled:

👉 https://myaccount.google.com/apppasswords

Google might ask you to re-login.

3️⃣ Create a new password

Under “Select app”, choose Mail

Under “Select device”, choose “Other” and name it something like xpress-daily-news

Click Generate

4️⃣ Copy the 16-character password

It’ll look like this (but with different letters):

abcd efgh ijkl mnop


Use it without spaces:

abcdefghijklmnop


That is your EMAIL_PASSWORD.

5️⃣ Put it in your .env

Example:

EMAIL_USER="yourgmail@gmail.com"
EMAIL_PASSWORD="abcdefghijklmnop"


And you’re done — Gmail SMTP will now authenticate.


5. Run the script

    python3 news-digest-script.py


## Cron Job (Optional)


Make the sh file executable:
```
chmod +x run-news-digest-script.sh
```

Edit path in sh file from "Users/jim/Git-Projects/xpress-daily-news" to your path.

test it:
```
./run-news-digest-script.sh
```

Run every day at 8am:
```
crontab -e
```

Add this line (Changing to your system path):

```
0 8 * * * /Users/jim/Git-Projects/xpress-daily-news/run_news_digest_script.sh > /Users/jim/Git-Projects/xpress-daily-news/cron.log 2>&1
```

<br/>
---


## Setup Local Certs

If you see the error, "Exception: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1000)>"

Try this (iOS):
```
python -m pip install certifi
```

Then, locate and run the script in your specific Python version's directory:
```
open /Applications/Python\ 3.12/Install\ Certificates.command
```