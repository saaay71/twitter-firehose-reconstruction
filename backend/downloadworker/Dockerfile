FROM python:3.9-slim

COPY requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt

COPY src /app/src

CMD ["python3", "/app/src/worker.py"]