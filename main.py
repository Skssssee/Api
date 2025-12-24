
import os
import yt_dlp
import aiohttp
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse

app = FastAPI()

# ─────────────────────────────────────
# COOKIES
# ─────────────────────────────────────

COOKIE_FILE = None

if os.path.exists("cookies.txt"):
    COOKIE_FILE = "cookies.txt"
    print("✅ Cookies loaded from file")
    print("📄 Cookies size:", os.path.getsize(COOKIE_FILE))
else:
    print("❌ Cookies not found")

# ─────────────────────────────────────
# YT-DLP OPTIONS (ANTI-SABR)
# ─────────────────────────────────────

BASE_YDL_OPTS = {
    "quiet": True,
    "nocheckcertificate": True,
    "geo_bypass": True,
    "cookiefile": COOKIE_FILE,
    "user_agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "extractor_args": {
        "youtube": {
            # VERY IMPORTANT
            "player_client": ["web", "mweb"],
            "skip": ["dash", "hls"]   # 🚫 SABR / adaptive streams
        }
    },
    "format_sort": ["res", "codec:h264", "br"],
}

# ─────────────────────────────────────
# GET STREAM LINK
# ─────────────────────────────────────

async def get_stream_link(url: str, audio: bool):
    opts = BASE_YDL_OPTS.copy()

    if audio:
        # progressive audio only
        opts["format"] = "bestaudio[acodec!=none]/best"
    else:
        # progressive mp4 only
        opts["format"] = "best[ext=mp4]/best"

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if "url" in info:
                return info["url"]

            # fallback for formats
            for f in info.get("formats", []):
                if f.get("url"):
                    return f["url"]

            return None

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
        return JSONResponse(status_code=500, content={"error": "No audio stream"})
    return StreamingResponse(stream_generator(link), media_type="audio/mpeg")

@app.get("/download")
async def video(url: str):
    print("🎬 Video Request:", url)
    link = await get_stream_link(url, audio=False)
    if not link:
        return JSONResponse(status_code=500, content={"error": "No video stream"})
    return StreamingResponse(stream_generator(link), media_type="video/mp4")
