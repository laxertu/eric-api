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

item_process_time = get_param(1, '0.02')
blocking_operation_time = get_param(2, '0.5')
fixture_size = get_param(3, '200')


benchmark_params = {
  "item_process_time": float(item_process_time), # Duration of item processing step
  "blocking_operation_time": float(blocking_operation_time), # Duration of blocking operation time
  "fixture_size": int(fixture_size) # Size of fixture
}

print("Launching with", benchmark_params)

def launch(label: str, url: str, params: dict):
    print(f'starting {label}')
    st = time.time()
    result = requests.post(url, json=params)
    result.raise_for_status()
    print(f"Time {label}", time.time() - st)

with ThreadPoolExecutor(max_workers=2) as e:

    e.submit(launch, label='Threaded', url='http://127.0.0.1:8000/start_sse', params=benchmark_params)
    e.submit(launch, label='Naive', url='http://127.0.0.1:8000/start_get', params=benchmark_params)



