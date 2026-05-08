import requests
import re
import json

EXCLUDED_DOMAINS = {
    "sentry.wixpress.com",
    "sentry-next.wixpress.com"
}

FIREBASE_DB_URL = "https://trackingclients-default-rtdb.firebaseio.com/emails.json"


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

    local = email.split("@")[0]
    if len(local) > 40:
        return False

    return True


def save_to_firebase(email):
    try:
        data = {"email": email}
        r = requests.post(FIREBASE_DB_URL, data=json.dumps(data))
        if r.ok:
            print("Saved:", email)
        else:
            print("Firebase error:", r.text)
    except Exception as e:
        print("Firebase exception:", e)


def scrape_urls(urls):
    all_emails = set()

    for url in urls:
        url = clean_url(url)
        print("Scraping:", url)

        emails = extract_emails_from_url(url)

        for email in emails:
            if is_valid_email(email):
                all_emails.add(email)

    print("\nSaving to Firebase...\n")

    for email in all_emails:
        save_to_firebase(email)

    print("\nDONE. Total emails:", len(all_emails))


def main():
    # 🔥 PUT YOUR TARGET WEBSITES HERE
    urls = [
        "https://example.com",
        "https://example.org"
    ]

    scrape_urls(urls)


if __name__ == "__main__":
    main()
