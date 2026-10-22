import re
import uuid


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[-\s]+", "-", text).strip("-")
    if not text:
        text = "shop"
    return f"{text[:40]}-{uuid.uuid4().hex[:8]}"
