from logging import getLogger

from fastapi import FastAPI, Request
from eric_sse.entities import Message
from eric_sse.servers import SSEChannelContainer
from sse_starlette.sse import EventSourceResponse

logger = getLogger(__name__)

channel_container = SSEChannelContainer()

app = FastAPI()

@app.put("/create")
async def create():
    channel = channel_container.add()
    return {"channel_id": channel.id}


@app.post("/subscribe")
async def subscribe(channel_id: str):
    l = channel_container.get(channel_id).add_listener()
    return {"listener_id": l.id}

@app.post("/broadcast")
async def broadcast(channel_id: str, msg: Message):
    channel_container.get(channel_id).broadcast(msg)
    return None

@app.post("/dispatch")
async def send(channel_id: str, listener_id: str, msg: Message):
    channel_container.get(channel_id).dispatch(listener_id, msg)

@app.get("/stream/{channel_id}/{listener_id}")
async def stream(request: Request, channel_id: str, listener_id: str):
    channel = channel_container.get(channel_id)
    listener = channel.get_listener(listener_id)
    await listener.start()
    #logger.info(f"wget -q -S -O - 127.0.0.1:8000/stream/{channel_id}/{listener_id} 2>&1")
    if await request.is_disconnected():
        await listener.stop()
    return EventSourceResponse(await channel.message_stream(listener))

@app.delete("/listener/{channel_id}/{listener_id}")
async def delete_listener(channel_id: str, listener_id: str):
    channel_container.get(channel_id).remove_listener(listener_id)

@app.delete("/channel/{channel_id}")
async def delete_channel(channel_id: str):
    channel_container.rm(channel_id)
