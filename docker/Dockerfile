FROM python:3.12-slim AS builder
WORKDIR /build
RUN python -m venv /venv
ENV PATH=/venv/bin:$PATH
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim AS runtime
WORKDIR /app
ENV HF_HOME=/app/.cache \
    PATH=/venv/bin:$PATH

COPY --from=builder /venv /venv
COPY app/ ./app/

# Pre-download the embedding model so the container needs no network at runtime
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

RUN groupadd --system covenant \
    && useradd --system --gid covenant covenant \
    && chown -R covenant:covenant /app

USER covenant
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
