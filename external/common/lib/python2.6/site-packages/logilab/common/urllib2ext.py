import logging
import urllib2

import kerberos as krb

class GssapiAuthError(Exception):
    """raised on error during authentication process"""

import re
RGX = re.compile('(?:.*,)*\s*Negotiate\s*([^,]*),?', re.I)

def get_negociate_value(headers):
    for authreq in headers.getheaders('www-authenticate'):
        match = RGX.search(authreq)
        if match:
            return match.group(1)

class HTTPGssapiAuthHandler(urllib2.BaseHandler):
    """Negotiate HTTP authentication using context from GSSAPI"""

    handler_order = 400 # before Digest Auth

    def __init__(self):
        self._reset()

    def _reset(self):
        self._retried = 0
        self._context = None

    def clean_context(self):
        if self._context is not None:
            krb.authGSSClientClean(self._context)

    def http_error_401(self, req, fp, code, msg, headers):
        try:
            if self._retried > 5:
                raise urllib2.HTTPError(req.get_full_url(), 401,
                                        "negotiate auth failed", headers, None)
            self._retried += 1
            logging.debug('gssapi handler, try %s' % self._retried)
            negotiate = get_negociate_value(headers)
            if negotiate is None:
                logging.debug('no negociate found in a www-authenticate header')
                return None
            logging.debug('HTTPGssapiAuthHandler: negotiate 1 is %r' % negotiate)
            result, self._context = krb.authGSSClientInit("HTTP@%s" % req.get_host())
            if result < 1:
                raise GssapiAuthError("HTTPGssapiAuthHandler: init failed with %d" % result)
            result = krb.authGSSClientStep(self._context, negotiate)
            if result < 0:
                raise GssapiAuthError("HTTPGssapiAuthHandler: step 1 failed with %d" % result)
            client_response = krb.authGSSClientResponse(self._context)
            logging.debug('HTTPGssapiAuthHandler: client response is %s...' % client_response[:10])
            req.add_unredirected_header('Authorization', "Negotiate %s" % client_response)
            server_response = self.parent.open(req)
            negotiate = get_negociate_value(server_response.info())
            if negotiate is None:
                logging.warning('HTTPGssapiAuthHandler: failed to authenticate server')
            else:
                logging.debug('HTTPGssapiAuthHandler negotiate 2: %s' % negotiate)
                result = krb.authGSSClientStep(self._context, negotiate)
                if result < 1:
                    raise GssapiAuthError("HTTPGssapiAuthHandler: step 2 failed with %d" % result)
            return server_response
        except GssapiAuthError, exc:
            logging.error(repr(exc))
        finally:
            self.clean_context()
            self._reset()

if __name__ == '__main__':
    import sys
    # debug
    import httplib
    httplib.HTTPConnection.debuglevel = 1
    httplib.HTTPSConnection.debuglevel = 1
    # debug
    import logging
    logging.basicConfig(level=logging.DEBUG)
    # handle cookies
    import cookielib
    cj = cookielib.CookieJar()
    ch = urllib2.HTTPCookieProcessor(cj)
    # test with url sys.argv[1]
    h = HTTPGssapiAuthHandler()
    response = urllib2.build_opener(h, ch).open(sys.argv[1])
    print '\nresponse: %s\n--------------\n' % response.code, response.info()
