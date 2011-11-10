import binascii
import hmac
import random
import urllib
from urlparse import urlparse, urlunparse
try:
    from hashlib import sha1
    sha = sha1
except ImportError:
    # hashlib was added in Python 2.5
    import sha


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
        if verifier is None:
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


class SignatureMethod_HMAC_SHA1(object):
    """
    This is a barebones implementation of a signature method only suitable for use 
    for signing OAuth HTTP requests as a hook to requests library.
    """
    name = 'HMAC-SHA1'

    def check(self, request, consumer, token, signature):
        """Returns whether the given signature is the correct signature for
        the given consumer and token signing the given request."""
        built = self.sign(request, consumer, token)
        return built == signature

    def signing_base(self, request, consumer, token):
        pass

    def sign(self, request, consumer, token):
        """Builds the base signature string."""
        key, raw = self.signing_base(request, consumer, token)
        hashed = hmac.new(key, raw, sha)
        # Calculate the digest base 64.
        return binascii.b2a_base64(hashed.digest())[:-1]
