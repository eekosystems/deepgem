FROM python:3.12-slim

# Gemini CLI
RUN apt-get update && apt-get install -y nodejs npm git && rm -rf /var/lib/apt/lists/*
RUN npm i -g @google/gemini-cli

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir build && python -m build && pip install --no-cache-dir dist/*.whl

ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["deepgem"]
