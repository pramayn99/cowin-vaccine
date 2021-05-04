import datetime
import os
import time

import requests
from dotenv import load_dotenv, find_dotenv
from schedule import every, run_pending
from twilio.rest import Client

# (IN MINUTES)
FREQUENCY = 5


class Vaccination:

    def __init__(self):
        self.DISTRICT_ID = int(os.environ.get("DISTRICT_ID"))
        self.MIN_AGE = int(os.environ.get("MIN_AGE"))
        self.MAX_AGE = int(os.environ.get("MAX_AGE"))
        self.NO_OF_DAYS = int(os.environ.get("NO_OF_DAYS"))
        self.TWILIO_ACCOUNT_ID = os.environ.get("TWILIO_ACCOUNT_ID")
        self.TWILIO_TOKEN = os.environ.get("TWILIO_TOKEN")
        self.URL = os.environ.get("URL")

    def send_notification(self, sessions):
        body = ''
        client = Client(self.TWILIO_ACCOUNT_ID, self.TWILIO_TOKEN)
        for session in sessions:
            body = '''
                DATE: {A},
                PLACE: {B},
                PIN_CODE: {C},
                FEE: {D},
                VACCINE_NAME: {E},
                AVAILABLE_CAPACITY: {F},
                AGE_LIMIT {G}:
            '''
            body = body.format_map({
                'A': session.get('date'),
                'B': session.get('name'),
                'C': session.get('pincode'),
                'D': session.get('fee'),
                'E': session.get('vaccine'),
                'F': session.get('available_capacity'),
                'G': session.get('min_age_limit')
            })

        client.messages.create(to="<TWILIO_REGISTERED_MOBILE_NUMBER>",
                               from_="<TWILIO_MOBILE_NUMBER>",
                               body=body)

    def process_session_data(self, session_data):
        sessions = session_data.get('sessions', [])
        filtered_sessions = [s for s in sessions if self.MIN_AGE <= s.get('min_age_limit') <= self.MAX_AGE]
        if filtered_sessions:
            self.send_notification(sessions=filtered_sessions)

    def ping_and_get_district_data(self, date):
        response = requests.get(
            f'{self.URL}{self.DISTRICT_ID}&date'
            f'={date}')
        if response.status_code == 200:
            self.process_session_data(session_data=response.json())
        else:
            print("RETRYING...")
            self.ping_and_get_district_data(date=date)

    def execute(self):
        for day_count in range(self.NO_OF_DAYS):
            str_date = f'{datetime.date.today() + datetime.timedelta(days=day_count):%d-%m-%Y}'
            self.ping_and_get_district_data(date=str_date)


def job():
    _vaccination = Vaccination()
    _vaccination.execute()


def main():
    load_dotenv(find_dotenv())
    every(FREQUENCY).minutes.do(job)
    while True:
        run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
