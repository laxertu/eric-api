import sys

from requests import get, post, put, delete, HTTPError

from sseclient import SSEClient

try:
    API_HOST = sys.argv[1]
except IndexError:
    API_HOST = 'http://127.0.0.1:8000'

def create_channel(channel_id: str | None = None) -> str:
    create_response = post(f'{API_HOST}/channel/create', {"channel_id": channel_id}).json()
    assert 'channel_id' in create_response
    return create_response['channel_id']

def subscribe(channel_id: str):
    subscribe_response = post(f'{API_HOST}/subscribe?channel_id={channel_id}').json()
    assert 'listener_id' in subscribe_response

    return subscribe_response['listener_id']

def delete_channel(channel_id: str):
    print('deleting', channel_id)
    deletion_response = delete(f'{API_HOST}/channel/{channel_id}')
    assert deletion_response.status_code == 200

def delete_listener(channel_id, listener_id):
    response = delete(f"{API_HOST}/listener/{channel_id}/{listener_id}")
    assert response.status_code == 200

def dispatch(channel_id:str, listener_id:str, t: str, pl):
    return post(
        f'{API_HOST}/dispatch?channel_id={channel_id}&listener_id={listener_id}',
        json={'type': t, 'payload': pl}
    )


def broadcast(channel_id: str, t: str, pl):
    return post(
        f'{API_HOST}/broadcast?channel_id={channel_id}',
        json={'type': t, 'payload': pl}
    )

def do_stream(channel_id, listener_id):
    client = SSEClient(f'{API_HOST}/stream/{channel_id}/{listener_id}')

    for m in client:
        print(m.data)
        if m.event == 'stop':
            break
    print("done")

def clean():
    channels = get(f'{API_HOST}/channels').json()
    if len(channels) == 0:
        print("No channels found")
    else:
        print("Found {} channels".format(len(channels)))
        for c in channels:
            print(c)
            deletion_response = delete(f'{API_HOST}/channel/{c}')
            assert deletion_response.status_code == 200


clean()

print("create channel")

ch_id_1 = create_channel()
listener_id_1 = subscribe(ch_id_1)
listener_id_2 = subscribe(ch_id_1)
dispatch_response = dispatch(channel_id=ch_id_1, listener_id=listener_id_1, t='test', pl={'a': 1})
assert dispatch_response.status_code == 200

# Add a channel
ch_id_2 = create_channel()
listener_id_3 = subscribe(ch_id_2)

broadcast_response = broadcast(ch_id_1,'stop', 'stop')
assert broadcast_response.status_code == 200

broadcast_response = broadcast(ch_id_2,'stop', 'stop')
assert broadcast_response.status_code == 200

do_stream(ch_id_1, listener_id_1)
try:
    do_stream('fake_channel', 'fake_listener')
except HTTPError as e:
    assert e.response.status_code == 404

dispatch_response = dispatch(channel_id='fake_channel', listener_id='fake_listener', t='test', pl={'a': 1})
assert dispatch_response.status_code == 404

broadcast_response = broadcast(channel_id='fake_channel', t='test', pl={'a': 1})
assert dispatch_response.status_code == 404


channels_and_listeners = get(f'{API_HOST}/').json()

assert channels_and_listeners == {
    ch_id_1: [listener_id_1, listener_id_2],
    ch_id_2: [listener_id_3]
}

clean()

ch_id_4 = create_channel()
listener_id_4 = subscribe(ch_id_4)
delete_listener(ch_id_4, listener_id_4)
channels_and_listeners = get(f'{API_HOST}/').json()

assert channels_and_listeners == {
    ch_id_4: []
}

delete_channel(ch_id_4)

channels_and_listeners = get(f'{API_HOST}/').json()
assert channels_and_listeners == {}

print("OK")
