FROM python:3.12.4

RUN pip install -U pip
RUN pip install pipenv 

WORKDIR /app

COPY [ "Pipfile", "Pipfile.lock", "./" ]

RUN pipenv install --system --deploy

COPY [ "server.py", "./" ]

EXPOSE 5000

ENTRYPOINT [ "gunicorn", "server:app", "-b", "0.0.0.0:5000", "-w", "4" ]