import traceback
from os import getenv

from dotenv import load_dotenv

from logging import getLogger
from logging import Handler

from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from redis import Redis

from eric_sse.interfaces import ChannelRepositoryInterface
from eric_sse.prefabs import SSEChannel
from eric_sse.servers import ChannelContainer
from eric_sse.exception import InvalidChannelException, InvalidConnectionException, ItemNotFound
from eric_sse.entities import AbstractChannel
from eric_sse.message import Message

from eric_redis_queues.repository import redis_channel_repository_builder


load_dotenv('.eric-api.env')
import logging

logging.basicConfig(
    level=logging.getLevelName(getenv('LOGLEVEL', 'INFO'))
)

logger = getLogger(__name__)
channel_container = ChannelContainer()

channel_repository: ChannelRepositoryInterface[SSEChannel] | None = None

class EricHandler(Handler):

    def __init__(self, error_dispatching_channel: AbstractChannel, level=0):
        super().__init__(level)
        self.__channel = error_dispatching_channel

    def emit(self, record):
        self.__channel.broadcast(Message(msg_type=record.levelname, msg_payload=self.format(record)))

def activate_redis():
    logger.info('Setting up redis queues')
    global channel_repository

    redis_client = Redis(
        host=getenv("REDIS_HOST", "127.0.0.1"),
        port=int(getenv("REDIS_PORT", "6379")),
        db=int(getenv("REDIS_DB", "0"))
    )

    channel_repository = redis_channel_repository_builder(SSEChannel, redis_client).build()

    for channel in channel_repository.load_all():
        channel_container.register(channel)

def new_channel(channel_id: str | None = None) -> SSEChannel:
    """Channels created through the repository get Redis backed connections, in memory ones otherwise"""
    if channel_repository is not None:
        return channel_repository.create({'channel_id': channel_id})
    return SSEChannel(channel_id=channel_id)


def activate_logging_channel(channel_id: str):
    if channel_id not in channel_container.get_all_ids():
        logging_channel = new_channel(channel_id)
        channel_container.register(logging_channel)
    else:
        logging_channel = channel_container.get(channel_id)

    logger.addHandler(EricHandler(logging_channel))
    logger.debug('logging channel activated')


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
        raise


def get_connection(channel_id: str, connection_id: str):
    try:
        selected_channel = get_channel(channel_id)
        return selected_channel.get_connection(connection_id)
    except (InvalidChannelException, InvalidConnectionException):
        if channel_repository is not None:
            # refresh channel and retry
            logger.debug(f'No connection with id {connection_id}. Reading from persistence layer')
            if channel_id in channel_container.get_all_ids():
                channel_container.rm(channel_id)
            channel_container.register(channel_repository.load_one(channel_id))
            selected_channel = get_channel(channel_id)
            return selected_channel.get_connection(connection_id)
        raise


class MessageDto(BaseModel):
    type: str
    payload: dict | list | str | int | float | None

    def to_message(self) -> Message:
        return Message(msg_type=self.type, msg_payload=self.payload)


if getenv("QUEUES_FACTORY") == "redis":
    activate_redis()

if getenv("LOGGING_CHANNEL") is not None:
    logger.info("Setting up logging channel")
    activate_logging_channel(getenv("LOGGING_CHANNEL"))

app = FastAPI()


@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.error(f"{request.url}\n{exc}\n{traceback.format_exc()}")

    return JSONResponse(
        status_code=500,
        content={"message": f"Unknown error"},
    )


@app.exception_handler(InvalidChannelException)
@app.exception_handler(InvalidConnectionException)
async def exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=400,
        content={"message": repr(exc)},
    )

@app.exception_handler(ItemNotFound)
async def exception_handler(request: Request, exc: Exception):
    logger.error(f"Item not found {exc}")
    return JSONResponse(
        status_code=404,
        content={"message": repr(exc)},
    )


@app.get("/channels")
async def get_channels(request: Request):
    """
    Returns a list of all channels ids
    """
    refresh_channels()
    return [i for i in channel_container.get_all_ids()]


@app.post("/channel/create")
async def create(channel_id: str | None = None):
    """
    Creates a new channel. Optionally, a channel id can be provided.
    """
    created_channel = new_channel(channel_id)
    channel_container.register(created_channel)

    if channel_repository is not None:
        channel_repository.persist(created_channel)
    return {"channel_id": created_channel.id}


@app.post("/subscribe")
async def subscribe(channel_id: str) -> dict[str, str]:
    """
    Channel subscription endpoint. Returns id if listener created.
    """
    my_channel = get_channel(channel_id)
    connection = my_channel.add_connection()
    if channel_repository is not None:
        channel_repository.persist(my_channel)

    # In eric-sse 3 connections are what channels address: their id is exposed as listener id for compatibility
    return {"listener_id": connection.id}


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
    get_connection(channel_id, listener_id)
    # message_stream starts the listener itself
    return EventSourceResponse(get_channel(channel_id).message_stream(listener_id))


@app.delete("/listener/{channel_id}/{listener_id}")
async def delete_listener(channel_id: str, listener_id: str):
    channel_object = get_channel(channel_id)
    channel_object.remove_connection(listener_id)
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
        result[channel_id] = [c.id for c in channel_container.get(channel_id).get_connections()]
    return result
