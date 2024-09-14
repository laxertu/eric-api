import logging

from fastapi import FastAPI
from eric.model import SSEChannel, MessageQueueListener, Message
from sse_starlette.sse import EventSourceResponse

server_channel = SSEChannel()

class ApiMessageListener(MessageQueueListener):

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
async def stream(listener_id: str):
    listener = server_channel.get_listener(listener_id)
    return EventSourceResponse(await server_channel.message_stream(listener))
