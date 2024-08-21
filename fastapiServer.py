import random
import os
from typing import Iterator

import asyncio
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
import subprocess

app = FastAPI()
templates = Jinja2Templates(directory="python/templates")
random.seed()


main_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")).replace('\\', '/')

@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> templates.TemplateResponse:
    return templates.TemplateResponse("receivers.html", {"request": request})


async def generate_random_data(request: Request) -> Iterator[str]:

    # client_ip = request.client.host

    write_path = os.path.join(main_path, 'parsed_data.txt')

    while True:
        data = []
        with open(write_path, 'r') as f:
            for s in f:
                data.append(s.strip())
        yield f"data: {data}\n\n"
        await asyncio.sleep(5)


@app.get("/data")
async def receivers_data(request: Request) -> StreamingResponse:
    response = StreamingResponse(generate_random_data(request), media_type="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response


def check_service_status(service_name):
    try:
        output = subprocess.check_output(f"systemctl status {service_name}", shell=True)
        return "active" in output.decode("utf-8")
    except Exception:
        return False


@app.post("/getTopicList")
async def get_topic_list():
    response = {"topics": []}

    extract_path = os.path.join(main_path, "rnx_files")

    for filename in os.listdir(extract_path):
        filepath = os.path.join(extract_path, filename).replace('\\', '/')

        if check_service_status(filename[0:11]):
            response['topics'].append(f"thread_sim/{filename}")
