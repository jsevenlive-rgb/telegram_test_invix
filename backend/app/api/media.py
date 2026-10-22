from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.services.s3 import get_object_bytes

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/{key:path}")
async def get_media(key: str):
    if not key or ".." in key:
        raise HTTPException(status_code=400, detail="Invalid key")
    try:
        data, content_type = get_object_bytes(key)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Not found") from exc
    return Response(
        content=data,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )
