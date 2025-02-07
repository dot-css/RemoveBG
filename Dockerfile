FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y libgl1

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app
WORKDIR /app

# Run the application
CMD ["python", "app.py"]