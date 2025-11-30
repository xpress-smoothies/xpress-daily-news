#!/usr/bin/env python3
import feedparser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from urllib.parse import quote_plus
from dotenv import load_dotenv
import os
import sys

# ---------------------------------------------------------------
# LOAD CONFIG FROM .env
# ---------------------------------------------------------------
load_dotenv()

def require_env(key: str) -> str:
    """Fetch an env variable and error out if missing."""
    val = os.getenv(key)
    if val is None or val.strip() == "":
        print(f"ERROR: Missing required environment variable: {key}")
        sys.exit(1)
    return val

# Required values
SMTP_SERVER = require_env("SMTP_SERVER")
SMTP_PORT = int(require_env("SMTP_PORT"))
EMAIL_USERNAME = require_env("EMAIL_USERNAME")
EMAIL_PASSWORD = require_env("EMAIL_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM", EMAIL_USERNAME)
EMAIL_TO = [email.strip() for email in require_env("EMAIL_TO").split(",")]

# NEWS_QUERIES *must* exist, and must parse
_raw_queries = require_env("NEWS_QUERIES")
NEWS_QUERIES = [q.strip() for q in _raw_queries.split(",") if q.strip()]

if not NEWS_QUERIES:
    print("ERROR: NEWS_QUERIES is set but empty or unparseable. Provide comma-separated search terms.")
    sys.exit(1)

# Optional
MAX_HEADLINES_PER_QUERY = int(os.getenv("MAX_HEADLINES_PER_QUERY", "5"))

# ---------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------

def build_google_news_rss_url(query: str) -> str:
    encoded = quote_plus(query)
    return f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"


def fetch_news_for_query(query: str):
    url = build_google_news_rss_url(query)
    feed = feedparser.parse(url)
    items = []

    for entry in feed.entries[:MAX_HEADLINES_PER_QUERY]:
        source = ""
        if "source" in entry and "title" in entry.source:
            source = entry.source.title
        elif "publisher" in entry:
            source = entry.publisher

        items.append({
            "title": entry.title,
            "link": entry.link,
            "published": getattr(entry, "published", ""),
            "source": source
        })

    return items


def compile_digest():
    all_items = []
    seen_links = set()

    for query in NEWS_QUERIES:
        news_items = fetch_news_for_query(query)
        filtered = [item for item in news_items if item["link"] not in seen_links]

        for item in filtered:
            seen_links.add(item["link"])

        all_items.append((query, filtered))

    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    subject = f"Hemp / THC Ban Daily Digest – {today_str}"

    # ----- text body -----
    text_lines = [
        f"Daily Hemp / THC Ban Digest – {today_str}",
        "-" * 50, ""
    ]

    # ----- HTML body -----
    html_lines = [
        f"<h2>Daily Hemp / THC Ban Digest – {today_str}</h2>",
        "<hr>",
    ]

    for query, items in all_items:
        text_lines.append(f"=== {query} ===")
        html_lines.append(f"<h3>{query}</h3><ul>")

        if not items:
            text_lines.append("(No recent headlines)\n")
            html_lines.append("<li>(No recent headlines)</li>")
        else:
            for item in items:
                src = f" [{item['source']}]" if item['source'] else ""

                text_lines.append(f"- {item['title']}{src}")
                text_lines.append(f"  {item['link']}\n")

                html_lines.append(
                    f"<li><b>{item['title']}</b>{src}<br>"
                    f"<a href='{item['link']}'>{item['link']}</a></li>"
                )

        html_lines.append("</ul>")

    return subject, "\n".join(text_lines), "\n".join(html_lines)


def send_email(subject: str, text_body: str, html_body: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = ", ".join(EMAIL_TO)

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())


def main():
    subject, text_body, html_body = compile_digest()
    send_email(subject, text_body, html_body)


if __name__ == "__main__":
    main()
