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

Results of some execution in my laptop, 6 workers

**Better performance use cases**

Quite low processing time 20.000 items
```
python bm.py 0.001 0.5 20000

Time Threaded 5.832854270935059
Time Naive 29.387115001678467
```

High processing time, only 200 items

```
python bm.py 0.1 0.5 200

Time Threaded 3.9334359169006348
Time Naive 23.868850708007812
```

**Same performance, so better choice is naive's simplicity**

Super-low processing time. 20.000 items

```
python bm.py 0.00001 0.5 20000 

Time Threaded 2.602198600769043
Time Naive 2.9316182136535645
``` 

Quite low processing time. 20 itema
```
python bm.py 0.001 0.5 20

Time Threaded 0.5315909385681152
Time Naive 0.5514707565307617
```

