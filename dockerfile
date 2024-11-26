# Dockerfile

# Use Python 3.10.5 slim base image
ARG PYTHON_VERSION=3.10.5
FROM python:${PYTHON_VERSION}-slim

# Disable .pyc files and ensure logs are not buffered
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Create a non-privileged user to run the app
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Switch to the non-privileged user
USER appuser

# Copy the application source code to the container
COPY . .

# Expose the port that the FastAPI app will run on
EXPOSE 8000

# Run the FastAPI app using Uvicorn
CMD ["uvicorn", "app.main:app", "--host=0.0.0.0", "--port=8000"]