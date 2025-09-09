import requests
import json
from datetime import date, datetime
from zoneinfo import ZoneInfo
import os
import smtplib
from email.message import EmailMessage

# --- Configuration ---
API_KEY = os.environ.get('API_KEY')
QUALITY_THRESHOLD = 0.75 # Set your desired quality threshold here

# List of locations and recipients. Add or remove friends here!
LOCATIONS = [
    {
        "name": "Jinnie",
        "latitude": "41",
        "longitude": "-73",
        "timezone": "America/New_York",
        "recipient_email": "isstgml@gmail.com", # Your email for New Haven
        "place": "New Haven"
    },
    {
        "name": "宝宝",
        "latitude": "31.2304",
        "longitude": "121.4737",
        "timezone": "Asia/Shanghai",
        "recipient_email": "wuqzh@shanghaitech.edu.cn", # Change to their email
        "place": "上海"
    # },
    # {
    #     "name": "dd",
    #     "latitude": "30.2672",
    #     "longitude": "-97.7431",
    #     "timezone": "America/Chicago",
    #     "recipient_email": "isstgml@gmail.com", # Change to their email
    #     "place": "Austin"
    }
]

# --- Function to fetch data for a specific location ---
def get_forecast_data(latitude, longitude):
    url = f'https://api.sunsethue.com/forecast?latitude={latitude}&longitude={longitude}&key={API_KEY}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        print(f"Data fetched for ({latitude}, {longitude}) successfully.")
        return data
    except requests.exceptions.RequestException as e:
        print(f"An error occurred fetching data for ({latitude}, {longitude}): {e}")
        return None

# --- Function to find and format high-quality sunsets ---
def find_high_quality_sunsets(data, timezone):
    if not data or 'data' not in data:
        return [] # Return an empty list
        
    local_tz = ZoneInfo(timezone)
    good_sunsets_details = []

    for forecast in data['data'][:5]:
        if forecast.get('type') == 'sunset' and forecast.get('quality', 0.0) >= QUALITY_THRESHOLD:
            # Helper function to convert UTC iso strings to local time strings
            def format_local_time(iso_str, fmt):
                utc_dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
                local_dt = utc_dt.astimezone(local_tz)
                return local_dt.strftime(fmt)

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
            
    return good_sunsets_details

# --- Function to send plain text email ---
def send_email_notification(subject, body, recipient_email):
    sender_email = os.environ.get('EMAIL_USER')
    sender_password = os.environ.get('EMAIL_PASS')

    if not all([sender_email, sender_password, API_KEY]):
        print("A required secret (API_KEY, EMAIL_USER, or EMAIL_PASS) is not set. Aborting email send.")
        return

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
            print(f"Notification email sent successfully to {recipient_email}!")
    except Exception as e:
        print(f"Failed to send email to {recipient_email}: {e}")

# --- Main execution loop ---
if __name__ == "__main__":
    for location in LOCATIONS:
        print(f"\n--- Checking for sunsets in {location['name']} ---")
        forecast_data = get_forecast_data(location['latitude'], location['longitude'])
    
        if forecast_data:
            high_quality_sunsets = find_high_quality_sunsets(forecast_data, location['timezone'])
        
            if high_quality_sunsets:
                opening_message = f"🥰泥好呀{location['name']}🥰\n"
                
                high_quality_sunsets.insert(0, opening_message)
                closing_message = "\n有时间去看看吧嘻嘻! 🌅🌇🌄\n\nFrom 你的去去😚"
                high_quality_sunsets.append(closing_message)

                full_message = "\n".join(high_quality_sunsets)
                print(f"High-quality sunset(s) found for {location['name']}. Sending notification...")
                print(full_message)
                
                send_email_notification(
                    subject=f"🌅 去去检测到{location['place']}好看的日落!!",
                    body=full_message,
                    recipient_email=location['recipient_email']
                )
            else:
                print(f"No high-quality sunsets predicted for {location['name']}. No email will be sent.")