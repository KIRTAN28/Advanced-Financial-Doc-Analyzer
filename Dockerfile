FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port 8000 (Railway will inject a PORT env variable, but this is a fallback/convention)
EXPOSE 8000

# Command to run the application using uvicorn
CMD uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}
