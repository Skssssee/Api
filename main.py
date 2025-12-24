import os
import yt_dlp
import aiohttp
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse

app = FastAPI()

# ─────────────────────────────────────
# COOKIES LOAD (FILE OR KOYEB SECRET)
# ─────────────────────────────────────

COOKIE_FILE = None

if "YT_COOKIES" in os.environ:
    with open("cookies.txt", "w", encoding="utf-8") as f:
        f.write(os.environ["YT_COOKIES"])
    COOKIE_FILE = "cookies.txt"
    print("✅ Cookies loaded from Koyeb secret")
elif os.path.exists("cookies.txt"):
    COOKIE_FILE = "cookies.txt"
    print("✅ Cookies loaded from file")
else:
    print("❌ Cookies NOT FOUND")

if COOKIE_FILE:
    print("📄 Cookies size:", os.path.getsize(COOKIE_FILE))

# ─────────────────────────────────────
# YT-DLP OPTIONS (WEB CLIENT ONLY)
# ─────────────────────────────────────

BASE_YDL_OPTS = {
    "quiet": True,
    "nocheckcertificate": True,
    "geo_bypass": True,
    "cookiefile": COOKIE_FILE,
    "extractor_args": {
        "youtube": {
            "player_client": ["web"]
        }
    },
    "user_agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ─────────────────────────────────────
# STREAM LINK FETCH
# ─────────────────────────────────────

async def get_stream_link(url: str, audio: bool):
    opts = BASE_YDL_OPTS.copy()
    opts["format"] = "bestaudio/best" if audio else "bestvideo+bestaudio/best"

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get("url")
    except Exception as e:
        print("❌ YT-DLP ERROR:", e)
        return None

# ─────────────────────────────────────
# STREAM GENERATOR
# ─────────────────────────────────────

async def stream_generator(url: str):
    headers = {
        "User-Agent": BASE_YDL_OPTS["user_agent"]
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return
            async for chunk in resp.content.iter_chunked(8192):
                yield chunk

# ─────────────────────────────────────
# ROUTES
# ─────────────────────────────────────

@app.get("/")
def home():
    return {"status": "online"}

@app.get("/audio")
async def audio(url: str):
    print("🎵 Audio Request:", url)
    link = await get_stream_link(url, audio=True)
    if not link:
        return JSONResponse(status_code=500, content={"error": "Extraction failed"})
    return StreamingResponse(stream_generator(link), media_type="audio/mpeg")

@app.get("/download")
async def video(url: str):
    print("🎬 Video Request:", url)
    link = await get_stream_link(url, audio=False)
    if not link:
        return JSONResponse(status_code=500, content={"error": "Extraction failed"})
    return StreamingResponse(stream_generator(link), media_type="video/mp4")
