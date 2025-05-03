FROM python:3.11-buster

RUN pip install eric-api
RUN pip install eric-redis-queues

CMD ["uvicorn", "--host", "0.0.0.0", "eric_api:app"]

