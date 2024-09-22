import asyncio
import time
from logging import getLogger

from fastapi import FastAPI, Request
from eric_sse.entities import Message, DataProcessingChannel, ThreadPoolListener
from dataclasses import dataclass
from sse_starlette.sse import EventSourceResponse

logger = getLogger(__name__)
MAX_WORKERS = 6

@dataclass
class BenchmarkParams:
    item_process_time: float
    blocking_operation_time: float
    fixture_size: int


def create_fixture(size: int) -> list[dict]:
    return [{f'x': x} for x in range(1, size)]

async def do_blocking_request(time_to_wait: float, response: list[dict]):
    await asyncio.sleep(time_to_wait)
    return response

def process_item(time_to_wait: float, item: dict) -> dict:
    time.sleep(time_to_wait)
    return item


channel = DataProcessingChannel()
listener_sse = ThreadPoolListener(callback=process_item, max_workers=MAX_WORKERS)
channel.register_listener(listener_sse)

app = FastAPI()

@app.post("/start_get")
async def get_data(params: BenchmarkParams):
    response = await do_blocking_request(params.blocking_operation_time, create_fixture(params.fixture_size))
    return [process_item(params.item_process_time, x) for x in response]


@app.post("/start_sse")
async def stream_data(request: Request, params: BenchmarkParams):
    response = await do_blocking_request(params.blocking_operation_time, create_fixture(params.fixture_size))
    for m in response:
        channel.dispatch(listener_sse.id, Message(type='test', payload=m))
    channel.dispatch(listener_sse.id, Message(type='_eric_channel_closed'))
    await listener_sse.start()
    if await request.is_disconnected():
        await listener_sse.stop()

    return EventSourceResponse(await channel.message_stream(listener_sse))



