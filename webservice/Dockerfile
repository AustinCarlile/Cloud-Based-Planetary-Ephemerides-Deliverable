# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8000 to the outside world
EXPOSE 8000

# Run the FastAPI app using Uvicorn
CMD ["uvicorn", "isdAPI:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
