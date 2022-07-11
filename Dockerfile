FROM python:3.9

# Install app
ADD Makefile requirements.txt /speid/
WORKDIR /speid
RUN pip install -qU pip
RUN pip install -q gunicorn
RUN make install

# Add repo contents to image
ADD . /speid/

ENV PORT 3000
EXPOSE $PORT
