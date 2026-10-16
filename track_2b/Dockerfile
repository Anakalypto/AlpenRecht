FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt pytest==9.1.1
COPY src/ src/
COPY data/ data/
COPY tests/ tests/
COPY eval/*.py eval/*.json eval/
ENV PYTHONPATH=/app/src PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8 HOST=0.0.0.0 PORT=5055
EXPOSE 5055
# Python as PID 1 ignores SIGTERM, so docker stop waited 10 s and then killed it; SIGINT stops the server cleanly
STOPSIGNAL SIGINT
CMD ["python", "-m", "alpenrecht", "serve"]
