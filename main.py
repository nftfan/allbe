import requests
import re
import json
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ---------------- FIREBASE ----------------
FIREBASE_DB_URL = "https://trackingclients-default-rtdb.firebaseio.com/emails.json"

# ---------------- SETTINGS ----------------
EXCLUDED_DOMAINS = {
    "sentry.wixpress.com",
    "sentry-next.wixpress.com"
}

CONTACT_PATHS = ["/contact", "/contact-us", "/about", "/impressum"]

# ---------------- CLEAN URL ----------------
def clean_url(url):
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    return url

# ---------------- EMAIL EXTRACTION ----------------
def extract_emails(text):
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return list(set(re.findall(pattern, text)))


def is_valid_email(email):
    if any(email.lower().endswith(x) for x in [".png", ".jpg", ".jpeg", ".gif"]):
        return False
    if ".." in email:
        return False

    domain = email.split("@")[-1]
    if domain in EXCLUDED_DOMAINS:
        return False

    return True

# ---------------- SCRAPER ----------------
def scrape_url(url):
    emails = set()
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        emails.update(extract_emails(r.text))

        # try contact pages
        for path in CONTACT_PATHS:
            try:
                r2 = requests.get(url.rstrip("/") + path, headers=headers, timeout=5)
                emails.update(extract_emails(r2.text))
            except:
                pass

    except Exception as e:
        print("Error scraping:", url, e)

    return list(emails)

# ---------------- FIREBASE SAVE ----------------
def save_to_firebase(email, session_id):
    url = f"https://trackingclients-default-rtdb.firebaseio.com/sessions/{session_id}.json"
    try:
        requests.post(url, data=json.dumps({"email": email}))
    except:
        pass

# ---------------- API ----------------
@app.route("/scrape", methods=["POST"])
def scrape():

    raw = request.data.decode("utf-8").strip()
    urls = []

    # JSON input
    try:
        data = request.get_json(silent=True)
        if data and "urls" in data:
            urls = data["urls"]
        else:
            urls = raw.splitlines()
    except:
        urls = raw.splitlines()

    # clean + limit
    urls = [clean_url(u) for u in urls if u.strip()]
    urls = urls[:100]

    session_id = str(int(time.time()))
    all_emails = set()

    for url in urls:
        print("Scraping:", url)

        emails = scrape_url(url)

        for email in emails:
            if is_valid_email(email):
                all_emails.add(email)
                save_to_firebase(email, session_id)

    return jsonify({
        "status": "success",
        "session_id": session_id,
        "total_emails": len(all_emails),
        "emails": list(all_emails)
    })

# ---------------- HEALTH CHECK ----------------
@app.route("/")
def home():
    return "Email Scraper API is running 🚀"

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
