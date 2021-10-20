FROM python:3.8
WORKDIR /swagger
COPY ./requirements.txt /swagger/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /swagger/requirements.txt
COPY main.py /swagger/
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
