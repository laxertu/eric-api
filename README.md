A ready - to use SSE messaging API. Intended for internal use only (all is public here by the moment).

Backend relies on https://github.com/laxertu/eric

Features:
* channel subscription
* broadcasting
* message deliver to one client
* SSE compliant streaming

**data_processing_example.py** is a server intended for both showing an example of I/O bound API
and providing a sandbox to benchmark your business logic

it simulates a quite common use case:

API depends on an external resource and needs to make a blocking call to it, process the result
and return.

**mb.py** is a script that tests performance for naive implementation and the one that uses a 
Listener that relies on a pool of 6 threads. You can modify it to test different input processing strategies performance
