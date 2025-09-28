from __future__ import annotations

from datetime import datetime, timezone

from google.protobuf.timestamp_pb2 import Timestamp


def utc_now() -> datetime:
    """Return a timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def to_timestamp(dt: datetime) -> Timestamp:
    """Convert a datetime into a protobuf Timestamp in UTC."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    ts = Timestamp()
    ts.FromDatetime(dt)
    return ts


def from_timestamp(ts: Timestamp) -> datetime:
    """Convert a protobuf Timestamp into a timezone-aware UTC datetime."""
    return ts.ToDatetime().astimezone(timezone.utc)


__all__ = ["utc_now", "to_timestamp", "from_timestamp"]
