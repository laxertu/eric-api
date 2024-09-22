import asyncio
import time
from logging import getLogger

from fastapi import FastAPI, Request
from eric_sse.prefabs import Message, DataProcessingChannel, ThreadPoolListener
from dataclasses import dataclass
from sse_starlette.sse import EventSourceResponse

logger = getLogger(__name__)
MAX_WORKERS = 6

@dataclass
class BenchmarkParams:
    """Put here the parameters needed to your I/O bound call"""
    item_process_time: float
    blocking_operation_time: float
    fixture_size: int


def create_fixture(size: int) -> list[dict]:
    # Put here examples of what your blocking call returns if you want to do isolated performance tests
    return [{f'x': x} for x in range(1, size)]


async def do_blocking_request(params: BenchmarkParams, fixture_response: list[dict] | None = None) -> list[dict]:
    if fixture_response is not None:
        await asyncio.sleep(params.blocking_operation_time)
        return fixture_response
    else:
        await send_blocking_request(params)

def process_item(time_to_wait: float, item: dict) -> dict:
    # Replace the mocking code with your business logic
    time.sleep(time_to_wait)
    return item


async def send_blocking_request(params: BenchmarkParams):
    # replace here with your blocking call if you want to test live integration
    return await do_blocking_request(params=params, fixture_response=create_fixture(params.fixture_size))

app = FastAPI()

@app.post("/start_get")
async def get_data(params: BenchmarkParams):
    response = await send_blocking_request(params)

    return [process_item(params.item_process_time, x) for x in response]


@app.post("/start_sse")
async def stream_data(request: Request, params: BenchmarkParams):
    response = await send_blocking_request(params)

    listener_sse = ThreadPoolListener(callback=process_item, max_workers=MAX_WORKERS)
    channel = DataProcessingChannel()
    channel.register_listener(listener_sse)

    for m in response:
        channel.dispatch(listener_sse.id, Message(type='test', payload=m))

    channel.dispatch(listener_sse.id, Message(type='_eric_channel_closed'))
    await listener_sse.start()
    if await request.is_disconnected():
        await listener_sse.stop()

    return EventSourceResponse(await channel.message_stream(listener_sse))



