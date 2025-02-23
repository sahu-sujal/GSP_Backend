FROM python:3

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    libxrender1 libxext6 libfontconfig1 && \
    rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install -r requirements.txt

RUN  python3 manage.py migrate

EXPOSE 8080/tcp

CMD ["python3","manage.py","runserver","0.0.0.0:8080"]
