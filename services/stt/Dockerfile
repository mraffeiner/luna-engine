FROM python:3.11-slim

WORKDIR /app

COPY requirements.in .

# ffmpeg decodes the uploaded audio (webm/mp3/wav) before Silero VAD
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.in

COPY src ./src

EXPOSE 5003

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "5003"]