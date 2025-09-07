import traceback
from os import getenv

from dotenv import load_dotenv
from logging import getLogger

from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from eric_sse.entities import Message
from eric_sse.prefabs import SSEChannel
from eric_sse.servers import ChannelContainer
from eric_sse.exception import InvalidChannelException, InvalidListenerException, ItemNotFound, RepositoryError

from eric_redis_queues import RedisConnection
from eric_redis_queues.repository import RedisSSEChannelRepository, RedisConnectionFactory, RedisConnectionRepository


load_dotenv('.eric-api.env')
logger = getLogger('uvicorn.error')
channel_container = ChannelContainer()

queues_factory = None
channel_repository = None
if getenv("QUEUES_FACTORY") == "redis":
    logger.info('Setting up redis queues')

    redis_connection = RedisConnection(
        host=getenv("REDIS_HOST", "127.0.0.1"),
        port=int(getenv("REDIS_PORT", "6379")),
        db=int(getenv("REDIS_DB", "0"))
    )

    connection_factory = RedisConnectionFactory(redis_connection=redis_connection)
    queues_factory = RedisConnectionRepository(redis_connection=redis_connection)
    channel_repository = RedisSSEChannelRepository(redis_connection=redis_connection)

    for channel in channel_repository.load_all():
        channel_container.register(channel)


# Below functions are to allow external updates to Redis db (other clients) are detected y handled
def refresh_channels():
    if channel_repository is not None:
        registered_ids = set(channel_container.get_all_ids())
        for persisted_channel in channel_repository.load_all():
            if persisted_channel.id not in registered_ids:
                channel_container.register(persisted_channel)


def get_channel(channel_id: str):
    try:
        return channel_container.get(channel_id)
    except InvalidChannelException:
        if channel_repository is not None:
            logger.debug(f'No channel found with id {channel_id}. Reading from persistence layer')
            fetched_channel = channel_repository.load_one(channel_id)
            channel_container.register(fetched_channel)
            return channel_container.get(channel_id)


def get_listener(channel_id: str, listener_id: str):
    try:
        selected_channel = get_channel(channel_id)
        return selected_channel.get_listener(listener_id)
    except (InvalidChannelException, InvalidListenerException):
        if channel_repository is not None:
            # refresh channel and retry
            logger.debug(f'No listener with id {listener_id}. Reading from persistence layer')
            channel_container.register(channel_repository.load_one(channel_id))
            selected_channel = get_channel(channel_id)
            return selected_channel.get_listener(listener_id)


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

@app.exception_handler(ItemNotFound)
async def exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=404,
        content={"message": repr(exc)},
    )


@app.get("/channels")
async def get_channels(request: Request):
    refresh_channels()
    return [i for i in channel_container.get_all_ids()]


@app.put("/create")
async def create():
    new_channel = SSEChannel(connections_factory=connection_factory)
    channel_container.register(new_channel)

    if channel_repository is not None:
        channel_repository.persist(new_channel)
    return {"channel_id": new_channel.id}


@app.post("/subscribe")
async def subscribe(channel_id: str):
    my_channel = get_channel(channel_id)
    l = my_channel.add_listener()
    if channel_repository is not None:
        channel_repository.persist(my_channel)

    return {"listener_id": l.id}


@app.post("/broadcast")
async def broadcast(channel_id: str, msg: MessageDto):
    get_channel(channel_id).broadcast(msg.to_message())
    return None


@app.post("/dispatch")
async def send(channel_id: str, listener_id: str, msg: MessageDto):
    get_channel(channel_id).dispatch(listener_id, msg.to_message())


@app.get("/stream/{channel_id}/{listener_id}")
async def stream(request: Request, channel_id: str, listener_id: str):
    """
    Opens a connection given a channel id and a listener id.

    A bash monitor would be:

    ***wget -q -S -O - 127.0.0.1:8000/stream/{channel_id}/{listener_id} 2>&1***
    """
    listener = get_listener(channel_id, listener_id)
    listener.start()
    if await request.is_disconnected():
        listener.stop()
    return EventSourceResponse(get_channel(channel_id).message_stream(listener))


@app.delete("/listener/{channel_id}/{listener_id}")
async def delete_listener(channel_id: str, listener_id: str):
    channel_object = get_channel(channel_id)
    channel_object.remove_listener(listener_id)
    if channel_repository is not None:
        channel_repository.persist(channel_object)


@app.get("/channels")
async def channels() -> list[str]:
    return [x for x in channel_container.get_all_ids()]


@app.delete("/channel/{channel_id}")
async def delete_channel(channel_id: str):
    if channel_repository is not None:
        channel_repository.delete(channel_id)
    channel_container.rm(channel_id)


@app.get("/")
async def root():
    refresh_channels()
    result = {}
    for channel_id in channel_container.get_all_ids():
        result[channel_id] = [c.listener.id for c in channel_container.get(channel_id).get_connections()]
    return result
