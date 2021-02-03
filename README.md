# ETA Application (Server)

The ETA Application is an implementation of a service that would use the Northbound APIs of NIMPA. It communicates with NIMPA, fetching and processing public utility vehicle (PUV) data, to track movements and compute the estimated time-of-arrival of PUVs.

### Dependencies
* Runs successfully with Python 3.5.x or newer
* Runs successfully with MongoDB 4.2.0
* See requirements.txt for list of required Python packages

### Managing the ETA Server
To help you manage the ETA server such as cleaning its databases or intializing performance logs, some Flask commands are provided for you to call via shell. Make sure that your working directory contains the eta_app directory prior to using these commands.

1. Clean segment MongoDB collection  `flask clean-segment-db`
    ```
    $ FLASK_APP=nimpa flask clean-segment-db
    ```
2. Clean vehicle MongoDB collection `flask clean-vehicle-db`
    ```    
    $ FLASK_APP=nimpa flask clean-vehicle-db
    ```
3. Initialize performance logs `flask init-perf-log`
    ```
    $ FLASK_APP=nimpa flask init-perf-logs
    ```
4. Initialize and seed the segment MongoDB collection `flask seed-segment-db`
    ```
    $ FLASK_APP=nimpa flask seed-segment-db <route_option>
    ```

### Installation
Note: The following steps are done on Ubuntu 18.04

* Install Python 3.x, git
    ```
    $ sudo apt-get install git python3 
    ```
* Installing MongoDB - Please refer to MongoDB Docs for Installation Guide
    https://docs.mongodb.com/manual/tutorial/install-mongodb-on-ubuntu/
    
* Clone GitLab Repository
    ```
    $ git clone https://gitlab.com/gps-198-ndsg2019-group/eta_app_198.git
    $ cd eta_app_198
    ```
* Create a virtual environment (Optional)
    ```
    $ python3 -m venv venv
    $ source venv/bin/activate
    
    # To deactivate:
    $ deactivate
    ```

* Install Python dependencies
    ```
    # with virtualenv activated
    $ pip install -r requirements.txt
    
    # without virtualenv
    $ pip3 install -r requirements.txt
    ```

### Running Locally
* Make sure MongoDB server is running
    ```
    $ sudo systemctl start mongod
    ```

* Initialize the performance logs and seed the route data to MongoDB database through Flask shell
    ```
    $ cd eta_app_198
    $ export FLASK_APP=eta_app
    $ flask init-perf-logs
    $ flask seed-segment-db ikot
    ```
* On a separate terminal, run the route updater Python script
    ```
    $ python eta_app/segment_watcher.py 
    ```
* Finally, run the ETA server
    ```
    $ cd eta_app_198
    $ source venv/bin/activate
    
    # running with Flask
    $ FLASK_APP=eta_app FLASK_ENV=development flask run -p 5000
    
    # running with gunicorn
    $ gunicorn -w 1 -b 127.0.0.1:5000 "eta_app:create_app()"
    ```
