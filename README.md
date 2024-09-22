A ready-to-use SSE messaging microservice implementation. 
Intended for internal use only (all is public here by the moment).

Backend relies on https://github.com/laxertu/eric

Features:
* channel subscription
* broadcasting
* message deliver to one client
* SSE compliant streaming

**data_processing_example.py** is a server intended for both showing an example of usage of eric in case of 
having to implement some I/O bound service and providing a sandbox to benchmark your business logic in such case.

it simulates a quite common situation, in its simplest form: API depends on an external resource and needs to 
make a blocking call to it, process the result and return.

**mb.py** is a script that tests performance for naive implementation and the one that uses a 
Listener that relies on a pool of 6 threads. 

You can modify it and the server to test different input processing 
strategies performance, in both "isolated mode", by mocking blocking calls responses, or in "end to end mode", by calling to 
your code in send_blocking_request function of the server  
