import sys
from concurrent.futures import ThreadPoolExecutor
import requests, time
def get_param(pos: int, default_value: str):
    try:
        return sys.argv[pos]
    except IndexError:
        return default_value

print("usage: python bm.py item_process_time blocking_operation_time fixture_size")
print("example: python bm.py 0.2 0.5 10")

item_process_time = get_param(1, '0.001')
blocking_operation_time = get_param(2, '0.5')
fixture_size = get_param(3, '5000')


benchmark_params = {
  "item_process_time": float(item_process_time), # Duration of item processing step
  "blocking_operation_time": float(blocking_operation_time), # Duration of blocking operation time
  "fixture_size": int(fixture_size) # Size of fixture
}

print("Launching with", benchmark_params)

def launch(label: str, callabe, **kwargs):
    st = time.time()
    callabe(**kwargs)
    print(f"Time {label}", time.time() - st)

with ThreadPoolExecutor(max_workers=2) as e:

    launch(callabe=requests.post, label='naive', url='http://127.0.0.1:8000/start_get', json=benchmark_params)
    launch(callabe=requests.post, label='threaded', url='http://127.0.0.1:8000/start_sse', json=benchmark_params)



