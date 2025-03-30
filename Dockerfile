FROM python:3.11-slim

WORKDIR /app

COPY requirements.in .

# Install system dependencies required for torchaudio (soundfile and ffmpeg backends)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.in

COPY src ./src

EXPOSE 5003

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "5003"]