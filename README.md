A ready - to use SSE messaging API. Intended for internal use only (all is public here by the moment)

Features:
* channel subscription
* broadcasting
* message deliver to one client
* SSE compliant streaming

**benchmark_main.py** is a server intended for benchmarking, it simulates a quite common use case:

API depends on an external resource and needs to maka a blocking call to it, process the result
and return.

The use case consists of 1000 dictionaries returned by a blocking call that 
adds a delay of 0.5 seconds, processing time of each of them is 0.02 seconds.

**mb.py** is a script that tests performance for naive implementation and the one that uses a 
Listener that relies on a pool of 6 threads

the results on my local machine are

naive    20.63297963142395

threaded 0.6210811138153076
