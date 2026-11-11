"""HTTPS GETs and downloads with the standard library, and working certificates.

The python.org installer's Python ships without CA certificates until its
"Install Certificates" step is run, so on many Macs every HTTPS request fails
with CERTIFICATE_VERIFY_FAILED. When Python's own store is empty, this module
falls back to the bundle macOS keeps at /etc/ssl/cert.pem.
"""

import json
import os
import ssl
import urllib.error
import urllib.request

from .errors import DOWNLOAD_FAILED, LOOKUP_FAILED, CastError

SYSTEM_CA_BUNDLE = "/etc/ssl/cert.pem"
USER_AGENT = "cast2skill/0.1 (+https://github.com/razamit/cast2skill)"
TIMEOUT_S = 30
MAX_TEXT_BYTES = 20 * 1024 * 1024  # feeds and API answers; audio goes through download()
MAX_DOWNLOAD_BYTES = 2 * 1024 ** 3  # a 10-hour 128 kbps episode is about 0.6 GB


def ca_bundle_override():
    """The CA file to use when Python's default store is empty, or None."""
    if os.environ.get("SSL_CERT_FILE"):
        return None
    if ssl.create_default_context().cert_store_stats().get("x509_ca", 0) > 0:
        return None
    return SYSTEM_CA_BUNDLE if os.path.isfile(SYSTEM_CA_BUNDLE) else None


def ssl_context():
    return ssl.create_default_context(cafile=ca_bundle_override())


def subprocess_env():
    """Environment for child tools (yt-dlp) with the same certificate fallback."""
    env = dict(os.environ)
    override = ca_bundle_override()
    if override:
        env["SSL_CERT_FILE"] = override
    return env


def require_http(url, error_code):
    if not url.lower().startswith(("https://", "http://")):
        raise CastError(error_code, f"Refusing a non-web link: {url[:120]}", "Only http(s) links are fetched.")


def open_url(url, timeout=TIMEOUT_S, error_code=LOOKUP_FAILED):
    require_http(url, error_code)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    return urllib.request.urlopen(request, timeout=timeout, context=ssl_context())


def get_bytes(url, error_code=LOOKUP_FAILED, hint=""):
    """(body bytes, content type). Raises CastError(error_code) on any failure."""
    try:
        with open_url(url) as response:
            body = response.read(MAX_TEXT_BYTES + 1)
            content_type = response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        raise CastError(error_code, f"{url} answered HTTP {exc.code}.", hint)
    except (urllib.error.URLError, OSError, ValueError) as exc:
        reason = getattr(exc, "reason", exc)
        raise CastError(error_code, f"Could not reach {url}: {reason}", hint)
    if len(body) > MAX_TEXT_BYTES:
        raise CastError(error_code, f"{url} returned more than {MAX_TEXT_BYTES} bytes.", hint)
    return body, content_type


def get_json(url, error_code=LOOKUP_FAILED, hint=""):
    body, _ = get_bytes(url, error_code, hint)
    try:
        return json.loads(body.decode("utf-8"))
    except ValueError:
        raise CastError(error_code, f"{url} did not return JSON.", hint)


def copy_with_limit(response, handle, limit=MAX_DOWNLOAD_BYTES):
    copied = 0
    while True:
        chunk = response.read(1024 * 1024)
        if not chunk:
            return copied
        copied += len(chunk)
        if copied > limit:
            raise CastError(DOWNLOAD_FAILED, f"The download is larger than {limit // 2**30} GB; stopped.",
                            "Download the audio yourself and pass the file.")
        handle.write(chunk)


def download(url, destination):
    """Stream a file to disk (written to a .part file, then renamed)."""
    partial = destination + ".part"
    try:
        with open_url(url, timeout=120, error_code=DOWNLOAD_FAILED) as response, open(partial, "wb") as handle:
            copy_with_limit(response, handle)
    except CastError:
        if os.path.exists(partial):
            os.remove(partial)
        raise
    except (urllib.error.URLError, OSError, ValueError) as exc:
        if os.path.exists(partial):
            os.remove(partial)
        reason = getattr(exc, "reason", exc)
        raise CastError(DOWNLOAD_FAILED, f"Download failed for {url}: {reason}",
                        "Check the link, or download the audio yourself and pass the file.")
    os.replace(partial, destination)
    return destination
