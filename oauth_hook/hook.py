# -*- coding: utf-8 -*-
import binascii
import hmac
import time
import random
import base64

import urllib
from urlparse import urlparse, urlunparse, parse_qs, urlsplit, urlunsplit

try:
    from hashlib import sha1
    sha = sha1
except ImportError:
    # hashlib was added in Python 2.5
    import sha

###Functions which were previously-provided by Python-oAuth2, ported and shrunk.
to_utf8 = lambda s: s.encode('UTF-8')
to_utf8_if_string = lambda s: isinstance(s, basestring) and to_utf8(s) or s
escape = lambda url: urllib.quote(to_utf8(url), safe='~')
def to_utf8_optional_iterator(x):
    if isinstance(x, basestring): return to_utf8(x)
    try:
        l = iter(x)
    except TypeError:
        return x
    return [to_utf8_if_string(i) for i in l]

###Token classes from oAuth2.
generate_verifier = lambda length=8: ''.join([str(random.randint(0, 9)) for i in xrange(length)])

class OAuthObject(object):
    key = secret = None


    def __init__(self, key, secret):
        self.key, self.secret = key, secret
        if None in (self.key, self.secret):
            raise ValueError("Key and secret must be set.")

class Consumer(OAuthObject):
    pass

class Token(OAuthObject):
    callback = callback_confirmed = verifier = None

    def set_callback(self, callback):
        self.callback = callback
        self.callback_confirmed = True

    def set_verifier(self, verifier=None):
        if varifier is None:
            verifier = generate_verifier()
        self.verifier = verifier

    def get_callback_url(self):
        if self.callback and self.verifier:
            # Append the oauth_verifier.
            parts = urlparse(self.callback)
            scheme, netloc, path, params, query, fragment = parts[:6]
            if query:
                query = '%s&oauth_verifier=%s' % (query, self.verifier)
            else:
                query = 'oauth_verifier=%s' % self.verifier
            return urlunparse((scheme, netloc, path, params,
                query, fragment))
        return self.callback

###Signature method

class CustomSignatureMethod_HMAC_SHA1(object):
    """This is a barebones implementation of a signature method only suitable for use for signing oAuth HTTP requests as a hook to the oAuth Hook library."""
    name = 'HMAC-SHA1'

    def check(self, request, consumer, token, signature):
        """Returns whether the given signature is the correct signature for
        the given consumer and token signing the given request."""
        built = self.sign(request, consumer, token)
        return built == signature

    def signing_base(self, request, consumer, token):
        normalized_url = OAuthHook.get_normalized_url(request.url)
        if normalized_url is None:
            raise ValueError("normalized URL for request is not set.")

        sig = (
            escape(request.method),
            escape(normalized_url),
            escape(OAuthHook.get_normalized_parameters(request)),
        )

        key = '%s&' % escape(consumer.secret)
        if token:
            key += escape(token.secret)
        raw = '&'.join(sig)
        return key, raw

    def sign(self, request, consumer, token):
        """Builds the base signature string."""
        key, raw = self.signing_base(request, consumer, token)
        hashed = hmac.new(key, raw, sha)
        # Calculate the digest base 64.
        return binascii.b2a_base64(hashed.digest())[:-1]

   

