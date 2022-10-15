FROM python:3.9-slim

COPY requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt

COPY src /app/src

EXPOSE 5000
WORKDIR /app/src

CMD ["flask", "run", "--host=0.0.0.0"]
