"""
/v1/chat/completions — the main proxy endpoint.
Accepts OpenAI-compatible requests, returns streaming or buffered responses.
"""

import json
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    Choice,
    Message,
    UsageInfo,
)
from app.services.auth import AuthResult, authenticate, bearer, check_model_access
from app.services.proxy_service import NoAvailableModelError, proxy_stream

router = APIRouter()


@router.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer),
    db: Session = Depends(get_db),
):
    auth = authenticate(credentials, db)
    check_model_access(auth, request.model)

    virtual_key_id = auth.virtual_key.id if auth.virtual_key else None

    try:
        if request.stream:
            return StreamingResponse(
                proxy_stream(request, virtual_key_id),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                },
            )
        else:
            # Buffer the stream and return a non-streaming response
            content = await _buffer_stream(request, virtual_key_id)
            return content

    except NoAvailableModelError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )


async def _buffer_stream(
    request: ChatCompletionRequest,
    virtual_key_id: str | None,
) -> ChatCompletionResponse:
    """Collect SSE chunks and assemble a non-streaming response."""
    full_content = []
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    finish_reason = "stop"
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"

    async for chunk in proxy_stream(request, virtual_key_id):
        if chunk.strip() == b"data: [DONE]" or chunk.strip() == b"data: [DONE]\n\n":
            continue
        if chunk.startswith(b"data:"):
            try:
                data = json.loads(chunk[5:].strip())
                for choice in data.get("choices", []):
                    delta = choice.get("delta", {})
                    if delta.get("content"):
                        full_content.append(delta["content"])
                    if choice.get("finish_reason"):
                        finish_reason = choice["finish_reason"]
                usage = data.get("usage") or {}
                if usage.get("prompt_tokens"):
                    prompt_tokens = usage["prompt_tokens"]
                if usage.get("completion_tokens"):
                    completion_tokens = usage["completion_tokens"]
                if usage.get("total_tokens"):
                    total_tokens = usage["total_tokens"]
            except Exception:
                pass

    if not total_tokens:
        total_tokens = prompt_tokens + completion_tokens

    return ChatCompletionResponse(
        id=completion_id,
        created=int(time.time()),
        model=request.model,
        choices=[
            Choice(
                message=Message(role="assistant", content="".join(full_content)),
                finish_reason=finish_reason,
            )
        ],
        usage=UsageInfo(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        ),
    )
