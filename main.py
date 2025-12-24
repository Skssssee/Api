from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
import yt_dlp
import aiohttp
import os

app = FastAPI()

COOKIE_FILE = "cookies.txt" if os.path.exists("cookies.txt") else None

YDL_OPTS_BASE = {
    "quiet": True,
    "nocheckcertificate": True,
    "geo_bypass": True,
    "cookiefile": COOKIE_FILE,
    "user_agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}

async def get_stream_link(url: str, audio: bool):
    ydl_opts = YDL_OPTS_BASE.copy()
    ydl_opts["format"] = "bestaudio/best" if audio else "bestvideo+bestaudio/best"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get("url")
    except Exception as e:
        print("YT-DLP ERROR:", e)
        return None

async def stream_generator(url: str):
    headers = {
        "User-Agent": YDL_OPTS_BASE["user_agent"]
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            async for chunk in resp.content.iter_chunked(8192):
                yield chunk

@app.get("/")
def home():
    return {"status": "online"}

@app.get("/audio")
async def audio(url: str):
    link = await get_stream_link(url, audio=True)
    if not link:
        return JSONResponse(status_code=500, content={"error": "Extraction failed"})
    return StreamingResponse(stream_generator(link), media_type="audio/mpeg")

@app.get("/download")
async def video(url: str):
    link = await get_stream_link(url, audio=False)
    if not link:
        return JSONResponse(status_code=500, content={"error": "Extraction failed"})
    return StreamingResponse(stream_generator(link), media_type="video/mp4")
