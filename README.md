# requests-oauth

This is a hook for <a href="http://github.com/kennethreitz/requests">python-requests</a> great python HTTP library by <a href="https://github.com/kennethreitz">Kenneth Reitz</a>, that makes python-requests support Open Authentication version 1.0. The intention of this project is to provide the easiest way to do OAuth connections with Python.

This hook was initially based on <a href="https://github.com/simplegeo/python-oauth2">python-oauth2</a>, which looks unmaintained, kudos to the authors and contributors for doing a huge effort in providing OAuth to python httplib2.

* Author: <a href="http://www.github.com/maraujop/">Miguel Araujo</a>
* Licence: BSD

## Installation

You can install requests-oauth by simply doing:

    pip install requests-oauth

## Usage

You can initialize the hook passing it 4 parameters: `access_token`, `access_token_secret`, `consumer_key`, `consumer_secret`. First two `access_token` and `access_token_secret` are optional, in case you want to retrieve those from the API service (see later for an example). There are two ways to do initialize the hook. First one:

    oauth_hook = OAuthHook(access_token, access_token_secret, consumer_key, consumer_secret)

If you are using the same `consumer_key` and `consumer_secret` all the time, you probably want to setup those fixed, so that you only have to pass the token parameters for setting the hook:

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

Then fill in the information there. At the moment, the testing of the library is done in a functional way, doing a GET and a POST request against OAuth API services, so use a test account and not your personal account:

    ./tests.py

## Contributing

If you'd like to contribute, simply fork the repository, commit your changes to the `dev` branch (or branch off of it), and send a pull request. Make sure you add yourself to AUTHORS.

## TODO

* Improve testing suite.
* Support for python3.