class OAuthHook(object):
    OAUTH_VERSION = '1.0'
    consumer_key = None
    consumer_secret = None
    signature = CustomSignatureMethod_HMAC_SHA1()

    def __init__(self, access_token=None, access_token_secret=None, consumer_key=None, consumer_secret=None):
        """
        Consumer is compulsory, while the user's Token can be retrieved through the API
        """
        if access_token is not None and access_token_secret is not None:
            self.token = Token(access_token, access_token_secret)
        else:
            self.token = None

        if consumer_key is None and consumer_secret is None:
            consumer_key = self.consumer_key
            consumer_secret = self.consumer_secret

        self.consumer = Consumer(consumer_key, consumer_secret)

    @staticmethod
    def _split_url_string(param_str):
        """Turn URL string into parameters."""
        parameters = parse_qs(param_str.encode('utf-8'), keep_blank_values=True)
        for k, v in parameters.iteritems():
            parameters[k] = urllib.unquote(v[0])
        return parameters

    @staticmethod
    def get_normalized_parameters(request):
        """Returns a string that contains the parameters that must be signed. 
        This function is called by oauth2 SignatureMethod subclass CustomSignatureMethod_HMAC_SHA1 """
        data_and_params = dict(request.data.items() + request.params.items())
        items = []
        for key, value in data_and_params.iteritems():
            if key == 'oauth_signature':
                continue
            # 1.0a/9.1.1 states that kvp must be sorted by key, then by value,
            # so we unpack sequence values into multiple items for sorting.
            if isinstance(value, basestring):
                items.append((to_utf8_if_string(key), to_utf8(value)))
            else:
                try:
                    value = list(value)
                except TypeError, e:
                    assert 'is not iterable' in str(e)
                    items.append((to_utf8_if_string(key), to_utf8_if_string(value)))
                else:
                    items.extend((to_utf8_if_string(key), to_utf8_if_string(item)) for item in value)

        # Include any query string parameters from the provided URL
        query = urlparse(request.url)[4]

        url_items = OAuthHook._split_url_string(query).items()
        url_items = [(to_utf8(k), to_utf8(v)) for k, v in url_items if k != 'oauth_signature']
        items.extend(url_items)

        items.sort()
        encoded_str = urllib.urlencode(items)
        # Encode signature parameters per OAuth Core 1.0 protocol
        # spec draft 7, section 3.6
        # (http://tools.ietf.org/html/draft-hammer-oauth-07#section-3.6)
        # Spaces must be encoded with "%20" instead of "+"
        return encoded_str.replace('+', '%20').replace('%7E', '~')

    @staticmethod
    def get_normalized_url(url):
        """
        Returns a normalized url, without params
        """
        if url is not None:
            scheme, netloc, path, params, query, fragment = urlparse(url)

            # Exclude default port numbers.
            if scheme == 'http' and netloc[-3:] == ':80':
                netloc = netloc[:-3]
            elif scheme == 'https' and netloc[-4:] == ':443':
                netloc = netloc[:-4]
            if scheme not in ('http', 'https'):
                raise ValueError("Unsupported URL %s (%s)." % (url, scheme))

            # Normalized URL excludes params, query, and fragment.
            return urlunparse((scheme, netloc, path, None, None, None))
        else:
            return None

    @staticmethod
    def to_url(request):
        """Serialize as a URL for a GET request."""
        scheme, netloc, path, query, fragment = urlsplit(request.url.encode('utf-8'))
        query = parse_qs(query)
        data_and_params = dict(request.data.items() + request.params.items())

        for key, value in data_and_params.iteritems():
            query.setdefault(key.encode('utf-8'), []).append(to_utf8_optional_iterator(value))
            
        query = urllib.urlencode(query, True)
        return urlunsplit((scheme, netloc, path, query, fragment))

    @staticmethod
    def to_postdata(request):
        """Serialize as post data for a POST request. This serializes data and params"""
        # Headers and data together in a dictionary
        data_and_params = dict(request.data.items() + request.params.items())

        d = {}
        for k, v in data_and_params.iteritems():
            d[k.encode('utf-8')] = to_utf8_optional_iterator(v)

        # tell urlencode to deal with sequence values and map them correctly
        # to resulting querystring. for example self["k"] = ["v1", "v2"] will
        # result in 'k=v1&k=v2' and not k=%5B%27v1%27%2C+%27v2%27%5D
        return urllib.urlencode(d, True).replace('+', '%20')

    def sign_request(self, request):
        """Signs the request using `self.signature`, `self.consumer` and `self.token`
        for OAuth authentication handling. This basically means generating and adding 
        `oauth_signature_method` and `oauth_signature` to `request.params`.
        """
        if not request.method == "POST":
            # according to
            # http://oauth.googlecode.com/svn/spec/ext/body_hash/1.0/oauth-bodyhash.html
            # section 4.1.1 "OAuth Consumers MUST NOT include an
            # oauth_body_hash parameter on requests with form-encoded
            # request bodies."
            if request._enc_data is None:
                request._enc_data = ''

            request.params['oauth_body_hash'] = base64.b64encode(sha(request._enc_data).digest())

        request.params['oauth_signature_method'] = self.signature.name
        request.params['oauth_signature'] = self.signature.sign(request, self.consumer, self.token)

    def __call__(self, request):
        """
        Pre-request hook that signs a Python-requests Request for OAuth authentication
        """
        # These checkings are necessary because type inconsisntecy of requests library
        # See request Github issue #230 https://github.com/kennethreitz/requests/pull/230
        if not request.params:
            request.params = {}
        if not request.data:
            request.data = {}
        if isinstance(request.params, list):
            request.params = dict(request.params)
        if isinstance(request.data, list):
            request.data = dict(request.data)

        # Adding oauth stuff to params
        request.params['oauth_consumer_key'] = self.consumer.key
        request.params['oauth_timestamp'] = str(int(time.time()))
        request.params['oauth_nonce'] = str(random.randint(0, 100000000))
        request.params['oauth_version'] = self.OAUTH_VERSION

        if self.token:
            request.params['oauth_token'] = self.token.key
        if hasattr(self.token, 'verifier'):
            request.params['oauth_verifier'] = self.token.verifier

        self.sign_request(request)

        # We reset _enc_params info to avoid that requests constructs a wrong url when calling
        # _build_url in models.py
        if request._enc_params:
            request._enc_params = ''

        if request.method in ("GET", "DELETE"):
            request.url = self.to_url(request)
        else:
            request.headers['Content-Type'] = 'application/x-www-form-urlencoded'
            request._enc_data = self.to_postdata(request)

        return request
