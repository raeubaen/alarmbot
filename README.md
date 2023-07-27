in LOCALE:
La prima volta:
- virtualenv targhenv
- mv targhenv ../.targhenv
- source activate ../.targhenv/bin/activate
- pip install -r requirements.txt
- chiedere a Ruben in privato il token del Bot
- mettere token del bot in .token
- python3 manage.py migrate

sempre:
- attivare virtualenv
- far partire il sistema in locale con python3 manage.py runserver --noreload
