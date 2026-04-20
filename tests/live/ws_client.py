"""Tiny aiohttp-based WebSocket client for talking to a live HA instance.

Authenticates with a long-lived access token and sends Home Assistant
WebSocket API messages.  Used by live tests to exercise home_tasks/* commands
the same way the Lovelace card does.

This is intentionally minimal — no message subscriptions, no event listening,
no reconnection.  Tests that need those features can extend it.
"""
from __future__ import annotations

import asyncio
from typing import Any

import aiohttp


class WSError(RuntimeError):
    """Raised when the HA WebSocket API returns an error response."""


class HAWebSocketClient:
    """Minimal HA WebSocket client used by live tests."""

    def __init__(self, url: str, token: str) -> None:
        # url may be http://host:8123 or http://supervisor/core
        self._url = url.rstrip("/")
        self._ws_url = self._url.replace("http://", "ws://").replace("https://", "wss://") + "/api/websocket"
        self._token = token
        self._session: aiohttp.ClientSession | None = None
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._next_id = 1

    async def connect(self) -> None:
        """Open the WebSocket and complete the auth handshake."""
        self._session = aiohttp.ClientSession()
        self._ws = await self._session.ws_connect(self._ws_url, heartbeat=30)

        hello = await self._ws.receive_json()
        if hello.get("type") != "auth_required":
            raise WSError(f"Expected auth_required, got {hello}")

        await self._ws.send_json({"type": "auth", "access_token": self._token})
        result = await self._ws.receive_json()
        if result.get("type") != "auth_ok":
            raise WSError(f"Auth failed: {result}")

    async def close(self) -> None:
        if self._ws is not None:
            await self._ws.close()
        if self._session is not None:
            await self._session.close()
        self._ws = None
        self._session = None

    async def __aenter__(self) -> "HAWebSocketClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def send_command(self, type_: str, **fields: Any) -> Any:
        """Send a WS command and return its `result` payload.

        Raises WSError if the response is unsuccessful.
        """
        if self._ws is None:
            raise WSError("WebSocket not connected — call connect() first")

        msg_id = self._next_id
        self._next_id += 1
        await self._ws.send_json({"id": msg_id, "type": type_, **fields})

        # The next message with our id is the response.  HA may interleave
        # event messages from other subscriptions, so loop until we find it.
        while True:
            msg = await asyncio.wait_for(self._ws.receive_json(), timeout=10)
            if msg.get("id") != msg_id:
                continue
            if msg.get("type") != "result":
                raise WSError(f"Unexpected message type: {msg}")
            if not msg.get("success", False):
                err = msg.get("error", {})
                raise WSError(f"{type_} failed: {err.get('code')} — {err.get('message')}")
            return msg.get("result")

    async def call_service(
        self,
        domain: str,
        service: str,
        service_data: dict | None = None,
        *,
        target: dict | None = None,
        return_response: bool = False,
    ) -> Any:
        """Convenience: call a HA service via the WS API.

        When return_response=True, the returned dict contains the service's
        response payload under the "service_response" key.
        """
        kwargs: dict[str, Any] = {
            "domain": domain,
            "service": service,
            "service_data": service_data or {},
        }
        if target is not None:
            kwargs["target"] = target
        if return_response:
            kwargs["return_response"] = True
        return await self.send_command("call_service", **kwargs)

    async def get_states(self) -> list[dict]:
        """Convenience: fetch all entity states."""
        return await self.send_command("get_states")

    async def refresh_entity(self, entity_id: str) -> None:
        """Force HA to re-fetch an entity's state from its underlying provider.

        Rich adapters (e.g. TodoistAdapter) talk to their provider's REST
        API directly, bypassing HA's own integration entity.  HA's entity
        therefore only learns about changes on its own polling cadence.
        Tests that want to see the provider's view right after a rich
        adapter wrote to it should call this first.
        """
        await self.call_service(
            "homeassistant", "update_entity",
            {"entity_id": entity_id},
        )

    async def get_provider_items(
        self,
        entity_id: str,
        *,
        status: str | None = None,
        refresh_first: bool = False,
    ) -> list[dict]:
        """Return the provider's own view of items on a todo entity.

        Calls HA's native ``todo.get_items`` service so we see what the
        provider (Google Tasks, Todoist, CalDAV, ...) actually reports —
        bypassing our overlay merge entirely.  This is how live tests
        verify that a reorder really reached the external system, rather
        than only landing in our local overlay.

        Pass refresh_first=True for rich-adapter providers (Todoist) whose
        integration entity lags behind direct API writes.
        """
        if refresh_first:
            await self.refresh_entity(entity_id)
            # give HA's coordinator a beat to finish the refresh
            await asyncio.sleep(2)

        service_data: dict[str, Any] = {}
        if status is not None:
            service_data["status"] = status
        result = await self.call_service(
            "todo", "get_items",
            service_data,
            target={"entity_id": entity_id},
            return_response=True,
        )
        response = result.get("response") or result.get("service_response") or {}
        return response.get(entity_id, {}).get("items", [])
