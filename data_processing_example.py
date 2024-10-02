import asyncio
import concurrent.futures
from logging import getLogger
from time import sleep
from fastapi import FastAPI, Request

from eric_sse.entities import MessageQueueListener
from eric_sse.prefabs import Message, DataProcessingChannel
from dataclasses import dataclass
from sse_starlette.sse import EventSourceResponse

logger = getLogger(__name__)
MAX_WORKERS = 10

@dataclass
class BenchmarkParams:
    """Put here the parameters needed to your I/O bound call"""
    item_process_time: float
    blocking_operation_time: float
    fixture_size: int


class Consumer(MessageQueueListener):
    def __init__(
            self,
            benchmark_params: BenchmarkParams,
    ):
        super().__init__()
        self.__benchmark_params = benchmark_params

    def on_message(self, msg: Message) -> None:
        if msg.type == 'test':
            logger.debug(f'Sleeping async {self.__benchmark_params.item_process_time}')
            sleep(self.__benchmark_params.item_process_time)
            process_message(msg)


def create_fixture(size: int) -> list[dict]:
    # Put here examples of what your blocking call returns if you want to do isolated performance tests
    return [{f'{x}': x} for x in range(1, size)]


async def do_blocking_request(params: BenchmarkParams, fixture_response: list[dict] | None = None) -> list[dict]:
    if fixture_response is not None:
        await asyncio.sleep(params.blocking_operation_time)
        return fixture_response
    else:
        await send_blocking_request(params)

def process_item(item: dict) -> None:
    # Replace the mocking code with your business logic
    item['processed'] = True


def process_message(message: Message):
    i = message.payload
    process_item(item=i)

async def send_blocking_request(params: BenchmarkParams):
    # replace here with your blocking call if you want to test live integration
    return await do_blocking_request(params=params, fixture_response=create_fixture(params.fixture_size))

app = FastAPI()

@app.post("/start_get")
async def get_data(params: BenchmarkParams):
    result = []
    response = await send_blocking_request(params)

    for item in response:
        logger.debug(f'Sleeping sync {params.item_process_time}')
        await asyncio.sleep(params.item_process_time)
        process_item(item)
        result.append(item)

    return result


@app.post("/start_sse")
async def stream_data(request: Request, params: BenchmarkParams):
    response = await send_blocking_request(params)

    channel = DataProcessingChannel(max_workers=1)
    e = concurrent.futures.ThreadPoolExecutor(max_workers=10)
    #listener_sse = channel.add_threaded_listener(process_message)
    listener_sse = Consumer(
        benchmark_params=params,
    )

    channel.register_listener(listener_sse)

    for m in response:
        channel.dispatch(listener_sse.id, Message(type='test', payload=m))

    await listener_sse.start()
    if await request.is_disconnected():
        await listener_sse.stop()

    return EventSourceResponse(await channel.process_queue(listener_sse))



