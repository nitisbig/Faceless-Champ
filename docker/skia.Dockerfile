FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 MPLCONFIGDIR=/tmp/matplotlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libfontconfig1 libgl1 libegl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . /app
RUN python -m pip install --no-cache-dir '.[skia]' './facelesschamp-kit[skia]' './facelesschamp-agent[skia]'
RUN useradd --create-home --uid 10001 renderer && mkdir -p /output && chown renderer:renderer /output
USER renderer
WORKDIR /app
CMD ["python", "examples/skia_showcase.py", "--output", "/output/preview.mp4"]
