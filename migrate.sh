if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "Running jobs makemigrations..."
python manage.py makemigrations jobs

echo "Running jobs migrate..."
python manage.py migrate jobs

echo "Running user makemigrations..."
python manage.py makemigrations user

echo "Running user migrate..."
python manage.py migrate user

echo "Done!"
