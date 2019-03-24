#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simple periodical process removes unused queues."""

import sched
import time

from queue_manager import DataQueueManager

from app import app

QUEUE_PRUNE_INTERVAL = app.config.get('QUEUE_PRUNE_INTERVAL', 3)
INACTIVITY_THRESHOLD = app.config.get('INACTIVITY_THRESHOLD', 3)

queue_manager = DataQueueManager()
scheduler = sched.scheduler(time.time, time.sleep)


def prune_inactive_queues(_scheduler):
    queue_manager.prune_inactive_queues(INACTIVITY_THRESHOLD)
    _scheduler.enter(
        delay=QUEUE_PRUNE_INTERVAL,
        priority=1,
        action=prune_inactive_queues,
        argument=(_scheduler,)
    )


scheduler.enter(
    delay=QUEUE_PRUNE_INTERVAL,
    priority=1,
    action=prune_inactive_queues,
    argument=(scheduler,)
)
scheduler.run()
