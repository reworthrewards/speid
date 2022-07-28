FROM python:3.9

# Install app
ADD Makefile requirements.txt /speid/
WORKDIR /speid
RUN pip install -qU pip
RUN pip install -q gunicorn
RUN make install

# Add repo contents to image
ADD . /speid/

ENV PORT 80
EXPOSE $PORT

CMD celery -A speid.tasks.celery worker -D --loglevel=info -c 5 && \
    gunicorn --access-logfile=- --error-logfile=- --bind=0.0.0.0:80 --workers=${SPEID_WORKERS:-5} speid:app

