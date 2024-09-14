import logging

from fastapi import FastAPI, Request
from eric.model import SSEChannel, MessageQueueListener, Message
from sse_starlette.sse import EventSourceResponse

server_channel = SSEChannel()

class ApiMessageListener(MessageQueueListener):
    ...


app = FastAPI()

@app.post("/subscribe")
async def subscribe():
    l = ApiMessageListener()
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
    if request.is_disconnected():
        server_channel.dispatch(listener, Message(type="connection_closed"))
        await listener.stop()
    return EventSourceResponse(await server_channel.message_stream(listener))
