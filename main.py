import logging

from fastapi import FastAPI, Request
from eric.model import SSEChannel, MessageQueueListener, Message
from sse_starlette.sse import EventSourceResponse

server_channel = SSEChannel()

class ApiMessageListener(MessageQueueListener):

    def __init__(self, request: Request):

        super().__init__()
        self.__request = request

    async def is_running(self) -> bool:
        if await self.__request.is_disconnected():
            return False
        else:
            return await super().is_running()

    def on_message(self, msg: Message) -> None:
        logging.info("Message received")

app = FastAPI()

@app.post("/subscribe")
async def subscribe():
    l = server_channel.add_listener(ApiMessageListener)
    return {"listener_id": l.id}

@app.post("/broadcast")
async def broadcast(msg: Message):
    server_channel.broadcast(msg)
    return None

@app.post("/dispatch")
async def send(listener_id: str, msg: Message):
    server_channel.dispatch(listener=server_channel.get_listener(listener_id), msg=msg)

@app.get("/stream/{listener_id}")
async def stream(request: Request, listener_id: str):
    listener = server_channel.get_listener(listener_id)
    return EventSourceResponse(await server_channel.message_stream(listener))
