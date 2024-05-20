FROM python:3.12-slim

RUN pip install -U uv

COPY . .

RUN uv venv && uv pip install -U --system -r requirements.txt