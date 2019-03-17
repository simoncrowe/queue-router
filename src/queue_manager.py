#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Defines logic for data queues."""

from collections import deque
from datetime import datetime
from hashlib import sha256
import random
import time
from uuid import uuid4

from util import int_factor_round


class DataQueueManager:
    """Maintains queues of data and provides access to them using addresses."""

    _queues = {}
    _last_accesses = {}

    def register(self):
        address = str(uuid4())
        self._queues.setdefault(address, deque())
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
        if identity in self._queues:
            current_time = int(time.time())
            # Allow for client time to deviate somewhat from server time
            if token in (
                    self.generate_token(
                        identity,
                        current_time + factor * i,
                        factor
                    )
                    for i in range(-1, 2)
            ):
                return True

        return False

    def get_any_address(self, _id):
        """Gets a random address. Used to pair nodes for data transfer."""
        try:
            return random.choice(
                list(
                    set(self._queues.keys()).difference({_id})
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
        self.record_access(address)

        if address:
            return self._enqueue_to_single_queue(
                address=address,
                data=data
            )
        else:
            self._enqueue_to_all(data)
            return True

    def _enqueue_to_single_queue(self, data, address):
        queue = self._queues.get(address)
        if queue is not None:
            queue.append(data)
            return True
        return False

    def _enqueue_to_all(self, data):
        for queue in self._queues.values():
            queue.append(data)

    def dequeue(self, address):
        """Removes first item from addressed queue and returns it.

        Args:
            address (str): The address of the queue.

        Returns:
            str: The first item in the queue, if found, otherwise None.
        """
        self.record_access(address)

        queue = self._queues.get(address)
        if queue:
            return queue.popleft()
        return None

    def record_access(self, address=None):
        """Records an attempt to access a given address.

        Args:
            address (str): An optional queue address.
        """
        if address is None:
            for address in self._last_accesses:
                self._last_accesses[address] = datetime.now()
        else:
            self._last_accesses[address] = datetime.now()

    @staticmethod
    def generate_token(identity, seconds, base=10):
        return sha256(
            '{id}-{timestamp}'.format(
                id=identity,
                timestamp=int_factor_round(seconds, base),
            ).encode('utf-8')
        ).hexdigest()
