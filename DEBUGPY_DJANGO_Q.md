# Debugging Django-Q Background Tasks with debugpy

The `@debugpy_django_q` decorator allows you to attach a debugger to any Django-Q background task.

## Quick Start

### 1. Configure Environment

Add these to your `.env` file (or `.env.local` for local development):

```env
DEBUGPY_ENABLE=true
DEBUG_DJANGO_Q_PORT=5021
DEBUGPY_DJANGO_Q_TIMEOUT=30
```

See `.env.sample` for all available debugpy options.

### 2. Add Decorator to Your Task

```python
from backend.canvas_app_explorer.decorators import debugpy_django_q

@debugpy_django_q
def my_background_task(task_data):
    """Your background task logic here"""
    logger.info("Task is running")
```

### 3. Start the Worker

```bash
python manage.py qcluster
```

### 4. Connect Debugger in VS Code

A launch configuration already exists in `.vscode/launch.json`. Click "Run and Debug" → "Django-Q Debug" to attach to the debugger, then queue a task.

## How It Works

When a decorated task runs:
1. Debugpy starts listening on `DEBUG_DJANGO_Q_PORT`
2. The task waits up to `DEBUGPY_DJANGO_Q_TIMEOUT` seconds for a debugger to attach
3. Once attached (or timeout expires), the task executes normally

## Configuration Options

| Environment Variable | Default | Description |
|---|---|---|
| `DEBUGPY_ENABLE` | `false` | Enable debugpy for both web UI and django_q tasks |
| `DEBUG_DJANGO_Q_PORT` | (none) | Port for django_q debugging (required to enable) |
| `DEBUGPY_DJANGO_Q_TIMEOUT` | `30` | Seconds to wait for debugger attachment |

## Combining Decorators

```python
@debugpy_django_q
@log_execution_time
def my_background_task(task_data):
    """Task with both debugging and timing"""
    pass
```

Place `@debugpy_django_q` closest to the function definition.

## Notes

- Tasks won't hang—they continue after the timeout even without a debugger
- Only one task can be debugged at a time unless using different ports
- The decorator has minimal overhead when debugging is disabled
- Check worker logs for debugpy initialization messages
