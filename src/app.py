#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Provides endpoints for routing app."""

import time

from flask import Flask, jsonify, Response
from webargs import fields
from webargs.flaskparser import use_kwargs

from queue_manager import DataQueueManager
from util import int_factor_round

app = Flask(__name__)
app.config.from_pyfile('settings.cfg')
queue_manager = DataQueueManager()


@app.route('/register', methods=['get'])
def register():
    return jsonify(
        {
            'address': queue_manager.register(),
        }
    )


@app.route('/enqueue', methods=['post'])
@use_kwargs(
    {
        '_id': fields.Str(required=True, allow_none=False,),
        'token': fields.Str(required=True, allow_none=False),
        'data': fields.Str(required=True, allow_none=False),
        'address': fields.Str(missing=None),
    }
)
def enqueue(_id, token, data, address):
    authorised = queue_manager.authenticate(
        _id,
        token,
        app.config.get('SECS_FACTOR')
    )
    if authorised:
        result = queue_manager.enqueue(data, address)

        if result:
            return Response('', status=200)
        else:
            return Response('', status=404)

    return Response('', status=401)


@app.route('/dequeue', methods=['get'])
@use_kwargs(
    {
        '_id': fields.Str(required=True, allow_none=False),
        'token': fields.Str(required=True, allow_none=False),
    }
)
def dequeue(_id, token):
    authorised = queue_manager.authenticate(
        _id,
        token,
        app.config.get('SECS_FACTOR')
    )
    if authorised:
        result = queue_manager.dequeue(_id)

        if result:
            return Response(result, status=200)
        else:
            return Response('', status=404)

    return Response('', status=401)


@app.route('/secs', methods=['get'])
def get_secs():
    return Response(
        str(int_factor_round(time.time(), app.config.get('SECS_FACTOR'))),
        status=200
    )


if __name__ == '__main__':
    app.run()
