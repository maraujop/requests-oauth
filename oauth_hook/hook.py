# -*- coding: utf-8 -*-
import time
import random
import urllib
from urlparse import urlparse, urlunparse, parse_qs, urlsplit, urlunsplit

from auth import Token, Consumer
from auth import to_utf8, escape
from auth import SignatureMethod_HMAC_SHA1


class CustomSignatureMethod_HMAC_SHA1(SignatureMethod_HMAC_SHA1):
    def signing_base(self, request, consumer, token):
        """
        This method generates the OAuth signature. It's defined here to avoid circular imports.
        """
        sig = (
            escape(request.method),
            escape(OAuthHook.get_normalized_url(request.url)),
            escape(OAuthHook.get_normalized_parameters(request)),
        )

        key = '%s&' % escape(consumer.secret)
        if token is not None:
            key += escape(token.secret)
        raw = '&'.join(sig)
        return key, raw


class OAuthHook(object):
    OAUTH_VERSION = '1.0'
    header_auth = False
    signature = CustomSignatureMethod_HMAC_SHA1()

    def __init__(self, access_token=None, access_token_secret=None, consumer_key=None, consumer_secret=None, header_auth=None):
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

        if header_auth is not None:
            self.header_auth = header_auth

        self.consumer = Consumer(consumer_key, consumer_secret)

    @staticmethod
    def _split_url_string(query_string):
        """
        Turns a `query_string` into a Python dictionary with unquoted values
        """
        parameters = parse_qs(to_utf8(query_string), keep_blank_values=True)
        for k, v in parameters.iteritems():
            parameters[k] = urllib.unquote(v[0])
        return parameters

    @staticmethod
    def get_normalized_parameters(request):
        """
        Returns a string that contains the parameters that must be signed. 
        This function is called by SignatureMethod subclass CustomSignatureMethod_HMAC_SHA1 
        """
        data_and_params = dict(request.data.items() + request.params.items())
        for key,value in data_and_params.items():
            request.data_and_params[to_utf8(key)] = to_utf8(value)

        if request.data_and_params.has_key('oauth_signature'):
            del request.data_and_params['oauth_signature']

        items = []
        for key, value in request.data_and_params.iteritems():
            # 1.0a/9.1.1 states that kvp must be sorted by key, then by value,
            # so we unpack sequence values into multiple items for sorting.
            if isinstance(value, basestring):
                items.append((key, value))
            else:
                try:
                    value = list(value)
                except TypeError, e:
                    assert 'is not iterable' in str(e)
                    items.append((key, value))
                else:
                    items.extend((key, item) for item in value)

        # Include any query string parameters included in the url
        query_string = urlparse(request.url)[4]
        items.extend([(to_utf8(k), to_utf8(v)) for k, v in OAuthHook._split_url_string(query_string).items()])
        items.sort()

        return urllib.urlencode(items).replace('+', '%20').replace('%7E', '~')

    @staticmethod
    def get_normalized_url(url):
        """
        Returns a normalized url, without params
        """
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

    @staticmethod
    def to_url(request):
        """Serialize as a URL for a GET request."""
        scheme, netloc, path, query, fragment = urlsplit(to_utf8(request.url))
        query = parse_qs(query)

        for key, value in request.data_and_params.iteritems():
            query.setdefault(key, []).append(value)
            
        query = urllib.urlencode(query, True)
        return urlunsplit((scheme, netloc, path, query, fragment))

    @staticmethod
    def to_postdata(request):
        """Serialize as post data for a POST request. This serializes data and params"""
        # tell urlencode to convert each sequence element to a separate parameter
        return urllib.urlencode(request.data_and_params, True).replace('+', '%20')

    @staticmethod
    def authorization_header(oauth_params):
        """Return Authorization header"""
        authorization_headers = 'OAuth realm="",'
        authorization_headers += ','.join(['{0}="{1}"'.format(k, urllib.quote(str(v)))
            for k, v in oauth_params.items()])
        return authorization_headers

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

        # We reset _enc_params info to avoid that requests constructs a wrong url when calling _build_url
        if request._enc_params:
            request._enc_params = ''

        # Looks like OAuth API providers don't handle cookies well, so we reset them
        # See Github issue #5 https://github.com/maraujop/requests-oauth/issues/5
        request.cookies = {}

        # Dictionary to store data and params mixed together
        request.oauth_params = {}

        # Adding OAuth params
        request.oauth_params['oauth_consumer_key'] = self.consumer.key
        request.oauth_params['oauth_timestamp'] = str(int(time.time()))
        request.oauth_params['oauth_nonce'] = str(random.randint(0, 100000000))
        request.oauth_params['oauth_version'] = self.OAUTH_VERSION
        if self.token:
            request.oauth_params['oauth_token'] = self.token.key
        if hasattr(self.token, 'verifier') and self.token.verifier:
            request.oauth_params['oauth_verifier'] = self.token.verifier
        request.oauth_params['oauth_signature_method'] = self.signature.name

        request.data_and_params = request.oauth_params.copy()
        request.oauth_params['oauth_signature'] = self.signature.sign(request, self.consumer, self.token)

        if request.method in ("GET", "DELETE"):
            if not self.header_auth:
                request.data_and_params['oauth_signature'] = request.oauth_params['oauth_signature']
                request.url = self.to_url(request)
            else:
                request.headers['Authorization'] = self.authorization_header(request.oauth_params)
        else:
            if not self.header_auth:
                request.data_and_params['oauth_signature'] = request.oauth_params['oauth_signature']
                request._enc_data = self.to_postdata(request)
            else:
                request.headers['Authorization'] = self.authorization_header(request.oauth_params)

        return request
