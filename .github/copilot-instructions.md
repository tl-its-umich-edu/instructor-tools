# Instructor Tools - AI Coding Agent Instructions

## Project Overview
A Django + React application for managing Canvas LTI tools and generating alt text for course images using AI. The app runs as an LTI 1.3 tool embedded in Canvas and provides two main features: (1) Tool discovery and navigation management, (2) Alt text generation for course content via background tasks.

## Architecture

### Backend (Django 4.2)
- **Framework**: Django with Django REST Framework (DRF) for API endpoints
- **Database**: MySQL 8 (configured in `docker-compose.yml`)
- **Key Apps**: `canvas_app_explorer` (main), `canvas_oauth` (Canvas OAuth), others in settings.py
- **Authentication**: LTI 1.3 launch (PyLTI1p3) + OAuth for Canvas API access
- **Background Jobs**: django-q2 with Django ORM broker; workers configured via `Q_CLUSTER_*` env vars
- **Entry Point**: `backend/settings.py` for Django config; `manage.py` for CLI

### Frontend (React + TypeScript)
- **Build**: Webpack with separate dev/prod configs in `frontend/webpack/`
- **Framework**: React 18 with React Query for data fetching, React Router for navigation
- **Styling**: Material-UI (MUI) with Emotion
- **Watch Mode**: Runs in Docker container alongside backend during development
- **Output**: Bundles managed by `webpack-loader` Django app

### Data Flow
1. **LTI Launch**: Canvas → PyLTI1p3 login/launch endpoints → Session setup with course_id, user data
2. **API Calls**: React frontend → DRF endpoints (`/api/lti_tools/`, `/api/alt-text/*`) with session auth
3. **Canvas Integration**: Views use `DjangoCourseLtiManagerFactory` to create authenticated Canvas API clients
4. **Background Tasks**: Views enqueue tasks with `django_q.tasks.async_task()`; workers process via django-q2 cluster

## Key Patterns & Conventions

