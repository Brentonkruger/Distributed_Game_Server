#!/usr/bin/python3

from flask import Flask, request, jsonify, request
import json
import requests 
app = Flask(__name__)

players = []
mainServerIP = -1

################################################# ClIENT FUCNTIONS ###################################

#connects clients to the game
@app.route("/connectPlayer", methods=["GET"])
def connectPlayer():
	ip = request.remote_addr
	if ip not in players:
		players.append(ip)
	return 'Recieved'

#forwards moves from the client to the main server
@app.route("/forwardToMainServer", methods=['POST'])
def sendMoves():
	moves = request.get_json()
	print (moves)
	requests.post(mainServerIP, data=moves)
	return 'Recieved'

################################################# SERVER FUCNTIONS ###################################

#recieves updated main server ip from a server
@app.route("/updateMainServer", methods=['POST'])
def updateMainServer():
	mainServerIP = request.get_json('ip')
	return 'Recieved'

#forwards game state from main server to all clients
@app.route("/updatePlayersGameState", methods=['POST'])
def updatePlayersGameState():
	gameState = request.get_json()
	for ip in players:
		requests.post(ip, data=gameState)
	return 'Recieved'

#returns the main server ip
#	-if no main server yet, sets the requesting server to the main server and returns the same servers address
@app.route("/join", methods=['GET'])
def join():
	global mainServerIP
	if mainServerIP != -1:
		return jsonify({'Type': 'JoinOK', "Primary_IP": str(mainServerIP)})
	else:
		mainServerIP = request.remote_addr
		return jsonify({'Type': 'JoinOK', "Primary_IP": str(mainServerIP)})
