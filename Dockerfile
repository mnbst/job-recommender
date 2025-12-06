FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies without creating a venv and omit dev tools
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --without dev

# Copy application code
COPY . .

EXPOSE 8501

CMD ["poetry", "run", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
