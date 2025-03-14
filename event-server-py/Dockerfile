FROM python:3.13-slim

# COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN apt update && apt install -y wget

RUN wget -qO- https://astral.sh/uv/install.sh | sh

COPY . /app

WORKDIR /app
RUN /root/.local/bin/uv sync --frozen --no-cache

CMD ["/app/.venv/bin/fastapi", "run", "app/main.py", "--port", "80", "--host", "0.0.0.0"]