### Views & Serializers
- Use ViewSets with DRF's `LoggingMixin` to auto-log API requests with course context
- Extract session data (`request.session['course_id']`, etc.) early; return 400 if missing
- Catch Canvas API exceptions and convert to HTTP responses via `CanvasHTTPError`
- Example: [backend/canvas_app_explorer/views.py](backend/canvas_app_explorer/views.py#L43-L61)

### LTI Authentication Flow
- Login endpoint validates LTI claims; launch endpoint creates user session
- OAuth token stored in session for Canvas API calls; refreshed as needed in `canvas_oauth`
- All endpoints require `SessionAuthentication` + `IsAuthenticated` permissions

### Models & Database
- Use custom validators (e.g., `MaxLengthIgnoreHTMLValidator`) for HTML fields
- File uploads use `db_file_storage` with database-backed storage
- `CourseScan` model tracks background task status; `ContentItem`/`ImageItem` store parsed content
- Migrations in `backend/canvas_app_explorer/migrations/` and `backend/canvas_oauth/migrations/`

### Background Tasks (django-q2)
- Enqueue with: `async_task('module.function', arg1, arg2, ..., task_name='name')`
- Tasks are stored in Django ORM; visible in admin UI under "Django Q → Scheduled Tasks"
- Configure workers with: `Q_CLUSTER_WORKERS`, `Q_CLUSTER_TIMEOUT`, `Q_CLUSTER_MAX_ATTEMPTS`
- Monitor via: `python manage.py qinfo` or admin UI

### Alt Text Generation
- [backend/canvas_app_explorer/alt_text_helper/ai_processor.py](backend/canvas_app_explorer/alt_text_helper/ai_processor.py) uses Azure OpenAI API
- Image → base64 JPEG → Azure Vision API → alt text string
- Configured via `django-constance` dynamic settings (e.g., `AZURE_API_KEY`, `AZURE_MODEL`)

### Frontend Components
- Routes: `/` (tool browser), `/alt-text-helper` (alt text scanning)
- Use React Query for server state; session data passed via Globals context
- API calls via [frontend/app/api.ts](frontend/app/api.ts) (check this file for endpoint patterns)
- MUI `<Card>`, `<Button>`, `<Link>` etc. with theme from [frontend/app/theme.ts](frontend/app/theme.ts)
- **Important**: Use MUI `Link` component for hyperlinks (not `Typography` with `component="a"`). MUI Link provides proper styling and accessibility
- **Accessibility**: All frontend elements must follow U of M accessibility guidelines: https://accessibility.umich.edu/basics/concepts-principles (links underlined by default, color change on hover, sufficient contrast, etc.)

## Developer Workflows

### Setup & Running
```bash
# Start full stack (MySQL, Redis, Django, React)
docker-compose down
docker-compose build
docker-compose up

# Access: http://localhost:5000/ (requires LTI launch from Canvas)
# Swagger API docs: http://localhost:5000/api/schema/swagger-ui  (or append /api/schema/swagger-ui to your Canvas launch URL)
```

### IMPORTANT: All Commands Run in Docker
All Django management commands, migrations, tests, and Python scripts must be run inside the Docker container:
```bash
docker exec -it instructor_tools python manage.py <command>
```
Do NOT run these commands directly on the host machine.

### Testing
```bash
# Run all tests (in container)
docker exec -it instructor_tools python manage.py test

# Run specific test file
docker exec -it instructor_tools python manage.py test backend.tests.test_imageitem_alt_text

# Watch mode during development
cd frontend && npm run watch
```

### Database
- MySQL config: [mysql/init.sql](mysql/init.sql)
- Migrations: `docker exec -it instructor_tools python manage.py makemigrations && docker exec -it instructor_tools python manage.py migrate`
- Canvas OAuth migrations managed manually in `backend/canvas_oauth/migrations/`

### Background Task Monitoring
```bash
# Monitor task queue and workers
docker exec -it instructor_tools python manage.py qinfo

# Via Django admin: /admin/ → Django Q → Task management
```

### Debugging
- Set `DEBUG=True` in `.env` (enabled in docker-compose by default)
- Django logs to stdout; check `docker logs instructor_tools`
- Add `debugpy` breakpoints: import and call (configured in [backend/debugpy.py](backend/debugpy.py))

## Critical Files & Dependencies
- **ORM Models**: [backend/canvas_app_explorer/models.py](backend/canvas_app_explorer/models.py) — defines LtiTool, CourseScan, ContentItem, ImageItem
- **Canvas Integration**: [backend/canvas_app_explorer/canvas_lti_manager/](backend/canvas_app_explorer/canvas_lti_manager/) — adapter for canvasapi
- **Serializers**: [backend/canvas_app_explorer/serializers.py](backend/canvas_app_explorer/serializers.py) — DRF serializers for API responses
- **LTI Endpoints**: [backend/canvas_app_explorer/lti1p3.py](backend/canvas_app_explorer/lti1p3.py) — PyLTI1p3 handlers
- **Alt Text Tasks**: [backend/canvas_app_explorer/alt_text_helper/background_tasks/](backend/canvas_app_explorer/alt_text_helper/background_tasks/) — async task functions
- **External Libraries**: Django 4.2, canvasapi, PyLTI1p3, azure-openai, drf-spectacular, django-q2

## Common Pitfalls
- **Missing course_id**: Check session is populated by LTI launch; return 400 if missing
- **Canvas API rate limits**: Wrap in try/catch; use `RateLimitExceeded` handler
- **Background task timeouts**: Increase `Q_CLUSTER_TIMEOUT` for long-running image processing
- **Database migrations**: Always create new migrations after model changes; don't edit existing ones
- **React Query cache**: Invalidate cache after mutations (e.g., after updating tool visibility)
- **MUI Links in Frontend**: Always use the MUI `Link` component for hyperlinks, not `Typography` with `component="a"`

## Related Documentation
- Canvas API: https://canvas.instructure.com/doc/api/
- LTI 1.3: https://www.imsglobal.org/activity/learning-tools-interoperability/
- Django REST Framework: https://www.django-rest-framework.org/
- django-q2: https://django-q2.readthedocs.io/
