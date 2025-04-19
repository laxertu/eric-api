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

    uvicorn eric_api:app

API documentation is available at http://127.0.0.1:8000/docs by default (see below)

See correspondant uvicorn configuration https://www.uvicorn.org/deployment/#running-from-the-command-line 

