#!/usr/bin/python3

from flask import Flask, request, jsonify, request
import json
import requests 
app = Flask(__name__)

serverPort = 9999
clientPort = 8080
players = {} # (key,value) = (client_id, client_ip)
mainServerIP = "-1"
#mainServerIP = "127.0.0.1"

################################################# ClIENT FUCNTIONS ###################################

def getURL():
    url = "http://" + mainServerIP + ":" + str(serverPort)
    return url

def getPlayerURL(ip):
    url = "http://" + str(ip) + ":" + str(clientPort)
    return url

#connects clients to the game
@app.route("/ClientJoin", methods=["POST"])
def ClientJoin():
    global players
    ip = request.remote_addr #store clients ip
    joinMsg = request.get_json(force=True) #get message from client
    joinResponse = requests.post(getURL() + "/ClientJoin", json=joinMsg) #send message to server
    #store client_id and ip
    body = joinResponse.json()
    clientID = body['Client_ID']
    players.update({str(clientID): str(ip)})
    print(players)
    return jsonify(joinResponse.json()) #send response back to client

#forwards moves from the client to the main server
@app.route("/PlayerMovement", methods=['POST'])
def PlayerMovement():
    moves = request.get_json(force=True)
    response = requests.post(getURL(), json=moves) 
    return response.content

#tells server player is ready
@app.route("/Ready", methods=["POST"])
def Ready():
    readyMsg = request.get_json(force=True)
    readyResponse = requests.post(getURL() + "/Ready", json=readyMsg)
    return readyResponse.content


################################################# SERVER FUCNTIONS ###################################

#recieves updated main server ip from a server
@app.route("/NewPrimary", methods=['POST'])
def NewPrimary():
    global mainServerIP
    ip = request.get_json('IP')
    mainServerIP = str(ip['IP'])
    print (mainServerIP)
    return 'ok'

#forwards game state from main server to all clients
@app.route("/GameUpdate", methods=['POST'])
def GameUpdate():
    gameState = request.get_json(force=True)
    for ip in players:
        requests.post(getPlayerURL(players[ip]), json=gameState)
    return 'ok'

#returns the main server ip
#	-if no main server yet, sets the requesting server to the main server and returns the same servers address
@app.route("/Join", methods=['GET'])
def Join():
	global mainServerIP
	if mainServerIP != "-1":
		return jsonify({'Type': 'JoinOK', "Primary_IP": mainServerIP})
	else:
		mainServerIP = str(request.remote_addr)
		return jsonify({'Type': 'JoinOK', "Primary_IP": mainServerIP})

#server tells all players game is starting
@app.route("/GameStart", methods=['POST'])
def GameStart():
	gameState = request.get_json(force=True)
	for ip in players:
		requests.post(getPlayerURL(players[ip]), json=gameState)
	return 'ok'
