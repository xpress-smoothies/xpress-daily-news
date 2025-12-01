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
import pytz
import urllib.request

# ---------------------------------------------------------------
# LOAD CONFIG FROM .env
# ---------------------------------------------------------------
load_dotenv()

def require_env(key: str) -> str:
    """Fetch an env variable and error out if missing."""
    val = os.getenv(key)
    if val is None or val.strip() == "":
        sys.stderr.write(f"ERROR: Missing required environment variable: {key}\n")
        sys.stderr.flush()
        sys.exit(1)
    return val

# Required values
try:
    SMTP_SERVER = require_env("SMTP_SERVER")
    SMTP_PORT = int(require_env("SMTP_PORT"))
    EMAIL_USERNAME = require_env("EMAIL_USERNAME")
    EMAIL_PASSWORD = require_env("EMAIL_PASSWORD")
    EMAIL_FROM = os.getenv("EMAIL_FROM", EMAIL_USERNAME)
    EMAIL_TO = [email.strip() for email in require_env("EMAIL_TO").split("|")]

    _raw_queries = require_env("NEWS_QUERIES")
    NEWS_QUERIES = [q.strip() for q in _raw_queries.split("|") if q.strip()]

    if not NEWS_QUERIES:
        sys.stderr.write("ERROR: NEWS_QUERIES is set but empty or unparseable. Provide comma-separated search terms.\n")
        sys.stderr.flush()
        sys.exit(1)

    MAX_HEADLINES_PER_QUERY = int(os.getenv("MAX_HEADLINES_PER_QUERY", "5"))

except ValueError as e:
    sys.stderr.write(f"ERROR: Configuration issue (e.g., non-integer port): {e}\n")
    sys.stderr.flush()
    sys.exit(1)

# ---------------------------------------------------------------
# CORE FUNCTIONS
# ---------------------------------------------------------------

def build_google_news_rss_url(query: str) -> str:
    encoded = quote_plus(query)
    return f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"

def fetch_news_for_query(query: str):
    url = build_google_news_rss_url(query)
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read()
        feed = feedparser.parse(content)
        sys.stderr.write(f"SUCCESS: Fetched feed for '{query}' with {len(feed.entries)} entries.\n")
        sys.stderr.flush()
    except Exception as e:
        sys.stderr.write(f"ERROR: Failed to fetch feed for '{query}'. Exception: {e}\n")
        sys.stderr.flush()
        return []

    items = []
    for entry in feed.entries[:MAX_HEADLINES_PER_QUERY]:
        title = getattr(entry, "title", None)
        link = getattr(entry, "link", None)
        if not title or not link:
            continue

        source = getattr(entry, "source", None)
        if source:
            if hasattr(source, "title"):
                source = source.title
            elif isinstance(source, dict) and "title" in source:
                source = source["title"]
        else:
            source = ""

        items.append({
            "title": title,
            "link": link,
            "published": getattr(entry, "published", ""),
            "source": source
        })

    if not items:
        sys.stderr.write(f"DEBUG: Feed for '{query}' returned 0 valid entries.\n")
    else:
        sys.stderr.write(f"SUCCESS: Feed for '{query}' returned {len(items)} valid headlines.\n")
    sys.stderr.flush()

    return items

def compile_digest():
    all_items = []
    seen_links = set()
    total_headlines = 0

    for query in NEWS_QUERIES:
        news_items = fetch_news_for_query(query)
        filtered = [item for item in news_items if item["link"] not in seen_links]

        for item in filtered:
            seen_links.add(item["link"])
            total_headlines += 1

        all_items.append((query, filtered))

    ny_tz = pytz.timezone("America/New_York")
    ny_time = datetime.now(ny_tz)
    today_str = ny_time.strftime("%Y-%m-%d")
    subject = f"Xpress News Digest – {today_str}"

    # ----- text body -----
    text_lines = [
        f"Xpress News Digest – {today_str}",
        "-" * 50, ""
    ]

    # ----- HTML body -----
    html_lines = [
        f"<h2 style='font-size:1.6em;'>{subject}</h2>",
        "<hr>",
    ]

    if total_headlines == 0:
        text_lines.append("No recent headlines found for any of your search terms.")
        html_lines.append("<p>No recent headlines found for any of your search terms.</p>")

    for query, items in all_items:
        text_lines.append(f"=== {query} ===")
        html_lines.append(
            f"<h3 style='font-size:1.4em; text-decoration:underline; margin-top:1em;'>{query}</h3>"
        )

        if items:
            html_lines.append("<ul>")
            for item in items:
                # Source as hyperlink
                if item['source']:
                    src_html = f"<br/><a href='{item['link']}'>Read the full article at {item['source']}</a>"
                    src_text = f"[{item['source']}]"
                else:
                    src_html = ""
                    src_text = ""

                text_lines.append(f"- {item['title']} {src_text}")
                html_lines.append(f"<li><b>{item['title']}</b> {src_html}</li>")
            html_lines.append("</ul>")
        else:
            text_lines.append("(No recent headlines for this query)\n")
            html_lines.append("<p>(No recent headlines for this query)</p>")

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
    try:
        subject, text_body, html_body = compile_digest()
        send_email(subject, text_body, html_body)
        sys.stderr.write("SUCCESS: Email sent successfully!\n")
        sys.stderr.flush()
    except Exception as e:
        sys.stderr.write(f"FATAL ERROR during digest creation or email sending: {e}\n")
        sys.stderr.flush()
        sys.exit(1)

if __name__ == "__main__":
    main()
