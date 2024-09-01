import random
import os
from typing import Iterator

import asyncio
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
import subprocess
import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")
random.seed()


main_path = os.path.abspath(os.path.join(os.path.dirname(__file__))).replace('\\', '/')

@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> templates.TemplateResponse:
    return templates.TemplateResponse("receivers.html", {"request": request})


async def generate_data(request: Request) -> Iterator[str]:
    while True:
        data = []
        extract_path = os.path.join(main_path, "txt_files")

        for filename in os.listdir(extract_path):
            filepath = os.path.join(extract_path, filename).replace('\\', '/')

            with open(filepath, 'r') as f:
                for s in f:
                    data.append(s.strip())

        while datetime.datetime.now().strftime("%S") != "45" and datetime.datetime.now().strftime("%S") != "15":
            await asyncio.sleep(0.001)

        yield f"data: {data}\n\n"


@app.get("/data")
async def receivers_data(request: Request) -> StreamingResponse:
    response = StreamingResponse(generate_data(request), media_type="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response


def find_services(substring):
    process = subprocess.run(['systemctl', 'list-units', '--type=service', '--state=active'], capture_output=True, text=True)
    services = process.stdout.splitlines()

    filtered_services = [service for service in services if substring in service]

    return filtered_services


@app.get("/getTopicList")
async def get_topic_list():
    response = {"topics": []}

    active_publisher_services = find_services('_publisher')

    for service in active_publisher_services:
        response['topics'].append(f"thread_sim/{service.split()[0][0:11]}")

    return response
