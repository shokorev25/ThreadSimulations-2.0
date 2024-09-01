import paho.mqtt.client as mqtt_client
import hashlib
import datetime
import sys
import systemd.daemon
import os
import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from gnss_tec import rnx

systemd.daemon.notify('READY=1')


main_path = os.path.abspath(os.path.join(os.path.dirname(__file__))).replace('\\', '/')
filename = sys.argv[1]


will_stop = False
check_fullpath = ''


def get_data():
    global check_fullpath

    data = []
    fullpath = ''

    extract_path = os.path.join(main_path, 'rnx_files')
    for file in os.listdir(extract_path):
        if filename in file:
            fullpath = os.path.join(main_path, 'rnx_files', file)
            check_fullpath = fullpath.replace('\\', '/')

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


def update_check_fullpath():
    global check_fullpath
    extract_path = os.path.join(main_path, 'rnx_files')

    for file in os.listdir(extract_path):
        if filename[0:11] in file:
            check_fullpath = os.path.join(main_path, 'rnx_files', file).replace('\\', '/')


def check_new_data():
    global check_fullpath

    extract_path = os.path.join(main_path, 'rnx_files')

    for file in os.listdir(extract_path):
        if filename[0:11] in file:
            if check_fullpath != os.path.join(main_path, 'rnx_files', file).replace('\\', '/'):
                return True
            else:
                return False

    return False


def update_data():
    global new_data
    global check_fullpath
    global will_stop
    fullpath = ''

    extract_path = os.path.join(main_path, 'rnx_files')
    for file in os.listdir(extract_path):
        if filename[0:11] in file:
            fullpath = os.path.join(main_path, 'rnx_files', file)
            check_fullpath = fullpath.replace('\\', '/')

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
        will_stop = True


def broker_setup():
    broker = "broker.emqx.io"

    time_str = str(datetime.datetime.now())
    user_id = hashlib.md5(time_str.encode()).hexdigest()

    client = mqtt_client.Client(
        mqtt_client.CallbackAPIVersion.VERSION2,
        user_id[0:12]
    )

    print("Connecting to broker", broker)
    client.connect(broker)
    client.loop()
    print("Publishing")

    return client


def round_time(dt):
    dt = dt + datetime.timedelta(seconds=2)
    round_to = 30

    seconds = (dt.second + dt.microsecond / 1000000.0)
    rounding_seconds = ((seconds + round_to - 1) // round_to) * round_to

    result = dt + datetime.timedelta(seconds=rounding_seconds - seconds)
    return result.strftime("%H:%M:%S")


def write_data(data_str, new):
    write_path = f"{main_path}/txt_files/{filename[0:11]}.txt"

    if not(os.path.exists(write_path)) or new:
        my_file = open(write_path, "w")
        my_file.write("")
        my_file.close()

    with open(write_path, 'a') as f:
        f.write(filename[0:11] + ' ' + data_str + '\n')


def publishing():
    global new_data
    parsing_current_time = -1
    current_data = new_data
    updated = False

    for text in current_data:
        if datetime.datetime.now().strftime("%H:%M:%S") == "23:59:58":
            break

        if parsing_current_time == text.split()[1] and datetime.datetime.now().strftime("%S") != "27"\
                and datetime.datetime.now().strftime("%S") != "57":
            client.publish("thread_sim/" + filename[0:11], text)
            write_data(text, False)
        else:
            wait_time = round_time(datetime.datetime.now())

            if text.split()[1] != wait_time:
                continue

            parsing_current_time = text.split()[1]

            while datetime.datetime.now().strftime("%H:%M:%S") != wait_time:
                time.sleep(0.001)

            now_hour = datetime.datetime.now().strftime("%H")
            if (now_hour == '22' or now_hour == '23') and check_new_data() and not updated:
                update_check_fullpath()
                updated = True

            if wait_time.endswith('00') and check_new_data():
                update_check_fullpath()
                return True

            client.publish("thread_sim/" + filename[0:11], text)
            write_data(text, True)

        print("message is " + text)

    return False


new_data = get_data()

if datetime.datetime.now().strftime("%H") == "23" or datetime.datetime.now().strftime("%H") == "22":
   while datetime.datetime.now().strftime("%H:%M:%S") != "23:59:35":
       time.sleep(0.001)


scheduler = BackgroundScheduler()
scheduler.add_job(update_data, trigger=CronTrigger(hour=23, minute=50))
scheduler.start()


client = broker_setup()


while not will_stop:
    if publishing():
        update_data()


exit()

