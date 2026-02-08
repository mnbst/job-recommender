# マルチステージビルドでuvを最終イメージから除外
FROM python:3.11-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY app/ ./app/
COPY .streamlit/ ./.streamlit/

# Install the project
RUN uv pip install --no-deps -e .

# Final stage - runtime only
FROM python:3.11-slim

WORKDIR /app

# Copy only the virtual environment and app
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/app /app/app
COPY --from=builder /app/.streamlit /app/.streamlit

# Use the virtual environment directly
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8501

CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.baseUrlPath=/app"]
