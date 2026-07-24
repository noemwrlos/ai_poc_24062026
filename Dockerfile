FROM python:3.14.4-slim-trixie AS base

RUN apt-get update -qy \
    && apt-get install -qyy \
    -o APT::Install-Recommends=false \
    -o APT::Install-Suggests=false \
    build-essential \
    ca-certificates

COPY --from=ghcr.io/astral-sh/uv:0.11.31 /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON=python3.14.4 \
    UV_PROJECT_ENVIRONMENT=/akmf

COPY pyproject.toml /_lock/
COPY uv.lock /_lock/

RUN cd /_lock && uv sync --group dev --group test --locked --no-install-project
##########################################################################
FROM python:3.14.4-slim-trixie

ENV PATH=/akmf/bin:$PATH

RUN groupadd -r akmf
RUN useradd -r -d /akmf -g akmf -N akmf

COPY --from=base --chown=akmf:akmf /akmf /akmf

USER akmf
WORKDIR /akmf
COPY /app/ app/
COPY .env app/
COPY pyproject.toml /akmf/pyproject.toml