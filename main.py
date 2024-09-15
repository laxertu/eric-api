from logging import getLogger

from fastapi import FastAPI, Request
from eric.entities import MessageQueueListener, Message
from eric.servers import ChannelContainer
from sse_starlette.sse import EventSourceResponse

logger = getLogger(__name__)

channel_container = ChannelContainer()

app = FastAPI()

@app.put("/create")
async def create():
    channel = channel_container.add()
    return {"channel_id": channel.id}


@app.post("/subscribe")
async def subscribe(channel_id: str):
    channel_container.get(channel_id).add_listener(MessageQueueListener)
    l = channel_container.get(channel_id).add_listener(MessageQueueListener)
    return {"listener_id": l.id}

@app.post("/broadcast")
async def broadcast(channel_id: str, msg: Message):
    channel_container.get(channel_id).broadcast(msg)
    return None

@app.post("/dispatch")
async def send(channel_id: str, listener_id: str, msg: Message):
    channel = channel_container.get(channel_id)
    channel.dispatch(listener=channel.get_listener(listener_id), msg=msg)

@app.get("/stream/{channel_id}/{listener_id}")
async def stream(request: Request, channel_id: str, listener_id: str):
    channel = channel_container.get(channel_id)
    listener = channel.get_listener(listener_id)
    await listener.start()
    #logger.info(f"wget -q -S -O - 127.0.0.1:8000/stream/{channel_id}/{listener_id} 2>&1")
    if await request.is_disconnected():
        await listener.stop()
    return EventSourceResponse(await channel.message_stream(listener))
