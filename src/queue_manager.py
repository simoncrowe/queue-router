#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Defines logic for data queues."""

from collections import deque
from datetime import datetime


class DataQueueManager:
    """Maintains queues of data and provides access to them using addresses."""

    _queues = {}
    _last_accesses = {}

    def register(self, address):
        self._queues.setdefault(address, deque())
        self.record_access(address)

    def enqueue(self, data, address=None):
        """Adds one or more items of data to one or all queues.

        Args:
            data (str): The data to be enqueued.
            address (str): The address of the queue to enqueue to.

        Returns:
            bool: False if address specified and doesn't exist, otherwise True.
        """
        self.record_access(address)

        queue = self._queues.get(address)
        if queue is not None:
            queue.append(data)
            return True
        else:
            return False

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
