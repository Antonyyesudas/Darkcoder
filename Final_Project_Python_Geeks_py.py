import requests
import json
import pyttsx3
import speech_recognition as sp
import re
import threading
import time

API_KEY = "tVYtonJcOSuU"
PROJECT_TOKEN = "taeXHrT7CP8S"
RUN_TOKEN = "tb2_ss-KshOc"


class Data:
    def __init__(self, api_key, project_token):
        self.api_key = api_key
        self.project_token = project_token
        self.params = {
            "api_key": self.api_key
        }
        self.data = self.get_data()

    def get_data(self):
        response = requests.get(f'https://www.parsehub.com/api/v2/projects/{PROJECT_TOKEN}/last_ready_run/data',
                                params={"api_key": API_KEY})
        data = json.loads(response.text)
        return data

    def total_cases(self):
        data = self.data['total']

        for content in data:
            if content['name'] == "Coronavirus Cases:":
                return content['value']

    def total_deaths(self):
        data = self.data['total']

        for content in data:
            if content['name'] == "Deaths:":
                return content['value']

        return "0"

    def country_data(self, country):
        data = self.data["country"]

        for content in data:
            if content['name'].lower() == country.lower():
                return content

        return "0"

    def country_list(self):
        countries = []
        for country in self.data['country']:
            countries.append(country['name'].lower())

        return countries

    def date_update(self):
        response = requests.post(f'https://www.parsehub.com/api/v2/projects/{PROJECT_TOKEN}/last_ready_run/data',
                                 params={"api_key": API_KEY})

        def poll():
            time.sleep(0.1)
            old_data = self.data
            while True:
                new_data = self.get_data()
                if new_data != old_data:
                    self.data = new_data
                    print("Data updated")
                    break
                time.sleep(5)

        t = threading.Thread(target=poll)
        t.start()


def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    engine.save_to_file(text, 'result.mp3')


def get_audio():
    r = sp.Recognizer()
    with sp.Microphone() as source:
        audio = r.listen(source)
        said = ""

        try:
            said = r.recognize_google(audio)
        except Exception as e:
            print("Exception:", str(e))

    return said.lower()


def main():
    print("Program is running Now")
    data = Data(API_KEY, PROJECT_TOKEN)
    END_PHRASE = "stop"
    list_of_countries = data.country_list()

    TOTAL_CASES_DEATHS = {
        re.compile("[\w\s]+ total [\w\s]+ cases"): data.total_cases,
        re.compile("[\w\s]+ total cases"): data.total_cases,
        re.compile("[\w\s]+ total [\w\s]+ deaths"): data.total_deaths,
        re.compile("[\w\s]+ total deaths"): data.total_deaths
    }

    COUNTRY_CASES_DEATH = {
        re.compile("[\w\s]+ cases [\w\s]+"): lambda country: data.country_data(country)['total_cases'],
        re.compile("[\w\s]+ deaths [\w\s]+"): lambda country: data.country_data(country)['total_deaths'],
    }

    UPDATE_COMMAND = "update"

    while True:
        print("Please Speak. Listening...")
        text = get_audio()
        print(text)
        result = None

        for pattern, c_d_ans in COUNTRY_CASES_DEATH.items():
            if pattern.match(text):
                words = set(text.split(" "))
                for country in list_of_countries:
                    if country in words:
                        result = c_d_ans(country)
                        break

        for pattern, c_d_ans in TOTAL_CASES_DEATHS.items():
            if pattern.match(text):
                result = c_d_ans()
                break

        if text == UPDATE_COMMAND:
            result = "Data is being updated. This may take a moment!"
            data.date_update()

        if result:
            speak(result)


        if text.find(END_PHRASE) != -1:  # stop loop
            print("Exit")
            break


main()