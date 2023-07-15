import tkinter as tk
from tkinter import END, INSERT, OptionMenu, StringVar
from math import floor
from google.oauth2 import service_account
from googleapiclient.discovery import build
import itertools
import time

    
def format_time(milli):
    milliseconds = "{:03}".format(milli % 1000)
    seconds = "{:02}".format(floor((milli / 1000) % 60))
    minutes = "{:02}".format(floor((milli / (60 * 1000)) % 60))

    return (minutes + ":" + seconds + "." + milliseconds)[:-1]

def stopwatch_label(label):
    start_time = time.time()
    def count():
        if running:
            global counter
            counter = round(((time.time() - start_time) * 1000))
            display = format_time(counter)

            label['text'] = display
            label.after(1, count)
    
    count()


def start(event=None):
    global running
    running = True
    stopwatch_label(stopwatch)
    start_button['state'] = 'disabled'
    lap_button['state'] = 'normal'
    stop_button['state'] = 'normal'
    reset_button['state'] = 'normal'


def lap(event=None):
    global lap_count
    global lap_times

    lap_time = format_time(counter)
    lap_times.append(lap_time)

    lap_text['state'] = 'normal'
    lap_text.insert(INSERT, f"Lap {lap_count}: {lap_time}\n")
    lap_text['state'] = 'disabled'

    lap_count += 1


def stop(event=None):
    global running

    start_button['state'] = 'normal'
    stop_button['state'] = 'disabled'
    lap_button['state'] = 'normal'
    reset_button['state'] = 'normal'

    running = False


def reset(event=None):
    global counter
    global lap_times
    global lap_count
    
    counter = 0
    lap_times.clear()
    lap_count = 1
    if not running:
        stopwatch['text'] = "00:00:00"

    lap_text['state'] = 'normal'
    lap_text.delete('1.0', END)
    lap_text['state'] = 'disabled'


def record_laps():
    try:
        if len(lap_times) != 0:
            sheet.values().update(
                spreadsheetId=SPREADSHEET_ID, range=f"{variable.get()}!E2", 
                valueInputOption="USER_ENTERED", 
                body={"values": [[lap_time] for lap_time in lap_times]}
            ).execute()
    except:
        print("Something went wrong with the Google Sheets API")


def score_teams():
    request = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        majorDimension="ROWS",
        range=f"{variable.get()}!E2:E",  
    ).execute()

    num_runners = len(list(filter(lambda time: time and time != ['-'], request['values']))) + 2

    value_ranges = [f"{variable.get()}!C{count}:E{count}" for count in range(2, num_runners)]

    request = sheet.values().batchGet(
        spreadsheetId=SPREADSHEET_ID,
        majorDimension="ROWS",
        ranges=value_ranges,  
    ).execute()

    runners = sorted([value_range['values'][0] for value_range in request['valueRanges']], key=lambda i: i[2])
    schools = dict.fromkeys((runner[1] for runner in runners), [])
    school_scores = schools.copy()

    for school in schools:
        schools.update({school: [runner for runner in runners if runner[1] == school][:7]})

    scoring_runners = sorted(list(itertools.chain.from_iterable(schools.values())), key=lambda i: i[2])

    for school in school_scores:
        school_scores.update({school: sum(list(scoring_runners.index(runner) + 1 for runner in schools[school][:5]))})

    request = sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{variable.get()}!G2",
        valueInputOption="USER_ENTERED",
        body={"values": list(map(list, school_scores.items()))}
    ).execute()


SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = "1xPgavG3krTLCmbpi8MRtXrMGzhrsUNqBSEzM9048JtI"
OPTIONS = [
    "Middle School",
    "Freshman",
    "JV",
    "Varsity",
]

creds = service_account.Credentials.from_service_account_file(
    "cross-country-362118-7d3622f60f88.json", scopes=SCOPES)

try:
  service = build('sheets', 'v4', credentials=creds)
except:
  DISCOVERY_SERVICE_URL = 'https://sheets.googleapis.com/$discovery/rest?version=v4'
  service = build('sheets', 'v4', credentials=creds, discoveryServiceUrl=DISCOVERY_SERVICE_URL)

sheet = service.spreadsheets()

running = False
counter = 0
lap_count = 1
lap_times = []

root = tk.Tk()
root.iconbitmap("sj.ico")
root.geometry("480x360")
root.title("Stopwatch")

root.bind('o', start)
root.bind('l', lap)
root.bind('p', stop)
root.bind('[', reset)

stopwatch = tk.Label(root, text="00:00:00", font="Roboto 30")
stopwatch.pack()

button_frame = tk.Frame(root)
button_frame.pack()

button_frame1=tk.Frame(root)
button_frame1.pack()

lap_text = tk.Text(root, state='disabled')
lap_text.pack()

start_button = tk.Button(button_frame, text='Start', command=start)
lap_button = tk.Button(button_frame, text='Lap', command=lap)
stop_button = tk.Button(button_frame, text="Stop", command=stop)
reset_button = tk.Button(button_frame, text="Reset", command=reset)
sheets_button = tk.Button(button_frame1, text="Send to Google Sheets", command=record_laps)
score_button = tk.Button(button_frame1, text="Score Teams", command=score_teams)

variable = StringVar(button_frame1)
variable.set(OPTIONS[2])
team_selector = OptionMenu(button_frame1, variable, *OPTIONS)

button_frame.pack(anchor='center', pady=3)
button_frame1.pack(anchor='center')

start_button.pack(side='left')
lap_button.pack(side='left')
stop_button.pack(side='left')
reset_button.pack(side='left')
team_selector.pack(side='left')
sheets_button.pack(side='left')
score_button.pack(side='left')

root.mainloop()
