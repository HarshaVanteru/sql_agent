"""Shared SQLAlchemy engine cache.

An Engine owns a connection pool and is meant to be long-lived. Creating one per
request builds a fresh pool whose connections are only closed once the Engine is
garbage collected, so pools accumulate while requests are in flight.

Caching is safe here because a stored connection is immutable: there is no
update endpoint, only create and delete, so a cached engine's URL can never go
stale.
"""
from collections import OrderedDict
from threading import Lock

import logfire
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.core.config import settings

ENGINE_CACHE_SIZE = settings.ENGINE_CACHE_SIZE

_engines: "OrderedDict[str, Engine]" = OrderedDict()
_lock = Lock()


def get_engine(url: str, connect_args: dict | None = None) -> Engine:
    """Return a pooled Engine for `url`, creating it on first use.

    Keyed on the URL alone: `connect_args` comes from the dialect, so the same
    URL always asks for the same ones.
    """
    with _lock:
        engine = _engines.get(url)
        if engine is not None:
            _engines.move_to_end(url)
            return engine

        # pool_pre_ping: a cached pool outlives the server's idle timeout, so
        # connections must be checked for liveness before being handed out.
        # pool_recycle: and a connection the far end quietly dropped hours ago
        # should be replaced rather than pinged forever.
        engine = create_engine(
            url,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=1800,
            connect_args=connect_args or {},
        )
        _engines[url] = engine

        while len(_engines) > ENGINE_CACHE_SIZE:
            _, evicted = _engines.popitem(last=False)
            evicted.dispose()
            logfire.info(
                "Disposed least-recently-used engine (cache limit {cache_size})",
                cache_size=ENGINE_CACHE_SIZE,
            )

        return engine
