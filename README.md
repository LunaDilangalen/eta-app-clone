# GUNICORN DOES NOT SEEM STABLE WITH THIS CODE - launches update_segment_speed twice.
`gunicorn -w 1 -b 127.0.0.1:5000 "eta_app:create_app()"`

`gunicorn -w 1 -b 127.0.0.1:5001 "eta_app:create_app()"`

# USE THIS INSTEAD
`FLASK_APP=eta_app FLASK_ENV=production flask run -p 5001`
`FLASK_APP=eta_app FLASK_ENV=production flask run -p 5000`
`FLASK_APP=eta_app FLASK_ENV=development flask run -p 5000`
