import json
import sys

from redis import Redis
from requests import get, post, put, delete

from sseclient import SSEClient

try:
    API_HOST = sys.argv[1]
except IndexError:
    API_HOST = 'http://127.0.0.1:8000'

def create_channel() -> str:
    create_response = put(f'{API_HOST}/create').json()
    assert 'channel_id' in create_response
    return create_response['channel_id']

def subscribe(channel_id: str):
    subscribe_response = post(f'{API_HOST}/subscribe?channel_id={channel_id}').json()
    assert 'listener_id' in subscribe_response

    return subscribe_response['listener_id']


def dispatch(channel_id:str, listener_id:str, t: str, pl):
    dispatch_response = post(
        f'{API_HOST}/dispatch?channel_id={channel_id}&listener_id={listener_id}',
        json={'type': t, 'payload': pl}
    )
    assert dispatch_response.status_code == 200
def broadcast(channel_id: str, t: str, pl):
    broadcast_response = post(
        f'{API_HOST}/broadcast?channel_id={channel_id}',
        json={'type': t, 'payload': pl}
    )
    assert broadcast_response.status_code == 200

def do_stream(channel_id, listener_id):
    print("**streaimng**")
    client = SSEClient(f'{API_HOST}/stream/{channel_id}/{listener_id}')

    for m in client:
        if m.event == 'stop':
            break
        print(m.data)
    print("done")


r = Redis()
for x in r.scan_iter('*'):
    r.delete(x)
#exit(0)

channels = get(f'{API_HOST}/channels').json()
if len(channels) == 0:
    print("No channels found")
else:
    print("Found {} channels".format(len(channels)))
    for c in channels:
        print(c)
        deletion_response = delete(f'{API_HOST}/channel/{c}')
        assert deletion_response.status_code == 200

print("create channel")
channels = get(f'{API_HOST}/channels').json()
assert channels == []

ch_id_1 = create_channel()
listener_id_1 = subscribe(ch_id_1)
listener_id_2 = subscribe(ch_id_1)
dispatch(channel_id=ch_id_1, listener_id=listener_id_1, t='test', pl={'a': 1})

# Add a channel
ch_id_2 = create_channel()

broadcast(ch_id_1,'stop', 'stop')
broadcast(ch_id_2,'stop', 'stop')

do_stream(ch_id_1, listener_id_1)

print(json.dumps(get(f'{API_HOST}/').json(), indent=4))


#--------
print("emptying")
channels = get(f'{API_HOST}/channels').json()
if len(channels) == 0:
    print("No channels found")
else:
    print("Found {} channels".format(len(channels)))
    for ch_id in channels:
        print('deleting', ch_id)
        deletion_response = delete(f'{API_HOST}/channel/{ch_id}')
        assert deletion_response.status_code == 200


print("OK")
