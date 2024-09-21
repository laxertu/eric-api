import asyncio
import time
from logging import getLogger
from typing import Any
from fastapi import FastAPI, Request
from eric.entities import Message, MessageQueueListener, AbstractChannel
from sse_starlette.sse import EventSourceResponse
from concurrent.futures import ThreadPoolExecutor

logger = getLogger(__name__)

PROCESS_TIME = 0.02
BLOCKING_OPERATION_TIME = 0.5
FIXTURE_SIZE = 1000

class BenchMarkChannel(AbstractChannel):

    def adapt(self, msg: Message) -> Any:
        return None

    def notify_end(self):
        self.broadcast(Message(type='end'))


class BenchMarkListener(MessageQueueListener):
    def __init__(self):
        super().__init__()
        self.executor = ThreadPoolExecutor(max_workers=6)

    def on_message(self, msg: Message) -> None:
        if msg.type == 'end':
            self.stop_sync()
        else:
            self.executor.submit(process_item, msg.payload)


channel = BenchMarkChannel()
listener_sse = BenchMarkListener()
channel.register_listener(listener_sse)

def create_fixture() -> list[dict]:
    return [{f'x': x} for x in range(1, 1000)]

async def do_blocking_request(response: list[dict]):
    print('doing blocking opertion')
    await asyncio.sleep(BLOCKING_OPERATION_TIME)
    print('Done')
    return response

def process_item(item: dict) -> dict:
    print('do processing')
    time.sleep(PROCESS_TIME)
    return item

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
    channel.dispatch(listener_sse.id, Message(type='end'))
    await listener_sse.start()
    # logger.info(f"wget -q -S -O - 127.0.0.1:8000/stream/{channel_id}/{listener_id} 2>&1")
    if await request.is_disconnected():
        await listener_sse.stop()

    return EventSourceResponse(await channel.message_stream(listener_sse))



