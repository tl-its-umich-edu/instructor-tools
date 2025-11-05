#!/bin/bash
echo "starting qworker..."

# Wait for backend to be ready since supervisor will spawn all the 3 processes backend, qworker, and frontend same time
while [ ! -f /tmp/backend_ready ]; do
    echo 'qworker: Waiting for backend to be ready...'
    sleep 2
done

echo "qworker: Running"
rm /tmp/backend_ready
watchfiles --filter python 'python manage.py qcluster' /code/backend