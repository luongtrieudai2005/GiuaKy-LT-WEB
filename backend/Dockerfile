# ============================================================
# Dockerfile — FastAPI backend
#
# Multi-stage build is overkill for this project size.
# We use a single slim image to keep the final image small.
# ============================================================

# Use official Python slim image (smaller than full python:3.11)
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# ============================================================
# Install dependencies first (before copying source code).
# This layer is cached by Docker — if requirements.txt has not
# changed, Docker reuses this layer instead of reinstalling.
# Copying requirements.txt separately is a deliberate optimization.
# ============================================================
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the source code
COPY . .

# Expose port 8000 (informational — actual binding is in docker-compose)
EXPOSE 8000

# Start the FastAPI app with uvicorn
# --host 0.0.0.0 means listen on all interfaces inside the container
# --reload is for development only — remove in production
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]