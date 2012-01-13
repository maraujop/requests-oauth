#! /usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import unittest
import random
import json
import requests
from urlparse import parse_qs

sys.path.append(os.path.dirname(os.getcwd()))

from oauth_hook.hook import OAuthHook
from test_settings import TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET
from test_settings import TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET
from test_settings import RDIO_API_KEY, RDIO_SHARED_SECRET

# Initializing the hook and Python-requests client
OAuthHook.consumer_key = TWITTER_CONSUMER_KEY
OAuthHook.consumer_secret = TWITTER_CONSUMER_SECRET
oauth_hook = OAuthHook(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
client = requests.session(hooks={'pre_request': oauth_hook})

class OAuthTestSuite(unittest.TestCase):
    def test_twitter_rate_limit_GET(self):
        oauth_hook.header_auth = True
        response = client.get('http://api.twitter.com/1/account/rate_limit_status.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['hourly_limit'], 350)

    def test_twitter_status_POST(self):
        oauth_hook.header_auth = False
        message = "Kind of a random message %s" % random.random()
        response = client.post('http://api.twitter.com/1/statuses/update.json', 
            {'status': message, 'wrap_links': True})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['text'], message)

    def test_twitter_status_GET_with_data(self):
        oauth_hook.header_auth = False
        response = client.get('http://api.twitter.com/1/statuses/friends.json', data={'user_id': 12345})
        self.assertEqual(response.status_code, 200)

    def test_twitter_create_delete_list(self):
        oauth_hook.header_auth = True
        screen_name = json.loads(client.get('https://api.twitter.com/1/account/verify_credentials.json').content)['screen_name']
        user_lists = json.loads(client.get('https://api.twitter.com/1/lists.json', data={'screen_name': screen_name}).content)['lists']
        for list in user_lists:
            if list['name'] == 'OAuth Request Hook':
                client.post('https://api.twitter.com/1/lists/destroy.json', data={'list_id': list['id']})

        created_list = json.loads(client.post('https://api.twitter.com/1/%s/lists.json' % screen_name, data={'name': "OAuth Request Hook"}).content)
        list_id = created_list['id']
        response = client.delete('http://api.twitter.com/1/%s/lists/%s.json' % (screen_name, list_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), created_list)

    def test_twitter_oauth_get_token(self):
        twitter_oauth_hook = OAuthHook(header_auth=True)
        client = requests.session(hooks={'pre_request': twitter_oauth_hook})
        response = client.get('https://api.twitter.com/oauth/request_token')
        self.assertEqual(response.status_code, 200)
        response = parse_qs(response.content)
        self.assertTrue(response['oauth_token'])
        self.assertTrue(response['oauth_token_secret'])

    def test_rdio_oauth_get_token_data(self):
        rdio_oauth_hook = OAuthHook(consumer_key=RDIO_API_KEY, consumer_secret=RDIO_SHARED_SECRET, header_auth=False)
        client = requests.session(hooks={'pre_request': rdio_oauth_hook})
        response = client.post('http://api.rdio.com/oauth/request_token', {'oauth_callback': 'oob'})
        self.assertEqual(response.status_code, 200)
        response = parse_qs(response.content)
        self.assertTrue(response['oauth_token'])
        self.assertTrue(response['oauth_token_secret'])

    def test_rdio_oauth_get_token_params(self):
        rdio_oauth_hook = OAuthHook(consumer_key=RDIO_API_KEY, consumer_secret=RDIO_SHARED_SECRET, header_auth=False)
        client = requests.session(hooks={'pre_request': rdio_oauth_hook}, params={'oauth_callback': 'oob'})
        response = client.post('http://api.rdio.com/oauth/request_token')
        self.assertEqual(response.status_code, 200)
        response = parse_qs(response.content)
        self.assertTrue(response['oauth_token'])
        self.assertTrue(response['oauth_token_secret'])

    def test_update_profile_image(self):
        # Images updates, need header authentication
        oauth_hook.header_auth = True
        files = {'image': ('hommer.gif', open('hommer.gif', 'rb'))}
        response = client.post('http://api.twitter.com/1/account/update_profile_image.json', files=files)
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
