# FROM directive instructing base image to build upon
# This could be used as a base instead: 
# https://hub.docker.com/r/nikolaik/python-nodejs
FROM python:3.10-slim-bookworm

# NOTE: requirements.txt not likely to change between dev builds
COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    netcat-openbsd \
    vim-tiny \
    jq \
    python3-dev \
    git \
    supervisor \
    curl && \
    apt-get upgrade -y && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /code/frontend

RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash - && \
    apt install -y nodejs

COPY /frontend/package*.json /code/frontend
RUN npm install

WORKDIR /code

# Sets the local timezone of the docker image
ARG TZ
ENV TZ ${TZ:-America/Detroit}
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# EXPOSE port 5000 to allow communication to/from server
EXPOSE 5000

# NOTE: project files likely to change between dev builds
COPY . .

CMD ["/usr/bin/supervisord", "-c", "/code/deploy/supervisor_docker.conf"]
# done!
