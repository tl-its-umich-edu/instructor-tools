# Global build arguments for version control
ARG DEBIAN_VERSION=bookworm
ARG NODE_VERSION=20
ARG MARIADB_VERSION=11.4

# node-build stage

FROM node:${NODE_VERSION}-${DEBIAN_VERSION}-slim AS node-build
WORKDIR /build/

COPY frontend .
RUN npm install

RUN npm run build:frontend

FROM python:3.13-slim-${DEBIAN_VERSION}

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

# Use the official MariaDB mirrors directly (No script, no Cloudflare issues)
# Version controlled via build arguments: DEBIAN_VERSION and MARIADB_VERSION
# 1. Install dependencies needed to add the repository
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    gnupg \
    && mkdir -p /etc/apt/keyrings \
    # 2. Add the MariaDB GPG Key
    && curl -fsSL https://mariadb.org/mariadb_release_signing_key.asc | gpg --dearmor -o /etc/apt/keyrings/mariadb.gpg \
    # 3. Define the repository using build arguments for flexibility
    && echo "deb [arch=amd64,arm64 signed-by=/etc/apt/keyrings/mariadb.gpg] https://deb.mariadb.org/${MARIADB_VERSION}/debian ${DEBIAN_VERSION} main" > /etc/apt/sources.list.d/mariadb.list \
    # 4. Update and install the library
    && apt-get update && apt-get install -y --no-install-recommends \
    libmariadb-dev \
    # 5. Cleanup to keep the image slim
    && rm -rf /var/lib/apt/lists/*

# Node.js is installed from NodeSource repository using the NODE_VERSION build argument

# 1. Add the Nodesource GPG Key
RUN curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    # 2. Add the Node.js Repository for the configured version
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_${NODE_VERSION}.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
    # 3. Update and install
    && apt-get update && apt-get install -y nodejs --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /code

# Copy only what is needed into /code/
COPY backend ./backend
COPY templates ./templates
COPY manage.py start_backend.sh start_worker.sh ./

COPY --from=node-build /build/bundles ./frontend/bundles 
COPY --from=node-build /build/webpack-stats.json ./frontend/
COPY --from=node-build /build/node_modules ./frontend/node_modules

# Sets the local timezone of the docker image
ARG TZ
ENV TZ ${TZ:-America/Detroit}
# By default run a build that won't have a running frontend process (only used in dev)
ARG RUN_FRONTEND
ENV RUN_FRONTEND ${RUN_FRONTEND:-false} 

# Run collectstatic *only* if RUN_FRONTEND is not true
RUN if [ "$RUN_FRONTEND" != "true" ]; then \
      echo "Running collectstatic during build..."; \
      python manage.py collectstatic --noinput; \
    else \
      echo "Skipping collectstatic (RUN_FRONTEND=$RUN_FRONTEND)"; \
    fi

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# EXPOSE port 5000 to allow communication to/from server
EXPOSE 5000

# NOTE: project files likely to change between dev builds
COPY . .

CMD ["/usr/bin/supervisord", "-c", "/code/deploy/supervisor_docker.conf"]
# done!