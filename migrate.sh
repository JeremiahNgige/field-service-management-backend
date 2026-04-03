# NOTE: migration files must be generated locally with:
#   python manage.py makemigrations
# and committed to version control before deploying.
# This script only applies already-committed migrations.

echo "Applying database migrations..."
python manage.py migrate

echo "Generating mock jobs data..."
python jobs_generator.py

echo "Done!"
