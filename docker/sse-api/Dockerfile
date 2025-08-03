FROM python:3.11
RUN pip install --upgrade pip
RUN pip install --force-reinstall eric-api
COPY .eric-api.env .
CMD ["uvicorn", "--host", "0.0.0.0", "eric_api:app"]


