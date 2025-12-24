# Use Python 3.10
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# --- CRITICAL FIX FOR "N CHALLENGE FAILED" ---
# We MUST install 'nodejs' so yt-dlp can solve the speed puzzles
RUN apt-get update && \
    apt-get install -y ffmpeg nodejs git && \
    rm -rf /var/lib/apt/lists/*
# ---------------------------------------------

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
