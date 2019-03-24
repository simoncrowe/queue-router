# queue-router
Flask-based REST API for routing queued data between distributed clients.

A client hits the `/register` endpoint, and is assigned a UUID address. This address can then used to enque and dequeu data from that client's queue using the `/enqueue` and `/dequeue` endpoints. Requests to `/enque` with no address specified add the data to all active clients' queues.

This is designed to allow browser-based clients to behave somewhat like a decentralised network. This is a rather _niche_ use case. Further, while this service is designed to be simple and lightweight, it is unlikely to scale well for production use. Something like RabbitMQ may be better.
