# Use Python 3.10
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# --- INSTALL NODEJS (REQUIRED BY YT-DLP WIKI) ---
RUN apt-get update && \
    apt-get install -y ffmpeg nodejs git && \
    rm -rf /var/lib/apt/lists/*
# ------------------------------------------------

# Install requirements (This now includes yt-dlp[default])
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Start server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
