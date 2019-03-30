#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick and dirty "unit" tests for API. Too complex but do the job."""

from multiprocessing import Process
import unittest
import uuid
import time

import requests

from app import app, queue_manager


class CallLocalApiTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_server = Process(target=app.run)
        cls.test_server.start()
        # Wait for the test server to start
        time.sleep(1)
        cls.registered_addresses_details = [
            requests.get(
                'http://127.0.0.1:5000/register'
            ).json()
            for i in range(10)
        ]
        cls.registered_address_details = requests.get(
            'http://127.0.0.1:5000/register'
        ).json()

        # registered_id is used as an id when authenticating
        cls.registered_id_details = requests.get(
            'http://127.0.0.1:5000/register'
        ).json()

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
            'identity',
            response.json(),
            '\'address\' key not in response JSON of \'register\' endpoint.'
        )
        self.assertIn(
            'epoch',
            response.json(),
            '\'epoch\' key not in response JSON of \'register\' endpoint.'
        )
        address_is_uuid = True
        try:
            uuid.UUID(response.json().get('identity'), version=4)
        except:
            address_is_uuid = False
        self.assertTrue(
            address_is_uuid,
            'Value of \'address\' in response from \'register\' endpoint '
            'is not a valid version 4 UUID.'
        )

    def test_enqueue_broadcast(self):
        request_args = self.get_authentication_args(
            **self.registered_id_details
        )
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
        for address_details in self.registered_addresses_details:
            response = requests.get(
                'http://127.0.0.1:5000/dequeue'
                '?identity={identity}&token={token}'.format(
                    **self.get_authentication_args(**address_details)
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
        request_args = self.get_authentication_args(
            **self.registered_id_details
        )
        request_args.update(
            {
                'data': '["spam", "spam", "spam"]',
                'address': self.registered_address_details['identity'],
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
            'http://127.0.0.1:5000/dequeue'
            '?identity={identity}&token={token}'.format(
                **self.get_authentication_args(
                    **self.registered_address_details
                )
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

    def test_time(self):
        response = requests.get(
            'http://127.0.0.1:5000/time?token={token}'.format(
                token=app.config['VISUALISER_TOKEN']
            )
        )
        self.assertEqual(
            response.status_code,
            200,
            'Request to \'/secs\' returns non-OKAY status code.'
        )

    @staticmethod
    def get_authentication_args(identity, epoch):
        return {
            'identity': identity,
            'token': queue_manager._generate_token(identity, epoch)
        }


if __name__ == '__main__':
    unittest.main()