FROM python:3.11-slim

WORKDIR /app

# Required bc pyvts is using opencv-python instead of opencv-python-headless
RUN apt-get update && apt-get install -y python3-opencv

COPY requirements.in .
RUN pip install --no-cache-dir -r requirements.in

COPY src ./src

EXPOSE 5007

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "5007"]