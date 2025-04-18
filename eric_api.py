import os
import uvicorn
from logging import getLogger

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from eric_sse.entities import Message
from eric_sse.servers import SSEChannelContainer
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

logger = getLogger(__name__)
load_dotenv()

channel_container = SSEChannelContainer()

class MessageDto(BaseModel):
    type: str
    payload: dict | list | str | int | float | None

    def to_message(self) -> Message:
        return Message(msg_type=self.type, msg_payload=self.payload)

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
async def broadcast(channel_id: str, msg: MessageDto):
    channel_container.get(channel_id).broadcast(msg.to_message())
    return None

@app.post("/dispatch")
async def send(channel_id: str, listener_id: str, msg: MessageDto):
    channel_container.get(channel_id).dispatch(listener_id, msg.to_message())

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



def run():
    host = os.getenv("ERIC_API_HOST", "127.0.0.1")
    port = int(os.getenv("ERIC_API_PORT", 8000))
    log_level = os.getenv("ERIC_API_LOG_LEVEL", "info")

    uvicorn.run(app=app, host=host, port=port, log_level=log_level)
