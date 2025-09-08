import requests
import json
from datetime import date, datetime
from zoneinfo import ZoneInfo
import os
import smtplib
from email.message import EmailMessage

# --- Configuration ---
# New Haven, CT
LATITUDE = '41'
LONGITUDE = '-73'
# API_KEY will be loaded from GitHub Secrets
API_KEY = os.environ.get('API_KEY')
FILENAME = f'{date.today().isoformat()}.json'
QUALITY_THRESHOLD = 0.30

# --- Function to fetch data ---
def get_forecast_data():
    url = f'https://api.sunsethue.com/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&key={API_KEY}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        print("Data fetched from API successfully.")
        return data
    except requests.exceptions.RequestException as e:
        print(f"An error occurred fetching data: {e}")
        return None

# --- Function to check for good sunsets ---
def find_good_sunsets(data):
    if not data or 'data' not in data:
        return None
    good_sunsets = []
    local_tz = ZoneInfo("America/New_York")
    for forecast in data['data']:
        if forecast['type'] == 'sunset' and forecast['quality'] >= QUALITY_THRESHOLD:
            sunset_time_utc = forecast['time']
            quality = forecast['quality_text']
            cloud_cover = int(forecast['cloud_cover'] * 100)
            utc_time = datetime.fromisoformat(sunset_time_utc.replace('Z', '+00:00'))
            local_time = utc_time.astimezone(local_tz)        # Convert from UTC to your local timezone
            date_str = local_time.strftime('%A, %b %d')
            # The '%Z' will correctly show 'EDT' or 'EST'
            time_str = local_time.strftime('%-I:%M %p %Z')

            good_sunsets.append(
                f"🌅 Good Sunset Alert!\n"
                f"Date: {date_str}\n"
                f"Time: {time_str}\n"
                f"Quality: {quality}\n"
                f"Cloud Cover: {cloud_cover}%"
            )
    return good_sunsets

# --- Function to send email ---
def send_email_notification(subject, body):
    sender_email = os.environ.get('EMAIL_USER')
    sender_password = os.environ.get('EMAIL_PASS')
    
    recipient_email = "isstgml@gmail.com"

    if not all([sender_email, sender_password, API_KEY]):
        print("A required secret (API_KEY, EMAIL_USER, or EMAIL_PASS) is not set. Aborting.")
        return

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email

    try:
        # Using Gmail's SMTP server as an example
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
            print("Notification email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

# --- Main execution ---
if __name__ == "__main__":
    forecast_data = get_forecast_data()
    # with open(FILENAME, 'r') as f:
    #     forecast_data = json.load(f)
    great_sunsets = find_good_sunsets(forecast_data)
    
    if great_sunsets:
        full_message = "\n\n".join(great_sunsets)
        print(full_message)
        send_email_notification("Good Sunset Forecast!", full_message)
    else:
        print("No good sunsets predicted in the next 3 days.")