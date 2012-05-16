#! /usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import unittest
import random
import json
import requests
from urlparse import parse_qs

# Insert this package's path in the PYTHON PATH as first route
path = os.path.dirname(os.getcwd())
sys.path.insert(0, path)

from oauth_hook.hook import OAuthHook
from test_settings import TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET
from test_settings import TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET
from test_settings import RDIO_API_KEY, RDIO_SHARED_SECRET

# Initializing the hook and Python-requests client
OAuthHook.consumer_key = TWITTER_CONSUMER_KEY
OAuthHook.consumer_secret = TWITTER_CONSUMER_SECRET
oauth_hook = OAuthHook(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
client = requests.session(hooks={'pre_request': oauth_hook})


class TwitterOAuthTestSuite(unittest.TestCase):
    def setUp(self):
        # twitter prefers that you use header_auth
        oauth_hook.header_auth = True

    def test_rate_limit_GET_urlencoded(self):
        oauth_hook.header_auth = False
        self.test_rate_limit_GET()

    def test_rate_limit_GET(self):
        response = client.get('http://api.twitter.com/1/account/rate_limit_status.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['hourly_limit'], 350)

    def test_status_POST_urlencoded(self):
        oauth_hook.header_auth = False
        self.test_status_POST()

    def test_status_POST(self):
        message = "Kind of a random message %s" % random.random()
        response = client.post('http://api.twitter.com/1/statuses/update.json',
            {'status': message, 'wrap_links': True})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['text'], message)

    def test_status_GET_with_data_urlencoded(self):
        oauth_hook.header_auth = False
        self.test_status_GET_with_data()

    def test_status_GET_with_data(self):
        response = client.get('http://api.twitter.com/1/statuses/friends.json', data={'user_id': 12345})
        self.assertEqual(response.status_code, 200)

    def test_status_GET_with_params_urlencoded(self):
        oauth_hook.header_auth = False
        self.test_status_GET_with_params()

    def test_status_GET_with_params(self):
        response = client.get('http://api.twitter.com/1/statuses/friends.json', params={'user_id': 12345})
        self.assertEqual(response.status_code, 200)

    def test_create_delete_list_urlencoded(self):
        oauth_hook.header_auth = False
        self.test_create_delete_list()

    def test_create_delete_list(self):
        screen_name = json.loads(client.get('http://api.twitter.com/1/account/verify_credentials.json').content)['screen_name']
        user_lists = json.loads(client.get('http://api.twitter.com/1/lists.json', data={'screen_name': screen_name}).content)['lists']
        for list in user_lists:
            if list['name'] == 'OAuth Request Hook':
                client.post('http://api.twitter.com/1/lists/destroy.json', data={'list_id': list['id']})

        created_list = json.loads(client.post('http://api.twitter.com/1/%s/lists.json' % screen_name, data={'name': "OAuth Request Hook"}).content)
        list_id = created_list['id']
        response = client.delete('http://api.twitter.com/1/%s/lists/%s.json' % (screen_name, list_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), created_list)

    def test_three_legged_auth(self):
        yes_or_no = raw_input("Do you want to skip Twitter three legged auth test? (y/n):")
        if yes_or_no.lower() in ['y', 'yes']:
            return

        twitter_oauth_hook = OAuthHook()
        for header_auth in (True, False):
            # See https://dev.twitter.com/docs/auth/implementing-sign-twitter
            # Step 1: Obtaining a request token
            twitter_oauth_hook.header_auth = header_auth

            client = requests.session(hooks={'pre_request': twitter_oauth_hook})
            response = client.post('http://api.twitter.com/oauth/request_token', data={'oauth_callback': 'oob'})
            self.assertEqual(response.status_code, 200)
            response = parse_qs(response.content)
            self.assertTrue(response['oauth_token'])
            self.assertTrue(response['oauth_token_secret'])

            oauth_token = response['oauth_token']
            oauth_secret = response['oauth_token_secret']

            # Step 2: Redirecting the user
            print "Go to https://api.twitter.com/oauth/authenticate?oauth_token=%s and sign in into the application, then enter your PIN" % oauth_token[0]
            oauth_verifier = raw_input('Please enter your PIN:')

            # Step 3: Authenticate
            response = client.post('http://api.twitter.com/oauth/access_token', {'oauth_verifier': oauth_verifier, 'oauth_token': oauth_token[0]})
            response = parse_qs(response.content)
            self.assertTrue(response['oauth_token'])
            self.assertTrue(response['oauth_token_secret'])

    def test_update_profile_image_urlencoded(self):
        oauth_hook.header_auth = False
        self.test_update_profile_image()

    def test_update_profile_image(self):
        files = {'image': ('hommer.gif', open('hommer.gif', 'rb'))}
        response = client.post('http://api.twitter.com/1/account/update_profile_image.json', files=files)
        self.assertEqual(response.status_code, 200)


class RdioOAuthTestSuite(unittest.TestCase):
    def setUp(self):
        rdio_oauth_hook = OAuthHook(consumer_key=RDIO_API_KEY, consumer_secret=RDIO_SHARED_SECRET, header_auth=False)
        self.client = requests.session(hooks={'pre_request': rdio_oauth_hook})

    def test_rdio_oauth_get_token_data(self):
        response = self.client.post('http://api.rdio.com/oauth/request_token', data={'oauth_callback': 'oob'})
        self.assertEqual(response.status_code, 200)
        response = parse_qs(response.content)
        self.assertTrue(response['oauth_token'])
        self.assertTrue(response['oauth_token_secret'])

    def test_rdio_oauth_get_token_params(self):
        self.client.params = {'oauth_callback': 'oob'}
        response = self.client.post('http://api.rdio.com/oauth/request_token')
        self.assertEqual(response.status_code, 200)
        response = parse_qs(response.content)
        self.assertTrue(response['oauth_token'])
        self.assertTrue(response['oauth_token_secret'])


if __name__ == '__main__':
    unittest.main()
