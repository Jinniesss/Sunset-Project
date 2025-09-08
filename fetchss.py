import requests
import json
from datetime import date, datetime
from zoneinfo import ZoneInfo
import os
import smtplib
from email.message import EmailMessage
# New import needed for HTML emails
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- Configuration ---
# New Haven, CT
LATITUDE = '41'
LONGITUDE = '-73'
API_KEY = os.environ.get('API_KEY')
QUALITY_THRESHOLD = 0.30
RECIPIENT_EMAIL = "isstgml@gmail.com" # Define recipient email here

# --- Function to fetch data (no changes) ---
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

# --- Function to format all sunsets for the email ---
def format_all_sunsets_html(data):
    if not data or 'data' not in data:
        return None, False
        
    html_rows = ""
    found_good_sunset = False
    local_tz = ZoneInfo("America/New_York")

    # Define emojis and colors for different quality levels
    quality_styles = {
        'Good': {'emoji': '🌅', 'color': '#28a745'},
        'Fair': {'emoji': '🌇', 'color': '#ffc107'},
        'Poor': {'emoji': '☁️', 'color': '#6c757d'}
    }

    for forecast in data['data']:
        if forecast['type'] == 'sunset':
            quality_text = forecast['quality_text']
            style = quality_styles.get(quality_text, quality_styles['Poor'])
            
            # Check if at least one good sunset exists to trigger the email
            if forecast['quality'] >= QUALITY_THRESHOLD:
                found_good_sunset = True

            # Convert times
            utc_time = datetime.fromisoformat(forecast['time'].replace('Z', '+00:00'))
            local_time = utc_time.astimezone(local_tz)
            
            golden_hour_start_local = datetime.fromisoformat(forecast['magics']['golden_hour'][0].replace('Z', '+00:00')).astimezone(local_tz)
            blue_hour_end_local = datetime.fromisoformat(forecast['magics']['blue_hour'][1].replace('Z', '+00:00')).astimezone(local_tz)

            # Build the HTML row for this sunset
            html_rows += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #dee2e6;">{local_time.strftime('%A, %b %d')}</td>
                <td style="padding: 12px; border-bottom: 1px solid #dee2e6;">{local_time.strftime('%-I:%M %p %Z')}</td>
                <td style="padding: 12px; border-bottom: 1px solid #dee2e6; color: {style['color']}; font-weight: bold;">
                    {style['emoji']} {quality_text}
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #dee2e6;">{int(forecast['cloud_cover'] * 100)}%</td>
                <td style="padding: 12px; border-bottom: 1px solid #dee2e6; font-family: monospace, monospace; white-space: nowrap;">
                    {golden_hour_start_local.strftime('%-I:%M%p')} -- SUNSET -- {blue_hour_end_local.strftime('%-I:%M%p')}
                </td>
            </tr>
            """
            
    return html_rows, found_good_sunset

# --- Updated Function to send HTML email ---
def send_email_notification(subject, html_body):
    sender_email = os.environ.get('EMAIL_USER')
    sender_password = os.environ.get('EMAIL_PASS')
    
    if not all([sender_email, sender_password, API_KEY]):
        print("A required secret (API_KEY, EMAIL_USER, or EMAIL_PASS) is not set. Aborting.")
        return

    # Create a multipart message and set headers
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = RECIPIENT_EMAIL
    
    # Attach the HTML body
    msg.attach(MIMEText(html_body, "html"))

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
        sunset_rows_html, has_good_sunset = format_all_sunsets_html(forecast_data)
        
        if has_good_sunset:
            # Main HTML structure for the email
            full_html_email = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: sans-serif; margin: 0; padding: 0; }}
                    .container {{ padding: 20px; }}
                    .header-img {{ width: 100%; max-height: 250px; object-fit: cover; }}
                    table {{ width: 100%; border-collapse: collapse; text-align: left; }}
                    th {{ background-color: #f2f2f2; padding: 12px; }}
                </style>
            </head>
            <body>
                <img src="https://images.pexels.com/photos/5433634/pexels-photo-5433634.jpeg" alt="Beautiful Sunset" class="header-img">
                <div class="container">
                    <h2>Upcoming Sunset Forecast for New Haven</h2>
                    <p>A potentially great sunset is on the horizon! Here is the full forecast for the next few days:</p>
                    <table>
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Sunset Time</th>
                                <th>Quality</th>
                                <th>Cloud Cover</th>
                                <th>Magic Hour Window</th>
                            </tr>
                        </thead>
                        <tbody>
                            {sunset_rows_html}
                        </tbody>
                    </table>
                    <p style="font-size: 12px; color: #888; margin-top: 20px;">
                        Powered by your GitHub Sunset Notifier.
                    </p>
                </div>
            </body>
            </html>
            """
            print("Good sunset found. Preparing to send HTML email.")
            send_email_notification("🌅 Good Sunset Forecast!", full_html_email)
        else:
            print("No good sunsets predicted in the next 3 days. No email will be sent.")