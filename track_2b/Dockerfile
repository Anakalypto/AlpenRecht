FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt pytest
COPY src/ src/
COPY data/ data/
COPY tests/ tests/
COPY eval/*.py eval/*.json eval/
ENV PYTHONPATH=/app/src PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8 HOST=0.0.0.0 PORT=5055
EXPOSE 5055
CMD ["python", "-m", "alpenrecht", "serve"]
