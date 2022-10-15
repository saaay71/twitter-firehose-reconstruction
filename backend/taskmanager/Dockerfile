FROM python:3.9-slim

COPY requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt

COPY src/snowflake /app/src/snowflake
COPY src /app/src

CMD ["python3", "/app/src/taskmanager.py"]