# requests-oauth

This plugins adds OAuth v1.0 support to <a href="https://github.com/kennethreitz">@kennethreitz</a> well-known <a href="http://github.com/kennethreitz/requests">requests</a> library providing both header and url-encoded authentication.

requests-oauth wants to provide the simplest and easiest way to do OAuth in Python. It was initially based on <a href="https://github.com/simplegeo/python-oauth2">python-oauth2</a> (which looks unmaintained), kudos to the authors and contributors for doing a huge effort in providing OAuth to python httplib2. From that point on, the code base has been cleaned, fixing several bugs and heavily refactoring it to eliminate dependencies with python-oauth2, being now a stand-alone plugin.

* Author: <a href="http://www.github.com/maraujop/">Miguel Araujo</a>
* Licence: BSD

## Installation

You can install requests-oauth by simply doing:

    pip install requests-oauth

## Usage

Import the hook doing:

    from oauth_hook import OAuthHook

You can initialize the hook passing it 5 parameters: `access_token`, `access_token_secret`, `consumer_key`, `consumer_secret` and `header_auth`. First two `access_token` and `access_token_secret` are optional, in case you want to retrieve those from the API service (see later for an example). There are two ways to do initialize the hook. First one:

    oauth_hook = OAuthHook(access_token, access_token_secret, consumer_key, consumer_secret, header_auth)

The `header_auth` parameter lets you chose the authentication method used. It's a boolean, if you set it to `True` you will be using an Authorization header. If your API supports this authentication method, it's the one you should be using and the prefered method by the OAuth spec (<a href="http://tools.ietf.org/html/rfc5849#section-3.5">RFC 5849</a>), an example would be Twitter's API. By default `header_auth` is set to `False`, which means url encoded authentication will be used. This is because this the most widely supported authentication system.

If you are using the same `consumer_key` and `consumer_secret` all the time, you probably want to setup those fixed, so that you only have to pass the token parameters for setting the hook:

    OAuthHook.consumer_key = consumer_key
    OAuthHook.consumer_secret = consumer_secret
    oauth_hook = OAuthHook(access_token, access_token_secret, header_auth=True)

Now you need to pass the hook to python-requests, you probably want to do it as a session, so you don't have to do this every time:

    client = requests.session(hooks={'pre_request': oauth_hook})

What you get is python-requests client which you can use the same way as you use requests API. Let's see a GET example:

    response = client.get('http://api.twitter.com/1/account/rate_limit_status.json')
    results = json.loads(response.content)

And a POST example:

    response = client.post('http://api.twitter.com/1/statuses/update.json', {'status': "Yay! It works!", 'wrap_links': True})

## 3-legged Authorization

First time authorization and authentication follows a system named three legged OAuth, very well described in <a href="https://dev.twitter.com/docs/auth/implementing-sign-twitter">Twitter documentation</a>.

Basically it is composed of three steps. Let's see an example based on Imgur's API. All the other APIs work pretty much the same way, only endpoints (urls) change:

#### Step 1: Obtaining a request token

We start asking for a request token, which will finally turn into an access token, the one we need to operate on behalf of the user.

    imgur_oauth_hook = OAuthHook(consumer_key=YOUR_IMGUR_CONSUMER_KEY, consumer_secret=YOUR_IMGUR_CONSUMER_SECRET)
    response = requests.post('http://api.imgur.com/oauth/request_token', hooks={'pre_request': imgur_oauth_hook})
    qs = parse_qs(response.text)
    oauth_token = qs['oauth_token'][0]
    oauth_secret = qs['oauth_token_secret'][0]

#### Step 2: Redirecting the user for getting authorization

In this step we give the user a link or open a web browser redirecting him to an endpoint, passing the `oauth_token` got in the previous step as a url parameter. The user will get a dialog asking for authorization for our application. In this case we are doing an out of band desktop application, so the user will have to input us a code named `verifier`. In web apps, we will get this code as a webhook.

    print "Go to http://api.imgur.com/oauth/authorize?oauth_token=%s allow the app and copy your PIN" % oauth_token
    oauth_verifier = raw_input('Please enter your PIN:')

#### Step 3: Authenticate

Once we get user's authorization, we request a final access token, to operate on behalf of the user. We build a new hook using previous request token information achieved on step1 and pass the verifier (got in step2) as data using `oauth_verifier` key:

    new_imgur_oauth_hook = OAuthHook(oauth_token, oauth_secret, IMGUR_CONSUMER_KEY, IMGUR_CONSUMER_SECRET)
    response = requests.post('http://api.imgur.com/oauth/access_token', {'oauth_verifier': oauth_verifier}, hooks={'pre_request': new_imgur_oauth_hook})
    response = parse_qs(response.content)
    final_token = response['oauth_token'][0]
    final_token_secret = response['oauth_token_secret'][0]

These `final_token` and `final_token_secret` are the credentials we need to use for handling user's oauth, so most likely you will want to persist them somehow. These are the ones you should use for building a requests session with a new hook. Beware that not all OAuth APIs provide unlimited time credentials.

## Testing

If you want to run the tests, you will need to copy `test_settings.py.template` into `test_settings.py`. This file is in the `.gitignore` index, so it won't be committed:

    cp test_settings.py.template test_settings.py

Then fill in the information there. The testing of the library is done in a functional way, doing GETs and POSTs against public OAuth APIs like Twitter, so use a test account and not your personal account:

    ./tests.py

## Contributing

If you'd like to contribute, simply fork the repository, commit your changes to the `dev` branch (or branch off of it), and send a pull request. Make sure you add yourself to AUTHORS.
