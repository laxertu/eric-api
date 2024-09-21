import sys
from concurrent.futures import ThreadPoolExecutor
import requests, time

benchmark_params = {
  "item_process_time": float(sys.argv[1]),
  "blocking_operation_time": float(sys.argv[2]),
  "fixture_size": int(sys.argv[3])
}

print("Launching with", benchmark_params)

def launch(label: str, callabe, **kwargs):
    st = time.time()
    callabe(**kwargs)
    print(f"Time {label}", time.time() - st)

with ThreadPoolExecutor(max_workers=2) as e:

    launch(callabe=requests.post, label='naive', url='http://127.0.0.1:8000/start_get', json=benchmark_params)
    launch(callabe=requests.post, label='threaded', url='http://127.0.0.1:8000/start_sse', json=benchmark_params)



