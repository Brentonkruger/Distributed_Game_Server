from flask import Flask, request
import json
app = Flask(__name__)

replica_data = {}
player_data = {}
primary_ip = ""


# Function that will take inputs from the query parameters, and return the newly processed data back.
def buildJson(name, location, desired_move):
    player_data[name] = {}
    player_data[name]['Location'] = location
    player_data[name]['New Location'] = 'Need to calculate'
    jsonified = json.dumps(player_data[name])
    return jsonified

#Function used to add a replica to the list of known replicas. It will also supply the primary ip.
def addReplica():
    if(primary_ip = ""):
        primary_ip


# This function needs to somehow return the values of the other players
# It also might do some processing, which is why it is a seperate function
def getPlayers():
    data = json.dumps(player_data)
    return data


@app.route('/calculate')
def calculate():
    return buildJson(request.args.get('name'), request.args.get('location'), request.args.get('move'))

@app.route('/players')
def players():
    return getPlayers()

@app.route('/join')
def players():
    return getPlayers()

