import os
import subprocess
import zipfile
import requests
import sys
import gzip
import schedule
import time
import shutil
import datetime

from services import services

date = sys.argv[1]

main_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")).replace('\\', '/')

def downloading():
    if not(os.path.exists(f"{main_path}/data/{date[0:4]}")):
        os.mkdir(f"{main_path}/data/{date[0:4]}")


    file_name = f"{main_path}/data/{date[0:4]}/{date[5:]}.zip"
    link = f"https://api.simurg.space/datafiles/map_files?date={date}"

    start_byte = 0
    if os.path.exists(file_name):
        start_byte = os.path.getsize(file_name)

    headers = {"Range": f"bytes={start_byte}-"}

    with open(file_name, "ab") as f:
        print("Загрузка %s" % file_name)
        response = requests.get(link, headers=headers, stream=True)

        total_length = int(response.headers.get('content-length', 0)) - start_byte
        dl = start_byte

        if total_length:
            for data in response.iter_content(chunk_size=4096):
                dl += len(data)
                f.write(data)
                done = int(50 * dl / total_length)
                sys.stdout.write("\r[%s%s] %3.1f%%" % ('=' * done, ' ' * (50 - done), 100 * dl / total_length))
                sys.stdout.flush()

        else:
            f.write(response.content)

    print("\nЗагрузка завершена %s" % file_name)

    return True

def clean_folder(folder_name):
    for filename in os.listdir(folder_name):
        file_path = os.path.join(folder_name, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)

def daily_downloading():
    global date
    date = (datetime.datetime.strptime(date, '%Y-%m-%d') + datetime.timedelta(days=1)).strftime("%H:%M:%S")

    clean_folder(os.path.join(main_path, 'rnx_files'))

    attempt = 0
    check = False

    while attempt < 3:
        try:
            check = downloading()
        except Exception as exp:
            print(exp)
            if not(check):
                time.sleep(60)
                attempt += 1
            else:
                break

    if not(check):
        print("Сбой загрузки")
        exit()

    # Распаковка архива
    zip_path = os.path.join(main_path, "data", date[:4], date[5:] + ".zip")
    extract_path = os.path.join(main_path, "data", date[:4], date[5:])
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

    # Обработка файлов
    for filename in os.listdir(extract_path):
        filepath = os.path.join(extract_path, filename).replace('\\', '/')
        if filename.endswith(".crx.gz"):
            with gzip.open(filepath, 'rb') as f_in:
                with open(filepath[:-3], 'wb') as f_out:
                    f_out.write(f_in.read())

            filename2 = filename.replace('.gz', '')
            subprocess.run([os.path.join(main_path, "python", "CRX2RNX.exe").replace('\\', '/'),
                            os.path.join(main_path, "data", date[:4], date[5:], filename2).replace('\\', '/')])

            filename2 = filename.replace('.crx', '.rnx')

            os.rename(os.path.join(main_path, "data", date[:4], date[5:], filename2).replace('\\', '/'),
                      os.path.join(main_path, "rnx_files", filename2).replace('\\', '/'))

            services(filename2, main_path)

schedule.every().day.at("22:00").do(daily_downloading)

while True:
    schedule.run_pending()
    time.sleep(60)