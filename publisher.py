import paho.mqtt.client as mqtt_client
import hashlib
import datetime
import os
import time
from gnss_tec import rnx
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

main_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")).replace('\\', '/')
filename = "ABPO00MDG_R_20230020000_01D_30S_MO.rnx"

check_fullpath = ''


def get_data():
    global check_fullpath

    data = []
    fullpath = ''

    extract_path = os.path.join(main_path, 'rnx_files')
    for file in os.listdir(extract_path):
        if filename in file:
            fullpath = os.path.join(main_path, 'rnx_files', file)
            check_fullpath = fullpath

    try:
        with open(fullpath) as obs_file:
            reader = rnx(obs_file)

            for tec in reader:
                state = '{} {}: {} {}'.format(
                    tec.timestamp,
                    tec.satellite,
                    tec.phase_tec,
                    tec.p_range_tec,
                )

                data.append(state)

        return data

    except FileNotFoundError:
        print('Файл не найден')
        exit()


def update_data():
    global new_data
    global check_fullpath
    fullpath = ''

    extract_path = os.path.join(main_path, 'rnx_files')
    for file in os.listdir(extract_path):
        if filename[0:11] in file:
            fullpath = os.path.join(main_path, 'rnx_files', file)
            check_fullpath = fullpath

    data = []
    try:
        with open(fullpath) as obs_file:
            reader = rnx(obs_file)

            for tec in reader:
                state = '{} {}: {} {}'.format(
                        tec.timestamp,
                        tec.satellite,
                        tec.phase_tec,
                        tec.p_range_tec,
                    )

                data.append(state)

        new_data = data

    except FileNotFoundError:
        print('Файл не найден')
        print('Паблишер прекратит работу')


def broker_setup():
    broker = "broker.emqx.io"

    time_str = str(datetime.datetime.now())
    user_id = hashlib.md5(time_str.encode()).hexdigest()

    client = mqtt_client.Client(
        mqtt_client.CallbackAPIVersion.VERSION2,
        user_id[0:12]
    )

    client.connect(broker)
    client.loop()

    return client


def round_time(dt):
    dt = dt + datetime.timedelta(seconds=2)
    round_to = 30

    seconds = (dt.second + dt.microsecond / 1000000.0)
    rounding_seconds = ((seconds + round_to - 1) // round_to) * round_to

    result = dt + datetime.timedelta(seconds=rounding_seconds - seconds)
    # return "23:59:30"
    return result.strftime("%H:%M:%S")


def publishing():
    global new_data
    parsing_current_time = -1
    current_data = new_data

    for text in current_data:

        if parsing_current_time == text.split()[1]:
            client.publish("info/" + filename[0:9], text)
        else:
            wait_time = round_time(datetime.datetime.now())

            if text.split()[1] != wait_time:
                continue

            parsing_current_time = text.split()[1]

            while datetime.datetime.now().strftime("%H:%M:%S") != wait_time:
                time.sleep(0.001)

            client.publish("info/" + filename[0:9], text)

        print("message is " + text)


client = broker_setup()

new_data = get_data()

if datetime.datetime.now().strftime("%H") == "23" or datetime.datetime.now().strftime("%H") == "22":
    while datetime.datetime.now().strftime("%H:%M:%S") != "23:59:35":
        time.sleep(0.001)

scheduler = BackgroundScheduler()
scheduler.add_job(update_data, trigger=CronTrigger(hour=23, minute=50))
scheduler.start()

while True:
    publishing()



