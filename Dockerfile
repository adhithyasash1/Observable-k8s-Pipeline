# ---- Builder Stage ----
FROM python:3.10-slim AS builder
WORKDIR /app
RUN pip install poetry
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false && \
    poetry install --no-root --only main

# ---- Final Stage ----
FROM python:3.10-slim
WORKDIR /app
RUN useradd -m -u 1000 appuser
USER appuser

# Copy installed packages and executables from the builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy your application code and model
COPY ./app/main.py .
COPY ./app/model.joblib .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
