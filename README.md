# King_of_the_559
This is a practice of creating a distributed system.

This is a 2D game survival game, where players can compete over LAN to survive against the map and each other. 

By using Viewstamped Replication, we can provide some amount of fault tolerance for each player (if the host disconnects) and provide a means to reconnect disconnected players.



# Routing README
A simple router, built using flask to route requests from our main Unity process to the appropriate server.

## Linux Installation Instructions
**Note:** This assumes you have a python3 installation.

Copy and paste this block of commands into terminal:
```
git clone https://github.com/michealfriesen/King_of_the_559.git
cd King_of_the_559/router
python3 -m venv venv
. venv/bin/activate
pip install Flask
```

## Windows Installation Instructions
**Note:** This is also assuming you have python3 installed.

Copy and paste this block of commands into terminal:
```
git clone https://github.com/michealfriesen/CPSC559-Router.git
cd CPSC559-Router
py -3 -m venv venv
venv\Scripts\activate
pip install Flask
```


## Usage Instructions:
If we arent in the virtual environment, run the following:

### Linux
```
. venv/bin/activate
set FLASK_APP=main.py
flask run
```

### Windows
```
venv\Scripts\activate
set FLASK_APP=main.py
flask run
```

This should start the server at localhost:5000.