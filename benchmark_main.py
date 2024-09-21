import asyncio
import time
from logging import getLogger

from fastapi import FastAPI, Request
from eric.entities import Message, DataProcessingChannel, ThreadPoolListener
from sse_starlette.sse import EventSourceResponse

logger = getLogger(__name__)

PROCESS_TIME = 0.02
BLOCKING_OPERATION_TIME = 0.5
FIXTURE_SIZE = 1000
MAX_WORKERS = 6


def create_fixture() -> list[dict]:
    return [{f'x': x} for x in range(1, FIXTURE_SIZE)]

async def do_blocking_request(response: list[dict]):
    print('doing blocking opertion')
    await asyncio.sleep(BLOCKING_OPERATION_TIME)
    print('Done')
    return response

def process_item(item: dict) -> dict:
    print('do processing')
    time.sleep(PROCESS_TIME)
    return item


channel = DataProcessingChannel()
listener_sse = ThreadPoolListener(callback=process_item, max_workers=MAX_WORKERS)
channel.register_listener(listener_sse)

app = FastAPI()

@app.get("/start_get")
async def create():
    response = await do_blocking_request(create_fixture())
    return [process_item(x) for x in response]


@app.get("/start_sse")
async def stream(request: Request):
    response = await do_blocking_request(create_fixture())
    for m in response:
        channel.dispatch(listener_sse.id, Message(type='test', payload=m))
    channel.dispatch(listener_sse.id, Message(type='_eric_channel_closed'))
    await listener_sse.start()
    # logger.info(f"wget -q -S -O - 127.0.0.1:8000/stream/{channel_id}/{listener_id} 2>&1")
    if await request.is_disconnected():
        await listener_sse.stop()

    return EventSourceResponse(await channel.message_stream(listener_sse))



