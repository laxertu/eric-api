import traceback

from logging import getLogger
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from eric_sse.entities import Message, AbstractChannel
from eric_sse.servers import SSEChannelContainer
from eric_sse.exception import InvalidChannelException, InvalidListenerException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from os import getenv
from dotenv import load_dotenv

load_dotenv('.eric-api.env')
logger = getLogger(__name__)

channel_container = SSEChannelContainer()

queues_factory = None

if getenv("QUEUES_FACTORY") == "redis":
    from eric_redis_queues import RedisQueueFactory
    queues_factory = RedisQueueFactory(
        host=getenv("REDIS_HOST", "127.0.0.1"),
        port=int(getenv("REDIS_PORT", "6379")),
        db=int(getenv("REDIS_DB", "0")),
    )


class MessageDto(BaseModel):
    type: str
    payload: dict | list | str | int | float | None

    def to_message(self) -> Message:
        return Message(msg_type=self.type, msg_payload=self.payload)

app = FastAPI()


@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.error(f"{exc}\n{traceback.format_exc()}")

    return JSONResponse(
        status_code=500,
        content={"message": f"Unknown error"},
    )


@app.exception_handler(InvalidChannelException)
@app.exception_handler(InvalidListenerException)
async def exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=400,
        content={"message": repr(exc)},
    )


@app.put("/create")
async def create():
    channel = channel_container.add(queues_factory=queues_factory)
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
    """
    Opens a connection given a channel id and a listener id.

    A bash monitor would be:

    ***wget -q -S -O - 127.0.0.1:8000/stream/{channel_id}/{listener_id} 2>&1***
    """
    channel = channel_container.get(channel_id)
    listener = channel.get_listener(listener_id)
    await listener.start()
    if await request.is_disconnected():
        await listener.stop()
    return EventSourceResponse(await channel.message_stream(listener))

@app.delete("/listener/{channel_id}/{listener_id}")
async def delete_listener(channel_id: str, listener_id: str):
    channel_container.get(channel_id).remove_listener(listener_id)


@app.get("/channels")
async def channels() -> list[str]:
    return [x for x in channel_container.get_all_ids()]


@app.delete("/channel/{channel_id}")
async def delete_channel(channel_id: str):
    channel_container.rm(channel_id)
