from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from markdown_it import MarkdownIt
import bleach

MAX_BYTES = 50 * 1024

md = MarkdownIt("commonmark", {"html": False}).enable("table").enable("strikethrough")

ALLOWED_TAGS = [
    "a","abbr","acronym","b","blockquote","br","code","em","i","li","ol","p",
    "pre","strong","ul","h1","h2","h3","h4","h5","h6","hr","table","thead","tbody",
    "tr","th","td"
]
ALLOWED_ATTRS = {
    "a": ["href", "title", "rel", "target"],
    "abbr": ["title"],
    "acronym": ["title"],
    "th": ["colspan","rowspan"],
    "td": ["colspan","rowspan"],
}

class RenderIn(BaseModel):
    markdown: str
    strip_html: Optional[bool] = False

class RenderOut(BaseModel):
    html: str
    stats: dict
    sanitized: bool
    text: Optional[str] = None

app = FastAPI(title="Markdown → HTML Microservice", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["POST"], allow_headers=["*"]
)

@app.post("/render", response_model=RenderOut)
async def render_markdown(
    payload: RenderIn,
    request: Request,
    pretty: Optional[int] = Query(default=0, ge=0, le=1)
):
    raw = payload.markdown
    if raw is None:
        raise HTTPException(status_code=400, detail="missing 'markdown' field")
    if not isinstance(raw, str):
        raise HTTPException(status_code=400, detail="'markdown' must be a string")

    size = len(raw.encode("utf-8", "strict"))
    if size > MAX_BYTES:
        raise HTTPException(status_code=400, detail=f"markdown too large (max {MAX_BYTES} bytes)")

    try:
        html = md.render(raw)
    except Exception:
        raise HTTPException(status_code=400, detail="markdown parse error")

    clean = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
    clean = bleach.linkify(clean, callbacks=[bleach.callbacks.nofollow, bleach.callbacks.target_blank])

    resp = RenderOut(
        html=clean,
        stats={"chars_in": len(raw), "chars_out": len(clean)},
        sanitized=True
    )

    if payload.strip_html:
        resp.text = bleach.clean(clean, tags=[], strip=True)

    return resp

