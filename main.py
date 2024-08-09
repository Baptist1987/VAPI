from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import datetime
import os
from dotenv import load_dotenv

# Laden der Umgebungsvariablen aus der .env-Datei
load_dotenv()

# Abrufen der Konfigurationen aus der .env Datei
FLASK_RUN_PORT = int(os.getenv('FLASK_RUN_PORT', 5000))
WEBHOOK_PATH = os.getenv('WEBHOOK_PATH', '/webhook')
GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
CALENDAR_ID = os.getenv('CALENDAR_ID', 'primary')

app = Flask(__name__)

# Laden Sie die Anmeldeinformationen für die Google Calendar API
creds = Credentials.from_authorized_user_file(GOOGLE_CREDENTIALS_PATH, ['https://www.googleapis.com/auth/calendar'])
service = build('calendar', 'v3', credentials=creds)


@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    data = request.json

    # Der String enthält das Datum und die Uhrzeit, z.B. "2024-08-10T15:00:00"
    datetime_str = data.get('datetime')

    # Konvertieren Sie den String in ein datetime-Objekt
    event_datetime = datetime.datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S")
    event_endtime = event_datetime + datetime.timedelta(hours=1)  # Beispiel: Termin dauert 1 Stunde

    # Formatieren Sie die Zeit für die Google Calendar API
    start_time = event_datetime.isoformat() + 'Z'  # 'Z' zeigt an, dass die Zeit in UTC ist
    end_time = event_endtime.isoformat() + 'Z'

    # Prüfen, ob der Termin verfügbar ist
    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=start_time,
        timeMax=end_time,
        maxResults=1,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    if not events:
        # Der Termin ist frei
        return jsonify({'status': 'free', 'message': 'The time slot is free.'})
    else:
        # Der Termin ist belegt, alternative Vorschläge machen
        alternative_times = find_alternative_times(service, event_datetime, event_endtime)
        return jsonify({'status': 'occupied', 'alternatives': alternative_times})


def find_alternative_times(service, start_time, end_time):
    alternative_times = []
    # Beispiel: Suchen Sie drei Alternativen in den nächsten 3 Stunden
    for i in range(1, 4):
        new_start_time = start_time + datetime.timedelta(hours=i)
        new_end_time = end_time + datetime.timedelta(hours=i)

        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=new_start_time.isoformat() + 'Z',
            timeMax=new_end_time.isoformat() + 'Z',
            maxResults=1,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        if not events:
            alternative_times.append({
                'start_time': new_start_time.isoformat(),
                'end_time': new_end_time.isoformat()
            })

    return alternative_times


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=FLASK_RUN_PORT)
