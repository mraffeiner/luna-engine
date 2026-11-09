FROM python:3.11-slim

WORKDIR /app

COPY requirements.in .
RUN pip install --no-cache-dir -r requirements.in

COPY src ./src

EXPOSE 8005

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8005", "--ws-ping-interval", "20", "--ws-ping-timeout", "20"]