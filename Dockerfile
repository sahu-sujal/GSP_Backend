FROM python:3

COPY . .

RUN python3 -m pip install -r requirements.txt

RUN  python3 manage.py migrate

EXPOSE 8080/tcp

CMD ["python3","manage.py","runserver","0.0.0.0:8080"]