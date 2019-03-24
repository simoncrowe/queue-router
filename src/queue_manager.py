# -*- coding: utf-8 -*-
"""Defines logic for data queues."""

from collections import deque
from hashlib import sha256
import json
from redis import Redis
import random
import time
from uuid import uuid4

from util import int_factor_round


class DataQueueManager:
    """Maintains queues of data and provides access to them using addresses."""

    def __init__(self):
        self.redis = Redis()

    def register(self):
        address = str(uuid4())
        self._set_queue(address=address, queue=deque())
        self.record_access(address)
        return address

    def authenticate(self, identity, token, factor):
        """Determines whether an id and token are valid.

        Args:
            identity: the identity or address of a node requesting access.
            token: the security token used by that node.
            factor: the factor restricting time steps.

        Returns:
            bool: True if the node is authorised, otherwise false.
        """
        if self._queue_exists(address=identity):
            current_time = int(time.time())
            # Earlier/later tokens allow client time to deviate from server time
            if token in (
                    self._generate_token(
                        identity,
                        current_time + factor * i,
                        factor
                    )
                    for i in range(-1, 2)
            ):
                self.record_access(identity)
                return True

        return False

    def get_any_address(self, _id):
        """Gets a random address. Used to pair nodes for data transfer."""
        try:
            return random.choice(
                list(
                    set(self.get_all_addresses()).difference({_id})
                )
            )
        except IndexError:
            return None

    def enqueue(self, data, address=None):
        """Adds one or more items of data to one or all queues.

        Args:
            data (str): The data to be enqueued.
            address (str): The address of the queue to enqueue to.

        Returns:
            bool: False if address specified and doesn't exist, otherwise True.
        """

        if address:
            return self._enqueue_to_single_queue(
                address=address,
                data=data
            )
        else:
            self._enqueue_to_all(data)
            return True

    def _enqueue_to_single_queue(self, address, data):
        queue = self._get_queue(address)
        if queue is not None:
            queue.append(data)
            self._set_queue(address, queue)
            return True
        return False

    def _enqueue_to_all(self, data):
        for address in self.get_all_addresses():
            self._enqueue_to_single_queue(
                address=address,
                data=data,
            )

    def dequeue(self, address):
        """Removes first item from addressed queue and returns it.

        Args:
            address (str): The address of the queue.

        Returns:
            str: The first item in the queue, if found, otherwise None.
        """
        queue = self._get_queue(address)

        if queue:
            data = queue.popleft()
            self._set_queue(address, queue)
            return data

        return None

    def record_access(self, address):
        """Records an attempt to access a given address.

        Args:
            address (str): An optional queue address.
        """
        last_access_key = self._get_last_access_key(address)
        self._set_data(last_access_key, time.time())

    def prune_inactive_queues(self, inactivity_threshold):
        addresses = self.get_all_addresses()
        for address in addresses:
            last_access_key = self._get_last_access_key(address)
            last_access = self._get_data(last_access_key)
            if time.time() - last_access > inactivity_threshold:
                queue_key = self._get_queue_key(address)
                self._delete_data(last_access_key, queue_key)

    def _queue_exists(self, address):
        queue_key = self._get_queue_key(address)
        return self.redis.exists(queue_key)

    def _get_queue(self, address):
        """Gets a queue from a given address.

        Args:
            address: The address of the queue.

        Returns:
            deque: The queue object, if present.

        """
        queue_key = self._get_queue_key(address)
        data = self._get_data(queue_key)
        if data is not None:
            return deque(data)

    def _set_queue(self, address, queue):
        """Set a queue at a given key to the cache.

        Args:
            address (str): The address of the queue.
            queue (deque): The queue object.
        """
        queue_key = self._get_queue_key(address)
        self._set_data(
            key=queue_key,
            data=list(queue)
        )

    def _set_data(self, key, data):
        """Sets data to cache."""
        self.redis.set(key, json.dumps(data))

    def _get_data(self, key):
        """Gets data from cache."""
        data = self.redis.get(key)
        if data is not None:
            return json.loads(data.decode())

    def _delete_data(self, *keys):
        self.redis.delete(*keys)

    def get_all_addresses(self):
        """Gets all addresses from the cache."""
        return [
            key.replace(b'_queue', b'').decode()
            for key in self.redis.scan_iter('*_queue')
        ]

    @staticmethod
    def _generate_token(identity, seconds, base=10):
        return sha256(
            '{id}-{timestamp}'.format(
                id=identity,
                timestamp=int_factor_round(seconds, base),
            ).encode('utf-8')
        ).hexdigest()

    @staticmethod
    def _get_queue_key(address):
        return '{address}_queue'.format(address=address).encode()

    @staticmethod
    def _get_last_access_key(address):
        return '{address}_last_access'.format(address=address).encode()
