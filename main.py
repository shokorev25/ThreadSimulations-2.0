import os
import requests
import sys
import zipfile
import gzip

def downloading(date, mainpath):
    file_name = f"{mainpath}/data/{date[0:4]}/{date[5:]}.zip"
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

def main(date_str):
    # mainpath = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    mainpath = "C:/Users/Admin/OneDrive/Рабочий стол/Practice"

    try:
        downloading(date_str, mainpath)
    except Exception as exp:
        print("Сбой загрузки", exp)
        exit()

    zip_path = os.path.join(mainpath, "data", date_str[:4], date_str[5:] + ".zip")
    extract_path = os.path.join(mainpath, "data", date_str[:4], date_str[5:])
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)


date = '2023-01-03'
# date = sys.argv[1]

main(date)