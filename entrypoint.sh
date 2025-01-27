#!/bin/bash
# if the script cannot be found, change the file from CRLF to LF

# laod env variables: https://stackoverflow.com/questions/19331497/set-environment-variables-from-file-of-key-value-pairs#comment37343914_20909045
export $(grep -v '^#' .env | xargs)

# run server
python manage.py makemigrations
python manage.py migrate

if [ "$DJANGO_SUPERUSER_USERNAME" ]
then
    echo "Trying to create user based on environment variables, error message after first creation is normal."
    python manage.py createsuperuser \
        --noinput 
fi

exec "$@"