# seed segment db
cd /opt/app/
export FLASK_APP=eta_app
env/bin/flask init-perf-logs
env/bin/flask seed-segment-db ikot
cd
