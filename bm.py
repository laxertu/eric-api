import requests, time

st = time.time()
x = requests.get('http://127.0.0.1:8000/start_get')
print(time.time() - st)


st = time.time()
x = requests.get('http://127.0.0.1:8000/start_sse')
print(time.time() - st)


