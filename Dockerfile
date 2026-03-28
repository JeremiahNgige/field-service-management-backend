FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . /app/

# Expose port
EXPOSE 8000

# ==============================================================================
# TESTING PURPOSES ONLY
# Uncomment the line below to run tests automatically when building the image. 
# Note: This will fail the build if tests do not pass.
# RUN python manage.py test user.tests_integration jobs.tests_integration
# ==============================================================================

# Run migrations and start server using gunicorn
CMD ["sh", "-c", "sh migrate.sh && gunicorn fsm_backend.wsgi:application --bind 0.0.0.0:8000"]
