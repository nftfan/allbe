import requests
import re
import json
import os

EXCLUDED_DOMAINS = {
    "sentry.wixpress.com",
    "sentry-next.wixpress.com"
}

FIREBASE_DB_URL = "https://trackingclients-default-rtdb.firebaseio.com/emails.json"
EMAILS_FILE = "emails.txt"


def load_emails_from_file(filename=EMAILS_FILE):
    if not os.path.exists(filename):
        return set()
    with open(filename, "r") as f:
        return {line.strip() for line in f if line.strip()}


def append_emails_to_file(emails, filename=EMAILS_FILE):
    with open(filename, "a") as f:
        for email in emails:
            f.write(email + "\n")


def save_email_to_firebase(email):
    try:
        data = {"email": email}
        r = requests.post(FIREBASE_DB_URL, data=json.dumps(data))
        return r.ok
    except:
        return False


def clean_url(url):
    url = url.replace("\\", "").strip()
    if not url.startswith("http"):
        url = "https://" + url
    return url


def extract_emails_from_url(url):
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        emails = re.findall(email_pattern, r.text)
        return list(set(emails))
    except:
        return []


def is_valid_email(email):
    if any(email.lower().endswith(x) for x in [".png", ".jpg", ".jpeg", ".gif"]):
        return False
    if ".." in email:
        return False
    domain = email.split("@")[-1]
    if domain in EXCLUDED_DOMAINS:
        return False
    return True


def filter_and_save(emails):
    existing = load_emails_from_file()
    new_emails = []

    for email in set(emails):
        if is_valid_email(email):
            if email not in existing:
                if save_email_to_firebase(email):
                    new_emails.append(email)

    if new_emails:
        append_emails_to_file(new_emails)

    return new_emails


def main():
    # 🔥 PUT YOUR TARGET WEBSITES HERE
    urls = [
        "https://example.com",
        "https://example.org"
    ]

    all_emails = []

    for url in urls:
        url = clean_url(url)
        print("Scraping:", url)
        emails = extract_emails_from_url(url)
        all_emails.extend(emails)

    valid = filter_and_save(all_emails)

    print("\nDONE")
    print("Valid emails found:", valid)


if __name__ == "__main__":
    main()
