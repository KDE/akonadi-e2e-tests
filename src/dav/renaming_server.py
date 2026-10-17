# SPDX-FileCopyrightText: 2026 David Faure <faure@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from logging import getLogger
from typing import override
from urllib.parse import quote

import requests

from src.dav.dav_server import DAVServer
from src.dav.radicale_server import RadicaleServer

log = getLogger(__name__)

# Hop-by-hop headers, and headers describing the body that requests already decoded
_SKIPPED_RESPONSE_HEADERS = {
    "connection",
    "keep-alive",
    "transfer-encoding",
    "content-encoding",
    "content-length",
}
_UID_RE = re.compile(rb"^UID:(.+?)\r?$", re.MULTILINE)


class _RenamingProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    upstream_url: str
    renamed: list[tuple[str, str]]

    def _forward(self) -> None:
        # Bodies with chunked transfer encoding are not supported; KDAV and requests don't send them
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else None
        path = self.path
        location = None

        # Store new items under their UID and say so with a path-only Location, like sabre/dav based servers (e.g. Kolab)
        if (
            self.command == "PUT"
            and self.headers.get("If-None-Match") == "*"
            and path.endswith(".ics")
            and body
        ):
            match = _UID_RE.search(body)
            if match:
                path = (
                    path.rsplit("/", 1)[0] + "/" + quote(match.group(1).decode(), safe="") + ".ics"
                )
                log.info("Storing %s as %s", self.path, path)
                location = path

        headers = {
            k: v
            for k, v in self.headers.items()
            if k.lower() not in ("host", "connection", "content-length")
        }
        try:
            resp = requests.request(
                self.command,
                self.upstream_url + path,
                headers=headers,
                data=body,
                allow_redirects=False,
                timeout=30,
            )
        except requests.RequestException as e:
            log.exception("Request to Radicale failed")
            self.send_error(502, explain=str(e))
            return

        renamed = location is not None and resp.status_code == 201
        if renamed:
            self.renamed.append((self.path, path))
        self.send_response(resp.status_code)
        for key, value in resp.headers.items():
            if key.lower() in _SKIPPED_RESPONSE_HEADERS or (renamed and key.lower() == "location"):
                continue
            self.send_header(key, value)
        if renamed:
            self.send_header("Location", path)
        self.send_header("Content-Length", str(len(resp.content)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(resp.content)

    def log_message(self, format, *args):  # noqa: A002
        log.debug(format, *args)


for _method in (
    "GET",
    "HEAD",
    "PUT",
    "POST",
    "DELETE",
    "OPTIONS",
    "PROPFIND",
    "PROPPATCH",
    "REPORT",
    "MKCOL",
    "MKCALENDAR",
    "MOVE",
    "COPY",
):
    setattr(_RenamingProxyHandler, f"do_{_method}", _RenamingProxyHandler._forward)


class RenamingRadicaleServer(DAVServer):
    """
    Radicale behind a proxy that stores new items under another name than the one the client asked for
    """

    def __init__(self):
        super().__init__()
        self.radicale = RadicaleServer()
        self.proxy: ThreadingHTTPServer | None = None
        # (requested path, stored path) of each item stored under another name
        self.renamed: list[tuple[str, str]] = []

    @override
    def start(self) -> None:
        self.radicale.start()
        handler = type(
            "Handler",
            (_RenamingProxyHandler,),
            {"upstream_url": self.radicale.base_url, "renamed": self.renamed},
        )
        self.proxy = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=self.proxy.serve_forever, daemon=True).start()
        self.wait_for_server(self.readiness_url)

    @override
    def cleanup_test_environment(self) -> None:
        self.renamed.clear()
        super().cleanup_test_environment()

    @override
    def stop(self) -> None:
        if self.proxy:
            self.proxy.shutdown()
            self.proxy.server_close()
        self.radicale.stop()

    @property
    @override
    def base_url(self) -> str:
        assert self.proxy
        return f"http://127.0.0.1:{self.proxy.server_address[1]}"

    @property
    @override
    def readiness_url(self) -> str:
        return f"{self.base_url}/{self.username}/"

    @property
    @override
    def username(self) -> str:
        return self.radicale.username

    @property
    @override
    def password(self) -> str:
        return self.radicale.password
