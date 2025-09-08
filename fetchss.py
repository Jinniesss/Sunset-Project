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
API_KEY = os.environ.get('API_KEY')
QUALITY_THRESHOLD = 0.75
RECIPIENT_EMAIL = "isstgml@gmail.com" # Define recipient email here

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

# --- Function to find and format high-quality sunsets ---
def find_high_quality_sunsets(data):
    if not data or 'data' not in data:
        return None
        
    good_sunsets_details = []
    local_tz = ZoneInfo("America/New_York")

    for forecast in data['data']:
        if forecast['type'] == 'sunset' and forecast['quality'] >= QUALITY_THRESHOLD:
            # --- Time Conversions ---
            # Helper function to convert UTC iso strings to local time strings
            def format_local_time(iso_str, fmt):
                utc_dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
                local_dt = utc_dt.astimezone(local_tz)
                return local_dt.strftime(fmt)

            # --- Formatting all the data points ---
            date_str = format_local_time(forecast['time'], '%A, %b %d')
            time_str = format_local_time(forecast['time'], '%-I:%M %p %Z')
            
            quality_text = forecast['quality_text']
            quality_score = forecast['quality']
            cloud_cover = int(forecast['cloud_cover'] * 100)
            direction = forecast['direction']
            
            golden_hour_start = format_local_time(forecast['magics']['golden_hour'][0], '%-I:%M %p')
            golden_hour_end = format_local_time(forecast['magics']['golden_hour'][1], '%-I:%M %p') 
            
            blue_hour_start = format_local_time(forecast['magics']['blue_hour'][0], '%-I:%M %p')
            blue_hour_end = format_local_time(forecast['magics']['blue_hour'][1], '%-I:%M %p')

            # --- Building the text block for this sunset ---
            details = f"""
☀️☀️☀️☀️☀️☀️☀️☀️☀️☀️☀️☀️
当当当当！马上有好看的日落！
☀️☀️☀️☀️☀️☀️☀️☀️☀️☀️☀️☀️

日期: {date_str}
日落时间: {time_str}
预测好看程度: {quality_text} (分数: {quality_score:.2f})
云覆盖率: {cloud_cover}%
太阳方向: {direction}°

详细时间:
  - 💛Golden Hour: {golden_hour_start} - {golden_hour_end}
  - 💙Blue Hour:   {blue_hour_start} - {blue_hour_end}


"""
            good_sunsets_details.append(details)
    end = """
有时间去看看吧嘻嘻! 🌅🌇🌄

From 你的去去😚
"""
    good_sunsets_details.append(end)
            
    return good_sunsets_details

# --- Function to send plain text email ---
def send_email_notification(subject, body):
    sender_email = os.environ.get('EMAIL_USER')
    sender_password = os.environ.get('EMAIL_PASS')

    if not all([sender_email, sender_password, API_KEY]):
        print("A required secret (API_KEY, EMAIL_USER, or EMAIL_PASS) is not set. Aborting.")
        return

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = RECIPIENT_EMAIL

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
            print("Notification email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

# --- Main execution ---
if __name__ == "__main__":
    forecast_data = get_forecast_data()
    
    if forecast_data:
        high_quality_sunsets = find_high_quality_sunsets(forecast_data)
        
        if high_quality_sunsets:
            # Join all the detailed text blocks together
            full_message = "\n".join(high_quality_sunsets)
            print("High-quality sunset found. Sending notification...")
            print(full_message)
            send_email_notification("🌅 去去检测到好看的日落!!", full_message)
        else:
            print("No high-quality sunsets predicted. No email will be sent.")