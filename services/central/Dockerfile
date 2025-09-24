FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/code

WORKDIR /code

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install debugpy

COPY services /code/services

EXPOSE 8000


CMD ["python3", "-m", "debugpy", "--listen", "0.0.0.0:5678", "-m", "uvicorn", "services.central.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
