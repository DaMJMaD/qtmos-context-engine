from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from mimetypes import guess_type
from typing import Any

from .ahk_policy_bridge import publish_ahk_policy_hook
from .models import dump_json
from .paths import PROJECT_ROOT
from .reporting import build_report_payload, load_report_payload
from .showcase import build_showcase_catalog
from .surface import append_surface_and_cycle, load_previous_surface
from .web import append_web_and_cycle, load_previous_web


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = dump_json(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
    handler.end_headers()
    handler.wfile.write(body)


def _file_response(handler: BaseHTTPRequestHandler, status: int, path: str) -> None:
    file_path = PROJECT_ROOT / path
    if not file_path.exists():
        _json_response(handler, HTTPStatus.NOT_FOUND, {"error": f"Missing file: {file_path}"})
        return
    body = file_path.read_bytes()
    content_type = guess_type(str(file_path))[0] or "application/octet-stream"
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class QTMoSBridgeHandler(BaseHTTPRequestHandler):
    server_version = "QTMoSAlphaBridge/0.1"

    def do_GET(self) -> None:  # noqa: N802
        clean_path = self.path.split("?", 1)[0]
        if clean_path in {"/alpha/report", "/alpha/report.json"}:
            _json_response(self, HTTPStatus.OK, load_report_payload())
            return
        if clean_path in {"/alpha/showcase.json"}:
            _json_response(self, HTTPStatus.OK, build_showcase_catalog())
            return
        if clean_path in {"/alpha/showcase", "/alpha/showcase/"}:
            _file_response(self, HTTPStatus.OK, "hosts/trust-console/showcase.html")
            return
        if clean_path in {"/", "/index.html", "/alpha", "/alpha/", "/alpha/console", "/alpha/console/"}:
            _file_response(self, HTTPStatus.OK, "hosts/trust-console/index.html")
            return
        if clean_path == "/favicon.ico":
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
            return
        _json_response(self, HTTPStatus.NOT_FOUND, {"error": f"Unknown path: {self.path}"})

    def do_OPTIONS(self) -> None:  # noqa: N802
        _json_response(self, HTTPStatus.NO_CONTENT, {})

    def do_POST(self) -> None:  # noqa: N802
        content_length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(content_length) if content_length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except Exception as exc:
            _json_response(
                self,
                HTTPStatus.BAD_REQUEST,
                {"error": f"Invalid JSON payload: {exc}"},
            )
            return

        try:
            if self.path == "/alpha/web-observe":
                result = self._handle_web_observe(payload)
            elif self.path == "/alpha/surface-observe":
                result = self._handle_surface_observe(payload)
            else:
                _json_response(
                    self,
                    HTTPStatus.NOT_FOUND,
                    {"error": f"Unknown path: {self.path}"},
                )
                return
        except Exception as exc:
            _json_response(
                self,
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": str(exc)},
            )
            return

        _json_response(self, HTTPStatus.OK, result)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _handle_web_observe(self, payload: dict[str, Any]) -> dict[str, Any]:
        previous_surface = load_previous_surface()
        linked_surface = payload.get("linked_surface") or {}
        if not linked_surface and previous_surface:
            linked_surface = {
                "surface_id": previous_surface.get("surface_id"),
                "process_name": previous_surface.get("process_name"),
                "window_title": previous_surface.get("window_title"),
            }

        result = append_web_and_cycle(
            host=payload.get("host", "browser-observer"),
            workspace=payload.get("workspace", str(PROJECT_ROOT)),
            session=payload.get("session", "chrome-active"),
            observer_id=payload.get("observer_id", "chrome-extension"),
            browser=payload.get("browser", "chromium"),
            url=payload.get("url", ""),
            title=payload.get("title", ""),
            text_snippet=payload.get("text_snippet", ""),
            tab_id=int(payload.get("tab_id", 0) or 0),
            window_id=int(payload.get("window_id", 0) or 0),
            mutated=bool(payload.get("mutated", False)),
            visible=bool(payload.get("visible", True)),
            linked_surface=linked_surface,
            candidate_surface=previous_surface,
            previous_web=load_previous_web(),
        )
        report = build_report_payload(result["state"], result["tags"], result["busydawg"])
        ahk_hook = publish_ahk_policy_hook(report)
        return {
            "ok": True,
            "event_id": result["event"]["id"],
            "kind": result["event"]["type"],
            "trust_status": result["tags"].get("trust_status"),
            "active_web": result["state"].get("active_web"),
            "ahk_hook": ahk_hook,
        }

    def _handle_surface_observe(self, payload: dict[str, Any]) -> dict[str, Any]:
        observation = payload.get("surface_observation") or {}
        result = append_surface_and_cycle(
            host=payload.get("host", "surface-observer"),
            workspace=payload.get("workspace", str(PROJECT_ROOT)),
            session=payload.get("session", "default"),
            observer_id=payload.get("observer_id", "external-surface-observer"),
            host_kind=payload.get("host_kind", "desktop"),
            label=payload.get("label", "active_surface"),
            observation=observation,
            previous_surface=load_previous_surface(),
        )
        report = build_report_payload(result["state"], result["tags"], result["busydawg"])
        ahk_hook = publish_ahk_policy_hook(report)
        return {
            "ok": True,
            "event_id": result["event"]["id"],
            "kind": result["event"]["type"],
            "trust_status": result["tags"].get("trust_status"),
            "active_surface": result["state"].get("active_surface"),
            "ahk_hook": ahk_hook,
        }


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    server = ThreadingHTTPServer((host, port), QTMoSBridgeHandler)
    print(f"QTMoS Alpha HTTP bridge listening on http://{host}:{port}")
    print("POST /alpha/web-observe or /alpha/surface-observe")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
