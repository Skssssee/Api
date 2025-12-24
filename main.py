import os
import uuid
import yt_dlp
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI()

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

COOKIE_FILE = "cookies.txt" if os.path.exists("cookies.txt") else None

YDL_OPTS = {
    "format": "bestaudio/best",
    "outtmpl": f"{DOWNLOAD_DIR}/%(id)s.%(ext)s",
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
            "player_client": ["web"]
        }
    },
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "192",
    }],
}

@app.get("/")
def home():
    return {"status": "online"}

@app.get("/audio")
def audio(url: str):
    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info["id"]
            file_path = f"{DOWNLOAD_DIR}/{video_id}.mp3"

        if not os.path.exists(file_path):
            return JSONResponse(
                status_code=500,
                content={"error": "Audio not created"}
            )

        size = os.path.getsize(file_path)
        if size < 50 * 1024:
            os.remove(file_path)
            return JSONResponse(
                status_code=500,
                content={"error": f"File too small ({size} bytes)"}
            )

        return FileResponse(
            file_path,
            media_type="audio/mpeg",
            filename=f"{video_id}.mp3"
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
