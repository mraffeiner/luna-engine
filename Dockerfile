FROM python:3.11-slim

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.in .
RUN pip install --no-cache-dir -r requirements.in

# Copy application code
COPY src ./src

# Expose the port the app runs on
EXPOSE 5003

# Command to run the application
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "5003"]