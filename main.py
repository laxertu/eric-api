from fastapi import FastAPI, Request
from eric.model import MessageQueueListener, Message
from eric.servers import ChannelContainer
from sse_starlette.sse import EventSourceResponse

channel_container = ChannelContainer()

app = FastAPI()

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
    if request.is_disconnected():
        channel.dispatch(listener, Message(type="connection_closed"))
        await listener.stop()
    return EventSourceResponse(await channel.message_stream(listener))
