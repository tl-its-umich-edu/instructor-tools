# Instructor Productivity Tools

## Usage

### Development mode

Development mode for this application starts up 2 processes in the same container, one running on port 5000 (Python/Django backend) and one that writes to the disk and recompiles the frontend. This allows for changes to be picked up and re-built from the mounted local volumes.

With Docker installed run
`docker-compose down; docker-compose build && docker-compose up`

Then the app in development should be accessible on http://localhost:5000/

Now you can make changes to files in `frontend` and the changes **should** show up in the browser automagically.

This app can currently only be launched via LTI.  Please see the Wiki for instructions on configuring with LTI.
#### Using OpenAPI and Swagger

The backend uses the [Django Rest Framework](https://www.django-rest-framework.org/) to build out a REST API. When `DEBUG` is equal to `True` in Django settings, the application leverages the [drf-spectacular](https://drf-spectacular.readthedocs.io/en/latest/index.html) library to document existing endpoints and provide for API testing using Swagger.

The OpenAPI schema can be downloaded as a YAML file from `http://localhost:5000/api/schema`. To use the Swagger UI, do the following:
1. Launch the tool from a course in Canvas.
2. Right-click in the iframe and select "View Frame Source" in Chrome (or your browser's equivalent).
3. Change the URL to navigate to `/api/schema/swagger-ui`.

Once on the page, requests can be made against the API using the "Try it out" functionality.

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
