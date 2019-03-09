#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick and dirty "unit" tests for API. Too long but do the job."""

from multiprocessing import Process
import unittest
import uuid
import time

import requests

from app import app, queue_manager
from util import int_factor_round


class CallLocalApiTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_server = Process(target=app.run)
        cls.test_server.start()
        # Wait for the test server to start
        time.sleep(1)
        cls.registered_addresses = [
            requests.get(
                'http://127.0.0.1:5000/register'
            ).json()['address']
            for i in range(10)
        ]
        cls.registered_address = requests.get(
            'http://127.0.0.1:5000/register'
        ).json()['address']

        # registered_id is used as an id when authenticating
        cls.registered_id = requests.get(
            'http://127.0.0.1:5000/register'
        ).json()['address']

    @classmethod
    def tearDownClass(cls):
        cls.test_server.terminate()
        cls.test_server.join()

    def test_register(self):
        response = requests.get('http://127.0.0.1:5000/register')
        self.assertEqual(
            response.status_code,
            200,
            'Request to \'/register\' returns non-OKAY status code.'
        )
        self.assertIn(
            'address',
            response.json(),
            '\'address\' key not in response JSON of \'register\' endpoint.'
        )
        address_is_uuid = True
        try:
            uuid.UUID(response.json().get('address'), version=4)
        except:
            address_is_uuid = False
        self.assertTrue(
            address_is_uuid,
            'Value of \'address\' in response from \'register\' endpoint '
            'is not a valid version 4 UUID.'
        )

    def test_enqueue_broadcast(self):
        request_args = self.get_authentication_args(self.registered_id)
        request_args['data'] = '["spam", "spam", "spam"]'
        response = requests.post(
            'http://127.0.0.1:5000/enqueue',
            data=request_args
        )
        self.assertEqual(
            response.status_code,
            200,
            'Request to \'/enqueue\' returns non-OKAY status code.'
        )
        for address in self.registered_addresses:
            response = requests.get(
                'http://127.0.0.1:5000/dequeue?_id={_id}&token={token}'.format(
                    **self.get_authentication_args(address)
                )
            )
            self.assertEqual(
                response.status_code,
                200,
                'Request to \'/dequeue\' returns non-OKAY status code.'
            )
            self.assertEqual(
                response.content,
                '["spam", "spam", "spam"]'.encode(),
                'Broadcast-dequeued data is not equal to enqueued data.'
            )

    def test_enqueue_addressed(self):
        request_args = self.get_authentication_args(self.registered_id)
        request_args.update(
            {
                'data': '["spam", "spam", "spam"]',
                'address': self.registered_address,
            }
        )
        response = requests.post(
            'http://127.0.0.1:5000/enqueue',
            data=request_args
        )
        self.assertEqual(
            response.status_code,
            200,
            'Request to \'/enqueue\' returns non-OKAY status code.'
        )
        response = requests.get(
            'http://127.0.0.1:5000/dequeue?_id={_id}&token={token}'.format(
                **self.get_authentication_args(self.registered_address)
            )
        )
        self.assertEqual(
            response.status_code,
            200,
            'Request to \'/dequeue\' returns non-OKAY status code.'
        )
        self.assertEqual(
            response.content,
            '["spam", "spam", "spam"]'.encode(),
            'Broadcast-dequeued data is not equal to enqueued data.'
        )

    def test_secs(self):
        response = requests.get('http://127.0.0.1:5000/secs')
        self.assertEqual(
            response.status_code,
            200,
            'Request to \'/secs\' returns non-OKAY status code.'
        )
        self.assertEqual(
            response.content.decode(),
            str(int_factor_round(time.time(), app.config['SECS_FACTOR'])),
            '\'secs\' returned incorrect "factor-truncated" epoch time.'
        )

    @staticmethod
    def get_authentication_args(_id):
        return {
            '_id': _id,
            'token': queue_manager.generate_token(
                _id,
                int(time.time()),
                app.config.get('SECS_FACTOR')
            )
        }


if __name__ == '__main__':
    unittest.main()