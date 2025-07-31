import sys
from requests import get, post, put, delete

from sseclient import SSEClient

try:
    API_HOST = sys.argv[1]
except IndexError:
    API_HOST = 'http://127.0.0.1:8000'


channels = get(f'{API_HOST}/channels').json()
if len(channels) == 0:
    print("No channels found")
else:
    print("Found {} channels".format(len(channels)))
    for channel_id in channels:

        deletion_response = delete(f'{API_HOST}/channel/{channel_id}')
        assert deletion_response.status_code == 200

channels = get(f'{API_HOST}/channels').json()
assert channels == []

create_response = put(f'{API_HOST}/create').json()
assert 'channel_id' in create_response

channel_id = create_response['channel_id']

subscribe_response = post(f'{API_HOST}/subscribe?channel_id={channel_id}').json()
assert 'listener_id' in subscribe_response
listener_id = subscribe_response['listener_id']

dispatch_response = post(
    f'{API_HOST}/dispatch?channel_id={channel_id}&listener_id={listener_id}',
    json={'type': 'test', 'payload': {'a': 1}}
)

assert dispatch_response.status_code == 200

subscribe_response_2 = post(f'{API_HOST}/subscribe?channel_id={channel_id}').json()
assert 'listener_id' in subscribe_response_2
listener_id_2 = subscribe_response_2['listener_id']


broadcast_response = post(
    f'{API_HOST}/broadcast?channel_id={channel_id}',
    json={'type': 'test', 'payload': 'broadcast text'}
)
assert broadcast_response.status_code == 200

broadcast_stop_response = post(
    f'{API_HOST}/broadcast?channel_id={channel_id}',
    json={'type': 'stop', 'payload': 'stop'}
)

assert broadcast_response.status_code == 200


client = SSEClient(f'{API_HOST}/stream/{channel_id}/{listener_id}')

for m in client:
    if m.event == 'stop':
        break
    print(m.data)

print("OK")