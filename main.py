import requests
import re
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# 🔥 Firebase (your database)
FIREBASE_DB_URL = "https://trackingclients-default-rtdb.firebaseio.com/emails.json"

# 🚫 blocked domains
EXCLUDED_DOMAINS = {
    "sentry.wixpress.com",
    "sentry-next.wixpress.com"
}

# ---------------- EMAIL EXTRACTION ----------------

def extract_emails(html):
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return list(set(re.findall(pattern, html)))


def is_valid_email(email):
    if any(email.lower().endswith(x) for x in [".png", ".jpg", ".jpeg", ".gif"]):
        return False

    if ".." in email:
        return False

    domain = email.split("@")[-1]
    if domain in EXCLUDED_DOMAINS:
        return False

    local = email.split("@")[0]
    if len(local) < 2 or len(local) > 50:
        return False

    return True


# ---------------- SCRAPE WEBSITE ----------------

def scrape_url(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(url, headers=headers, timeout=10)
        return extract_emails(response.text)

    except Exception as e:
        print("Error scraping:", url, e)
        return []


# ---------------- SAVE TO FIREBASE ----------------

def save_to_firebase(email):
    try:
        requests.post(
            FIREBASE_DB_URL,
            data=json.dumps({"email": email})
        )
    except Exception as e:
        print("Firebase error:", e)


# ---------------- API ENDPOINT ----------------

@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.json

    if not data or "urls" not in data:
        return jsonify({"error": "No URLs provided"}), 400

    urls = data["urls"][:100]   # 🔥 limit to 100

    all_emails = set()

    for url in urls:
        print("Scraping:", url)
        emails = scrape_url(url)

        for email in emails:
            if is_valid_email(email):
                all_emails.add(email)

    # save to firebase
    for email in all_emails:
        save_to_firebase(email)

    return jsonify({
        "status": "success",
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
