# Pull official base image
FROM python:3.8-buster
# Set work directory
WORKDIR /usr/src/app
# Install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt
# Set database initialization
COPY ./initial_data/*.sql /usr/src/app/initial_data
ADD initial_data/setup.sql /usr/src/app/initial_data
# Copy project
COPY . /usr/src/app/
EXPOSE 5000
# Permissions
RUN chmod a+r initial_data/*
RUN chmod u+x app/docker-entrypoint.sh
ENTRYPOINT ["sh", "app/docker-entrypoint.sh"]