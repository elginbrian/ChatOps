FROM python:3.9-slim as builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir=/app/wheelhouse -r requirements.txt

FROM python:3.9-slim
WORKDIR /app
COPY --from=builder /app/wheelhouse /wheelhouse
RUN pip install --no-cache /wheelhouse/*
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]