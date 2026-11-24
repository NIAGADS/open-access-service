import hashlib
import hmac

from fastapi import Request
from fastapi.responses import JSONResponse


async def verify_internal_proxy(request: Request, call_next):
    client_ip = request.headers.get("X-Client-IP")
    signature = request.headers.get("X-Client-IP-Signature")

    # Allow direct API requests without a proxy signature.
    if signature is None:
        return await call_next(request)

    if not client_ip:
        return JSONResponse(
            status_code=403,
            content={"detail": "Missing forwarded client IP"},
        )

    expected_signature = hmac.new(
        request.app.state.signing_secret,
        client_ip.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(
        signature.encode("utf-8"),
        expected_signature.encode("ascii"),
    ):
        return JSONResponse(
            status_code=403,
            content={"detail": "Invalid proxy signature"},
        )

    request.state.verified_client_ip = client_ip
    return await call_next(request)
