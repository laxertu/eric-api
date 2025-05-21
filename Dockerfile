FROM python:3.11
RUN pip install --upgrade pip
RUN mkdir /code
WORKDIR /code
COPY . /code
WORKDIR /code
RUN pip install -e .
RUN export PYTHONPATH="${PYTHONPATH}:/code"
CMD ["uvicorn", "--host", "0.0.0.0", "eric_api:app"]