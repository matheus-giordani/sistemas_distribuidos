from __future__ import annotations

import grpc

_METADATA_KEY = "x-api-key"


def metadata(api_key: str) -> tuple[tuple[str, str], ...]:
    """Helper to attach API key metadata to outgoing RPC calls."""
    return ((_METADATA_KEY, api_key),)


async def require_api_key(context: grpc.aio.ServicerContext, expected_api_key: str) -> None:
    """Abort the RPC if the provided metadata is missing or incorrect."""
    provided_key = None
    for key, value in context.invocation_metadata():
        if key.lower() == _METADATA_KEY:
            provided_key = value
            break

    if provided_key != expected_api_key:
        await context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid API key")


__all__ = ["metadata", "require_api_key"]
