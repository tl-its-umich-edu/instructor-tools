#!/bin/bash
echo "starting qworker..."

# Wait for backend to be ready since supervisor will spawn all the 3 processes backend, qworker, and frontend same time
while [ ! -f /tmp/backend_ready ]; do
    echo 'qworker: Waiting for backend to be ready...'
    sleep 2
done

# this is to ensure that the backend/DB is fully ready before starting the qworker
echo "qworker: Backend is ready, starting qworker..."

# Optional Django Q worker debugging with debugpy on port 5021.
QWORKER_DEBUGPY_ENABLE="${QWORKER_DEBUGPY_ENABLE:-false}"
QWORKER_DEBUGPY_PORT="${QWORKER_DEBUGPY_PORT:-5021}"
QWORKER_DEBUGPY_WAIT_FOR_CLIENT="${QWORKER_DEBUGPY_WAIT_FOR_CLIENT:-false}"

QCLUSTER_CMD="python manage.py qcluster"
if [ "${QWORKER_DEBUGPY_ENABLE}" = "true" ]; then
    echo "qworker: Debugpy enabled on 0.0.0.0:${QWORKER_DEBUGPY_PORT}"
    DEBUGPY_ARGS="python -m debugpy --listen 0.0.0.0:${QWORKER_DEBUGPY_PORT}"
    if [ "${QWORKER_DEBUGPY_WAIT_FOR_CLIENT}" = "true" ]; then
        DEBUGPY_ARGS="${DEBUGPY_ARGS} --wait-for-client"
        echo "qworker: Waiting for debugger client before starting qcluster"
    fi
    QCLUSTER_CMD="${DEBUGPY_ARGS} manage.py qcluster"
fi

if [ "${RUN_QWORKER_DEV_MODE:-false}" = "true" ]; then
    echo "qworker: Running in DEV mode"
    rm /tmp/backend_ready
    watchfiles --filter python  ${PYTHON_FLAGS} "${QCLUSTER_CMD}" /code/backend
else
    echo "qworker: Running in PROD mode"
    ${QCLUSTER_CMD}
fi