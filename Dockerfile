FROM python:3.11-slim

# Install system dependencies required for computer vision & image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code, sample photos, and baseline benchmark results
COPY src/ ./src/
COPY Sample-Photos/ ./Sample-Photos/
COPY results/ ./results/
COPY assets/ ./assets/
COPY interactive_prd/ ./interactive_prd/
COPY PRD_MERCHANT_MENU_IMAGE_PLATFORM.pdf ./
COPY PRD_MERCHANT_MENU_IMAGE_PLATFORM.md ./

# Cloud Run defaults (GOOGLE_CLOUD_PROJECT is injected at runtime via Cloud Run env / .env / ADC)
ARG GOOGLE_CLOUD_PROJECT=""
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}
ENV GOOGLE_CLOUD_LOCATION=global

EXPOSE 8080

# Launch FastAPI app matching local uvicorn runner
CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8080"]
