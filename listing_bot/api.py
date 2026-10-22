import hmac
from typing import Awaitable, Callable

from aiohttp import web

from .bot import Notifier
from .collector import Collector
from .config import Settings
from .models import Announcement
from .storage import Storage

Handler = Callable[[web.Request], Awaitable[web.StreamResponse]]


def create_app(settings: Settings, storage: Storage, collector: Collector, notifier: Notifier) -> web.Application:
    @web.middleware
    async def auth(request: web.Request, handler: Handler) -> web.StreamResponse:
        if request.path.startswith("/api/") and settings.api_token:
            token = request.headers.get("X-Api-Token", "")
            if not hmac.compare_digest(token, settings.api_token):
                raise web.HTTPUnauthorized()
        return await handler(request)

    async def health(_: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    async def collect(_: web.Request) -> web.Response:
        items, errors = await collector.collect()
        return web.json_response(
            {"count": len(items), "items": [item.to_dict() for item in items], "errors": errors}
        )

    async def broadcast(request: web.Request) -> web.Response:
        try:
            data = await request.json()
        except ValueError:
            raise web.HTTPBadRequest(text="invalid json")
        item = await storage.get(data["uid"]) if data.get("uid") else None
        if item is None:
            try:
                item = Announcement.from_dict(data)
            except (KeyError, TypeError, ValueError):
                raise web.HTTPBadRequest(text="invalid announcement")
        sent = await notifier.broadcast(item)
        return web.json_response({"uid": item.uid, "sent": sent})

    async def latest(request: web.Request) -> web.Response:
        limit = min(int(request.query.get("limit", "10")), 100)
        items = await storage.latest(limit)
        return web.json_response({"items": [item.to_dict() for item in items]})

    app = web.Application(middlewares=[auth])
    app.router.add_get("/health", health)
    app.router.add_post("/api/collect", collect)
    app.router.add_post("/api/broadcast", broadcast)
    app.router.add_get("/api/latest", latest)
    return app
