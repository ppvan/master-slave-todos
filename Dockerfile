FROM python:3.8.2

WORKDIR /todos

COPY ./requirements.txt .

RUN pip install -r requirements.txt

COPY ./app ./app
COPY ./alembic ./alembic
COPY ./alembic.ini ./alembic.ini

COPY ./.env ./.env

# RUN alembic upgrade head

EXPOSE 80


CMD [ "uvicorn", "app.main:app", "--port", "80", "--host", "0.0.0.0" ]
# CMD [ "uvicorn", "app.main:app", "--reload", "--port", "80", "--host", "0.0.0.0" ]