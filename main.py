from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import datetime

app = Flask(__name__)

# Hier sollten Sie Ihre Google Calendar API-Anmeldeinformationen bereitstellen
# Diese können in einer JSON-Datei gespeichert sein, die Sie von der Google Developer Console erhalten haben
creds = Credentials.from_authorized_user_file('credentials.json', ['https://www.googleapis.com/auth/calendar'])

service = build('calendar', 'v3', credentials=creds)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json

    # Extrahieren Sie das Datum und die Uhrzeit aus dem übermittelten String
    start_time_str = data.get('start_time')
    end_time_str = data.get('end_time')

    # Konvertieren Sie die Strings in datetime-Objekte
    start_time = datetime.datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M:%S")
    end_time = datetime.datetime.strptime(end_time_str, "%Y-%m-%dT%H:%M:%S")

    # Überprüfen Sie, ob der Termin frei ist
    events_result = service.events().list(calendarId='primary', timeMin=start_time.isoformat() + 'Z',
                                          timeMax=end_time.isoformat() + 'Z',
                                          maxResults=1, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        return jsonify({'status': 'free', 'message': 'The time slot is free.'})

    # Wenn der Termin belegt ist, alternative Termine vorschlagen
    alternative_times = find_alternative_times(service, start_time, end_time)

    return jsonify({'status': 'occupied', 'alternatives': alternative_times})

def find_alternative_times(service, start_time, end_time):
    alternative_times = []
    # Sie können hier z.B. drei Alternativen in der nächsten Stunde suchen
    for i in range(1, 4):
        new_start_time = start_time + datetime.timedelta(hours=i)
        new_end_time = end_time + datetime.timedelta(hours=i)

        events_result = service.events().list(calendarId='primary', timeMin=new_start_time.isoformat() + 'Z',
                                              timeMax=new_end_time.isoformat() + 'Z',
                                              maxResults=1, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            alternative_times.append({
                'start_time': new_start_time.isoformat(),
                'end_time': new_end_time.isoformat()
            })

    return alternative_times

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
