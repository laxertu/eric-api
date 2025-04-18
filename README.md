A ready-to-use SSE messaging microservice implementation. 
Intended for internal use only (all is public here by the moment).

Backend relies on https://github.com/laxertu/eric  
REST services rely on FastApi + Uvicorn

Features:
* channel subscription
* broadcasting
* message deliver to one client
* SSE compliant streaming

Installation:

    pip install eric-api

Start webserver

    start-ws

Some configuration is allowed by the following environment variables.
You can set them in a .env file:

    ERIC_API_HOST
    ERIC_API_PORT
    ERIC_API_LOG_LEVEL

See correspondant uvicorn configuration https://www.uvicorn.org/deployment/#running-from-the-command-line for ERIC_API_LOG_LEVEL 

