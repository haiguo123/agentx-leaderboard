FROM ghcr.io/astral-sh/uv:python3.13-bookworm

ENV AGENT_ID=019c0e01-6248-7f41-a72e-d51ee2ddfb99

RUN adduser agent
USER agent
WORKDIR /home/agent

COPY pyproject.toml uv.lock README.md ./
COPY src src

RUN \
    --mount=type=cache,target=/home/agent/.cache/uv,uid=1000 \
    uv sync --locked

ENTRYPOINT ["uv", "run", "src/server.py"]
CMD ["--host", "0.0.0.0"]
EXPOSE 9009