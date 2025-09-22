# Simple Dockerfile for deployment
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
ENV PORT=8080
EXPOSE 8080
CMD ["bash", "run.sh"]
