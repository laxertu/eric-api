A ready-to-use SSE messaging microservice implementation.

Backend documentation https://laxertu.github.io/eric/docs.html  
REST services rely on FastApi + Uvicorn

Features:
* channel subscription
* broadcasting
* message deliver to one client
* SSE compliant streaming

**Installation:**

    pip install eric-api

**Start webserver**

    uvicorn eric_api:app

**Docker stuff**

[Here](https://github.com/laxertu/eric-api/tree/master/docker) you can find a couple of prefabs for redis and api itself

Services exposed are

http://127.0.0.1:5540/ Redis Insights. Host to use when creating dbs have to be "redis", as per service definition
http://127.0.0.1:8000/docs Swagger

**Environment setup**
Configuration file is

.eric-api.env


**Logging**

Setup logging level

Activate it by setting .eric-api.env LOGLEVEL variable according to literals supported by python logger, for example:

    LOGLEVEL=DEBUG

setting LOGGING_CHANNEL to "true" activates a channel that receive broadcasts from logger used in the API. You can enable it
if you want to open a real time SSE alerting service. Default stream is _logging/_logging. It should be shown in '/' endpoint.

    LOGGING_CHANNEL=true

**Redis persistence support**   

Setup it in .eric-api.env file with the following:

    QUEUES_FACTORY=redis

Redis host is configured by  

    REDIS_HOST=[host to use]
    REDIS_PORT=[port]
    REDIS_DB=[db number]

API documentation is available at http://127.0.0.1:8000/docs by default

See correspondant uvicorn configuration https://www.uvicorn.org/deployment/#running-from-the-command-line 

Bug Tracker: https://github.com/laxertu/eric-api/issues
