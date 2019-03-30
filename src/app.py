#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Provides endpoints for routing app."""

import time

from flask import Flask, jsonify, Response
from flask_cors import CORS
from webargs import fields
from webargs.flaskparser import use_kwargs

from queue_manager import DataQueueManager

app = Flask(__name__)
# TODO: implement narrower CORS headers
CORS(app)
app.config.from_pyfile('settings.cfg')

queue_manager = DataQueueManager()


@app.route('/register', methods=['get'])
def register():
    identity, epoch = queue_manager.register()
    return jsonify(
        {
            'identity': identity,
            'epoch': epoch,
        }
    )


@app.route('/pair', methods=['get'])
@use_kwargs(
    {
        'identity': fields.Str(required=True, allow_none=False,),
        'token': fields.Str(required=True, allow_none=False),
    }
)
def pair(identity, token):
    if queue_manager.authenticate(
        identity,
        token,
    ):
        address = queue_manager.get_any_address(identity)
        if address:
            return jsonify(
                {'address': address}
            )
        else:
            return Response('', status=404)

    return Response('', status=401)


@app.route('/enqueue', methods=['post'])
@use_kwargs(
    {
        'identity': fields.Str(required=True, allow_none=False,),
        'token': fields.Str(required=True, allow_none=False),
        'data': fields.Str(required=True, allow_none=False),
        'address': fields.Str(missing=None),
    }
)
def enqueue(identity, token, data, address):
    if queue_manager.authenticate(identity, token):
        result = queue_manager.enqueue(
            data,
            sender_id=identity,
            address=address
        )

        if result:
            return Response('', status=200)
        else:
            return Response('', status=404)

    return Response('', status=401)


@app.route('/dequeue', methods=['get'])
@use_kwargs(
    {
        'identity': fields.Str(required=True, allow_none=False),
        'token': fields.Str(required=True, allow_none=False),
    }
)
def dequeue(identity, token):
    if queue_manager.authenticate(identity, token):
        result = queue_manager.dequeue(identity)

        if result:
            return Response(result, status=200)
        else:
            return Response('', status=404)

    return Response('', status=401)


@app.route('/traffic', methods=['get'])
@use_kwargs(
    {
        'token': fields.Str(required=True, allow_none=False),
    }
)
def traffic(token):
    if token == app.config.get('VISUALISER_TOKEN'):
        return jsonify(queue_manager.get_traffic())

    return Response('', status=401)


@app.route('/time', methods=['get'])
@use_kwargs(
    {
        'token': fields.Str(required=True, allow_none=False),
    }
)
def get_time(token):
    if token == app.config.get('VISUALISER_TOKEN'):
        return Response(
            str(time.time()),
            status=200
        )

    return Response('', status=401)


if __name__ == '__main__':
    app.run()
