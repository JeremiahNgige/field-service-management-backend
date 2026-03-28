#!/bin/sh
set -e

echo "Running tests integration test for user and jobs in docker container..."
python manage.py test user.tests_integration jobs.tests_integration
echo "Tests completed!"