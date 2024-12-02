# node-build stage

FROM node:20-slim AS node-build
WORKDIR /build/

COPY frontend .
RUN npm install

RUN npm run build:frontend

FROM python:3.10-slim

# NOTE: requirements.txt not likely to change between dev builds
COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    netcat-openbsd \
    vim-tiny \
    jq \
    python3-dev \
    git \
    supervisor \
    curl \
    pkg-config && \
    apt-get upgrade -y && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*

# Install MariaDB from the mariadb repository rather than using Debians 
# https://mariadb.com/kb/en/mariadb-package-repository-setup-and-usage/
RUN curl -LsS https://r.mariadb.com/downloads/mariadb_repo_setup | bash && \
apt install -y --no-install-recommends libmariadb-dev

RUN pip install --no-cache-dir -r requirements.txt

RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
apt install -y nodejs

WORKDIR /code

# Copy only what is needed into /code/
COPY backend ./backend
COPY templates ./templates
COPY manage.py start_backend.sh ./

COPY --from=node-build /build/bundles ./frontend/bundles 
COPY --from=node-build /build/webpack-stats.json ./frontend/
COPY --from=node-build /build/node_modules ./frontend/node_modules



# Sets the local timezone of the docker image
ARG TZ
ENV TZ ${TZ:-America/Detroit}
ENV RUN_FRONTEND ${RUN_FRONTEND:-false} 
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# EXPOSE port 5000 to allow communication to/from server
EXPOSE 5000

# NOTE: project files likely to change between dev builds
COPY . .

CMD ["/usr/bin/supervisord", "-c", "/code/deploy/supervisor_docker.conf"]
# done!