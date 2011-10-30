# requests-oauth-hook

This is a hook for <a href="http://github.com/kennethreitz/requests">python-requests</a> great python HTTP library by <a href="https://github.com/kennethreitz">Kenneth Reitz</a>, that makes python-requests support Open Authentication version 1.0. 

This hook is based on <a href="https://github.com/simplegeo/python-oauth2">python-oauth2</a> and uses portions of its code at the moment, kudos to the authors and contributors for doing a huge effort in providing OAuth to python httplib2.

* Author: <a href="http://www.github.com/maraujop/">Miguel Araujo</a>
* Licence: BSD

## Installation

You can install requests-oauth-hook, simply:

    pip install requests-oauth-hook

## Usage

You need to initialize the hook passing it 4 things: `access_token`, `access_token_secret`, `consumer_key`, `consumer_secret`. There are two ways to do this. First one:

    oauth_hook = OAuthHook(access_token, access_token_secret, consumer_key, consumer_secret)

If you are using the same `consumer_key` and `consumer_secret` all the time, you probably want to setup those fixed, so that you only have to pass the token parameters for settings the hook:

    OAuthHook.consumer_key = consumer_key
    OAuthHook.consumer_secret = consumer_secret
    oauth_hook = OAuthHook(access_token, access_token_secret)

Now you need to pass the hook to python-requests, you probably want to do it as a session, so you don't have to do this every time:

    client = requests.session(hooks={'pre_request': oauth_hook})

What you get is python-requests client which you can use the same way as you use requests API. Let's see a GET example:

    response = client.get('http://api.twitter.com/1/account/rate_limit_status.json')
    results = json.loads(response.content)

And a POST example:

    response = client.post('http://api.twitter.com/1/statuses/update.json', {'status': "Yay! It works!", 'wrap_links': True})

Beware that you are not forced to pass the token information to the hook. That way you can retrieve it from the API. Let's see a Twitter example:

    client = requests.session(hooks={'pre_request': OAuthHook(consumer_key=consumer_key, consumer_secret=consumer_secret)})
    response = client.get('https://api.twitter.com/oauth/request_token')
    response = parse_qs(response.content)
    print "Token: %s  Secret: %s" % (response['oauth_token'], response['oauth_token_secret'])

## Testing

If you want to run the tests, you will need to copy `test_settings.py.template` into `test_settings.py`. This file is in the `.gitignore` index, so it won't be committed:

    cp test_settings.py.template test_settings.py

Then fill in the information there. At the moment, the testing of the library is done in a functional way, doing a GET and a POST request against Twitter API. So use a test account and not your personal account:

    ./tests.py

## Contributing

If you'd like to contribute, simply fork the repository, commit your changes to the `dev` branch (or branch off of it), and send a pull request. Make sure you add yourself to AUTHORS.

## TODO

* Review python-oauth2 pull requests and bugs. It looks like it's not being maintained anymore.
* Work on real unit tests.
* Support for python3.
