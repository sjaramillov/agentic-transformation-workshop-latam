"""Explicit transport for trusted lab endpoints; no proxy or redirect forwarding."""
from urllib.request import HTTPRedirectHandler, ProxyHandler, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_):
        return None


def direct_open(request, *, timeout=4):
    """Keep service credentials at the configured endpoint, ignoring ambient proxies."""
    return build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=timeout)
