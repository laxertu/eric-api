from fastapi import FastAPI, Request
from eric.model import SSEChannel, MessageQueueListener, Message
from sse_starlette.sse import EventSourceResponse


server_channel = SSEChannel()

class BroadCastListener(MessageQueueListener):

    def on_message(self, msg: Message) -> None:
        server_channel.broadcast(msg)

app = FastAPI()

@app.post("/subscribe")
async def subscribe():
    l = server_channel.add_listener(BroadCastListener)
    return {"listener_id": l.id}

@app.post("/broadcast")
async def broadcast(msg: Message):
    server_channel.broadcast(msg)
    return None

@app.post("/send_to")
async def send_to(listener_id: str, msg: Message):
    server_channel.dispatch(listener=server_channel.get_listener(listener_id), msg=msg)

@app.get("/game/stream/{session_id}/{listener_id}")
async def message_stream(listener_id: str):
    listener = server_channel.get_listener(listener_id)
    return EventSourceResponse(await server_channel.message_stream(listener))

