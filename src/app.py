#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Provides endpoints for routing app."""

from uuid import uuid4

from flask import Flask, jsonify, Response
from webargs import fields
from webargs.flaskparser import use_kwargs

from queue_manager import DataQueueManager

app = Flask(__name__)
queue_manager = DataQueueManager()


@app.route('/register', methods=['get'])
def register():
    address = str(uuid4())
    queue_manager.register(address)
    return jsonify(
        {
            'address': address,
        }
    )


@app.route('/enqueue', methods=['post'])
@use_kwargs(
    {
        'data': fields.Str(required=True, allow_none=False),
        'address': fields.Str(missing=None),
    }
)
def enqueue(data, address):
    result = queue_manager.enqueue(data, address)
    if result:
        return Response('', status=200)
    else:
        return Response('', status=404)


@app.route('/dequeue', methods=['get'])
@use_kwargs(
    {
        'address': fields.Str(required=True, allow_none=False),
    }
)
def dequeue(address):
    result = queue_manager.dequeue(address)
    if result:
        return Response(result, status=200)
    else:
        return Response('', status=404)


if __name__ == '__main__':
    app.run()
