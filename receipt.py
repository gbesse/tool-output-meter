#!/usr/bin/env python3
"""Check when an accepted memory document becomes readable at a supplied URL."""
import argparse
import hashlib
import json
import math
import os
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

TEXT = {
    "en": {"visible": "Document visible", "not_visible": "Document still not visible", "denied": "Access denied", "rate_limited": "Rate limited", "server_error": "Server error", "invalid": "Invalid input", "attempts": "attempts"},
    "fr": {"visible": "Document visible", "not_visible": "Document toujours invisible", "denied": "Accès refusé", "rate_limited": "Limite de débit", "server_error": "Erreur du serveur", "invalid": "Entrée invalide", "attempts": "tentatives"},
    "es": {"visible": "Documento visible", "not_visible": "Documento todavía no visible", "denied": "Acceso denegado", "rate_limited": "Límite de solicitudes", "server_error": "Error del servidor", "invalid": "Entrada no válida", "attempts": "intentos"},
}
NOTES = {
    "en": "GET only. A 200 proves this URL responded now, not that retrieval or extraction completed.",
    "fr": "GET uniquement. Un 200 prouve que cette URL répond maintenant, pas que le rappel ou l'extraction est terminé.",
    "es": "Solo GET. Un 200 demuestra que esta URL responde ahora, no que la recuperación o extracción haya terminado.",
}
for language, messages in {
    'fr': {'content_mismatch': 'Le contenu ne correspond pas', 'content_unverified': 'Contenu non vérifié', 'body_limit': 'Corps trop volumineux'},
    'en': {'content_mismatch': 'Content does not match', 'content_unverified': 'Content not verified', 'body_limit': 'Body too large'},
    'es': {'content_mismatch': 'El contenido no coincide', 'content_unverified': 'Contenido no verificado', 'body_limit': 'Cuerpo demasiado grande'},
}.items():
    TEXT[language].update(messages)


def read_document(url, token=None, max_bytes=1_000_000):
    """Read bounded response bytes for identity checks without returning their content."""
    if type(max_bytes) is not int or not 1 <= max_bytes <= 10_000_000:
        raise ValueError('invalid body limit')
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, *_args, **_kwargs):
            return None
    headers = {'Accept': 'application/json', 'Accept-Encoding': 'identity'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    try:
        with build_opener(NoRedirect()).open(Request(url, headers=headers, method='GET'), timeout=10) as response:
            if response.status != 200:
                return {'http_status': response.status}
            raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                return {'http_status': 200, 'body_limit': True}
            return {'http_status': 200, 'content_sha256': hashlib.sha256(raw).hexdigest(), 'content_bytes': len(raw)}
    except HTTPError as error:
        return {'http_status': error.code}


def read_status(url, token=None):
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, *_args, **_kwargs):
            return None

    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers, method="GET")
    try:
        with build_opener(NoRedirect()).open(request, timeout=10) as response:
            return response.status
    except HTTPError as error:
        return error.code


def observe(fetch, attempts=10, interval=1.0, sleep=time.sleep, lang="en", expected_sha256=None):
    if type(attempts) is not int or attempts < 1 or type(interval) not in (int, float) or not math.isfinite(interval) or interval < 0:
        raise ValueError("attempts must be positive and interval nonnegative")
    if expected_sha256 is not None and (not isinstance(expected_sha256, str) or not re.fullmatch(r'[0-9a-f]{64}', expected_sha256)):
        raise ValueError('SHA-256 attendu non valide. / Invalid expected SHA-256. / SHA-256 esperado no válido.')
    start = time.monotonic()
    for number in range(1, attempts + 1):
        fetched = fetch()
        details = fetched if isinstance(fetched, dict) else {}
        code = details.get('http_status') if details else fetched
        if type(code) is not int:
            raise ValueError("GET status must be an integer")
        if code == 200:
            actual = details.get('content_sha256')
            if details.get('body_limit'):
                status = 'body_limit'
            elif expected_sha256 is not None:
                status = 'content_unverified' if actual is None else 'visible' if actual == expected_sha256 else 'content_mismatch'
            else:
                status = "visible"
        elif code == 404:
            status = "not_visible"
        elif code in (401, 403):
            status = "denied"
        elif code == 429:
            status = "rate_limited"
        else:
            status = "server_error"
        if status != "not_visible" or number == attempts:
            result = {"status": status, "http_status": code, "attempts": number,
                    "elapsed_seconds": round(time.monotonic() - start, 3),
                    "note": NOTES[lang]}
            if expected_sha256 is not None:
                result.update(expected_sha256=expected_sha256, content_sha256=details.get('content_sha256'), content_bytes=details.get('content_bytes'), identity_verified=status == 'visible')
            return result
        sleep(interval)
    raise AssertionError("unreachable")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("demo", "watch"))
    parser.add_argument("url", nargs="?")
    parser.add_argument("--token-env", help="Name of an environment variable holding a bearer token")
    parser.add_argument("--attempts", type=int, default=10)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--lang", choices=TEXT, default="en")
    parser.add_argument("--json", action="store_true")
    parser.add_argument('--expect-sha256', help='Empreinte exacte attendue / Expected exact hash / Huella exacta esperada')
    args = parser.parse_args(argv)
    if args.command == "demo":
        statuses = iter((404, 404, 200))
        fetch = lambda: next(statuses)
        attempts, interval = 3, 0
    else:
        parsed = urlsplit(args.url or "")
        if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username or parsed.password:
            parser.error(TEXT[args.lang]["invalid"] + ": watch requires an HTTP(S) document URL without credentials")
        token = os.environ.get(args.token_env) if args.token_env else None
        if args.token_env and not token:
            parser.error(TEXT[args.lang]["invalid"] + ": token environment variable is empty")
        if token and parsed.scheme == "http" and parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
            parser.error(TEXT[args.lang]["invalid"] + ": bearer token requires HTTPS outside localhost")
        fetch = lambda: read_document(args.url, token) if args.expect_sha256 else read_status(args.url, token)
        attempts, interval = args.attempts, args.interval
    try:
        result = observe(fetch, attempts, interval, lang=args.lang, expected_sha256=args.expect_sha256)
    except (ValueError, URLError, OSError) as error:
        print(f"{TEXT[args.lang]['invalid']}: {type(error).__name__}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"{TEXT[args.lang][result['status']]}: HTTP {result['http_status']}; "
              f"{result['attempts']} {TEXT[args.lang]['attempts']}")
    return 0 if result["status"] == "visible" else 2


if __name__ == "__main__":
    raise SystemExit(main())
