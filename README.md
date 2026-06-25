# Instructor Productivity Tools

## Usage

### Development mode

Development mode for this application starts up 2 processes in the same container, one running on port 5000 (Python/Django backend) and one that writes to the disk and recompiles the frontend. This allows for changes to be picked up and re-built from the mounted local volumes.

With Docker installed run
`docker-compose down; docker-compose build && docker-compose up`

Then the app in development should be accessible on http://localhost:5000/

Now you can make changes to files in `frontend` and the changes **should** show up in the browser automagically.

This app can currently only be launched via LTI.  Please see the Wiki for instructions on configuring with LTI.
For Canvas LTI launch background and platform behavior, see the [Canvas LTI launch overview](https://developerdocs.instructure.com/services/canvas/external-tools/lti/file.lti_launch_overview).

#### Configure LTI From The Command Line

You can create or update the PyLTI tool configuration from the command line without typing the full issuer and auth URLs each time.

Run the command inside Docker:

```sh
docker exec -it instructor_tools python manage.py manage_pylti \
    --domain=prod \
    --client_id=<canvas_client_id> \
    --title="Instructor Productivity Tools" \
    --tool_key=<tool_key_name> \
    --deployment_ids <deployment_id_1> <deployment_id_2>
```

Inputs:
1. `client_id` - Canvas LTI client ID (required)
2. `title` - Tool title saved in the PyLTI tool record (required)
3. `tool_key` - Tool key name to reuse or create (required)
4. `domain` - One of `prod`, `dev`, `beta`, or `test` (default: `prod`)
5. `deployment_ids` - Optional deployment ID values

Domain mapping:
1. `prod` and `dev` use issuer `https://canvas.instructure.com` and auth domain `https://sso.canvaslms.com`
2. `beta` uses issuer `https://canvas.beta.instructure.com` and auth domain `https://sso.beta.canvaslms.com`
3. `test` uses issuer `https://canvas.test.instructure.com` and auth domain `https://sso.test.canvaslms.com`

Notes:
1. `prod` is the default if `--domain` is omitted.
2. `--deployment_ids` is optional. Omit it if you do not need to set deployment IDs.
3. You can optionally override the generated issuer/auth domains using `--platform` and `--auth_domain`.
4. Example override usage:

```sh
docker exec -it instructor_tools python manage.py manage_pylti \
    --domain=prod \
    --platform=canvas.instructure.com \
    --auth_domain=sso.canvaslms.com \
    --client_id=<canvas_client_id> \
    --title="Instructor Productivity Tools" \
    --tool_key=<tool_key_name>
```

5. The command reuses an existing tool key if the name already exists; otherwise it generates a new RSA key pair.

#### Using OpenAPI and Swagger

The backend uses the [Django Rest Framework](https://www.django-rest-framework.org/) to build out a REST API. When `DEBUG` is equal to `True` in Django settings, the application leverages the [drf-spectacular](https://drf-spectacular.readthedocs.io/en/latest/index.html) library to document existing endpoints and provide for API testing using Swagger.

The OpenAPI schema can be downloaded as a YAML file from `http://localhost:5000/api/schema`. To use the Swagger UI, do the following:
1. Launch the tool from a course in Canvas.
2. Right-click in the iframe and select "View Frame Source" in Chrome (or your browser's equivalent).
3. Change the URL to navigate to `/api/schema/swagger-ui`.

Once on the page, requests can be made against the API using the "Try it out" functionality.

For endpoints protected by course tab isolation middleware, Swagger requests must include the signed course context header.
1. In Swagger UI, click `Authorize`.
2. For `SignedCoursePayload`, paste the signed value from session storage (no quotes).
3. Click `Authorize`, then `Close`.

To get the signed value, use one of the following methods.

Method 1 (recommended): DevTools Application tab
1. Open browser devtools in the launched tool page.
2. Go to `Application` -> `Session Storage`.
3. Select the app origin (for local this may be `localhost:5000`; when proxied, select your `ngrok` origin).
4. Find key `signed_course_user_payload` and copy its value.
5. Paste that value into Swagger `Authorize` for `SignedCoursePayload`.
Method 2: Get it from Source
1. Launch the app and Right click and choose "View Frame Source"
2. Look for <script> tag and `cae_globals` and Find key `signed_course_user_payload` and copy its value.
3. Paste that value into Swagger `Authorize` for `SignedCoursePayload`.
```

### Testing production (Openshift) build

The openshift build compiles all of the frontend assets into the container during the build. It uses whitenoise currently to serve up the content.

To build, use the separate docker-compose-openshift-test.yml file. This uses a slightly different dockerfiles/Dockerfile.openshift that uses a static path and disables DEBUG.

`docker compose -f docker-compose-openshift-test.yml build`

Then to start it you can run
`docker compose -f docker-compose-openshift-test.yml up`

This should start up as expected on http://localhost:5000


### Running Unit test
All test are in the `tests` folder. To run the tests 

```sh 
docker exec -it instructor_tools python manage.py test
```

### Configuring Canvas Staff Role Access
Access to the tool is controlled by Canvas course role values sent in the LTI custom parameter
`canvas_course_roles`.

The following base roles are always treated as staff:
1. `Account Admin`
3. `TeacherEnrollment`

To add institution-specific roles without code changes:
1. Open Django Admin.
2. Go to `Constance`.
3. Edit `ADDITIONAL_STAFF_COURSE_ROLES` with a comma-separated list of exact role strings. 

Default additional roles:
1. `Sub-Account Admin`


Notes:
1. Role matching is case-insensitive after trimming whitespace.
2. You can add or remove entries at runtime from Django Admin.
3. Environment variable `ADDITIONAL_STAFF_COURSE_ROLES` only provides the initial default value.
    After a value is saved in Constance, the admin value takes precedence.

### Django Queue
1. Getting the Alt text from course images run as a background task.
2. We are using [Django ORM](https://django-q2.readthedocs.io/en/master/brokers.html#django-orm) is set a default message Broker.
3. Django admin can be used for tracking Successful, Failed, Queued, Scheduled Tasks
    1. Apart from Django admin, CLI can be used for [tracking](https://django-q2.readthedocs.io/en/master/monitor.html) as well:
        ```
        python manage.py qinfo
        ```
4. The following environment variables can be set to configure Django Q background task processing
    1. `Q_CLUSTER_WORKERS` - Number of worker processes (default: 4)
    2. `Q_CLUSTER_TIMEOUT` - Task execution timeout in seconds (default: 900, i.e., 15 minutes)
    3. `Q_CLUSTER_RETRY` - Retry interval in seconds for failed tasks (default: 1800, i.e., 30 minutes)
    4. `Q_CLUSTER_BULK` - Sets the number of messages each cluster tries to get from the broker per call.
    5. `Q_CLUSTER_MAX_ATTEMPTS` - Maximum number of retry attempts for a task after failure (default: 1)
    6. `Q_CLUSTER_NAME` - Cluster Name

### Debugging Django Q tasks
To hit breakpoints in background task modules (for example [backend/canvas_app_explorer/alt_text_helper/background_tasks/canvas_tools_alt_text_scan.py](backend/canvas_app_explorer/alt_text_helper/background_tasks/canvas_tools_alt_text_scan.py)), run the qworker with debugpy enabled.

Set these environment variables (for local docker-compose):

```sh
QWORKER_DEBUGPY_ENABLE=true
QWORKER_DEBUGPY_PORT=5021
QWORKER_DEBUGPY_WAIT_FOR_CLIENT=true
```

Then:
1. Rebuild/restart containers (`docker-compose down && docker-compose build && docker-compose up`).
2. In VS Code Run and Debug, start `IPT Django Q Worker` (attach to localhost:5021).
3. Queue a scan task from the UI.
4. Breakpoints in the worker process should stop when task code executes.

Notes:
1. Port `5021` must be exposed on the web container.
2. If `QWORKER_DEBUGPY_WAIT_FOR_CLIENT=true`, the worker waits for debugger attach before executing queued tasks.


## Acknowledgment:

The concept for the Alt Text Helper tool was inspired by a proof‑of‑concept project created by Chris Smith (@ smithcth), Help Desk Supervisor in the Office of Online & Digital Education at the University of Michigan–Flint. We appreciate his guidance and collaboration on implementing the LTI version of the Alt Text Helper tool.