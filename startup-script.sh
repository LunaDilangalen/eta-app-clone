# Echo commands
set -v

# [START getting_started_gce_startup_script]
# Install Stackdriver logging agent
curl -sSO https://dl.google.com/cloudagents/install-logging-agent.sh
sudo bash install-logging-agent.sh

# Install or update needed software
apt-get update
apt-get install -yq git supervisor python python-pip
pip install --upgrade pip virtualenv

# Install mongodb
sudo apt-get -yq install mongodb
sudo mkdir $HOME/db
sudo mongod --dbpath $HOME/db --port 80 --fork --logpath /var/tmp/mongodb

# Account to own server process
useradd -m -d /home/pythonapp pythonapp

# Fetch source code
export HOME=/root
git clone https://gitlab.com/gps-198-ndsg2019-group/eta_app_198.git /opt/app

# Python environment setup
virtualenv -p python3 /opt/app/env
source /opt/app/env/bin/activate
/opt/app/env/bin/pip install -r /opt/app/requirements.txt

# Set ownership to newly created account
chown -R pythonapp:pythonapp /opt/app

# Put supervisor configuration in proper place
cp /opt/app/python-app.conf /etc/supervisor/conf.d/python-app.conf

# seed segment models in database
sudo bash /opt/app/seed_segment.sh

# Start service via supervisorctl
sudo supervisorctl reread
sudo supervisorctl update
# [END getting_started_gce_startup_script]
