A ready-to-use SSE messaging microservice implementation. 
Intended for internal use only (all is public here by the moment).

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

**Redis persistence support**   

Activate it by creating a .eric-api.env with the following:

    QUEUES_FACTORY=redis

Redis host is configured by  

    REDIS_HOST=[host to use]
    REDIS_PORT=[port]
    REDIS_DB=[db number]

API documentation is available at http://127.0.0.1:8000/docs by default

See correspondant uvicorn configuration https://www.uvicorn.org/deployment/#running-from-the-command-line 

Bug Tracker: https://github.com/laxertu/eric-api/issues
