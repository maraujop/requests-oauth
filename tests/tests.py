#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import unittest
import random
import json
import requests

sys.path.append(os.path.dirname(os.getcwd()))

from oauth_hook import OAuthHook
from test_settings import TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET
from test_settings import TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET

# Initializing the hook and Python-requests client
OAuthHook.consumer_key = TWITTER_CONSUMER_KEY
OAuthHook.consumer_secret = TWITTER_CONSUMER_SECRET
oauth_hook = OAuthHook(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
client = requests.session(hooks={'pre_request': oauth_hook})

class OAuthTestSuite(unittest.TestCase):
    def test_twitter_rate_limit_GET(self):
        response = client.get('http://api.twitter.com/1/account/rate_limit_status.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['hourly_limit'], 350)

    def test_twitter_status_POST(self):
        message = "Kind of a random message %s" % random.random()
        response = client.post('http://api.twitter.com/1/statuses/update.json', 
            {'status': message, 'wrap_links': True})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['text'], message)

    def test_twitter_status_GET_with_data(self):
        response = client.get('http://api.twitter.com/1/statuses/friends.json', data={'user_id': 12345})
        self.assertEqual(response.status_code, 200)

    def test_twitter_delete(self):
        """Depends on GET and POST also working properly, as we must first determine the current username and then create a test list to subsequently delete.
        This test creates a list on Twitter, then deletes it, testing to ensure that OAuth signing occurs on delete."""
        screen_name = json.loads(client.get('https://api.twitter.com/1/account/verify_credentials.json').content)['screen_name']
        created_list = json.loads(client.post('https://api.twitter.com/1/%s/lists.json' % screen_name, data={'name': "OAuth Request Hook"}).content)
        list_id = created_list['id']
        response = client.delete('http://api.twitter.com/1/%s/lists/%s.json' % (screen_name, list_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), created_list)

if __name__ == '__main__':
    unittest.main()
