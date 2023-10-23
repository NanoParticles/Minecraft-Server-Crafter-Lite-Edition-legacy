#main.py

from customtkinter import *
import subprocess
import time
import threading
import traceback
from altdialog import FileSelectWindow
from tkinter import filedialog
import json
import socket
import os
import sys
import requests
import math
import psutil
import zipfile
from PIL import Image,ImageTk
from CTkToolTip import *
import hashlib
from tempfile import NamedTemporaryFile
from CTkListbox import *
import sqlite3
import uuid
import datetime

versionType="release-lite"
version="0.0.15"
MinecraftServerCrafter_versionData = {}
MinecraftServerProperties = {}
MinecraftServerType = {}
MinecraftServerType["name"] = ""
possibleJarNames = ["paper-","fabric-","forge-","spigot-","server","minecraft-","bukkit-","craftbukkit-","purpur-"]
blocksize = 1024**2
#Set the absolute path, so we are going to cheese it
pathreferenceTemp = os.path.dirname(os.path.abspath(__file__))
#Random file reference
propertiesJSONFilepath = os.path.join(pathreferenceTemp,"properties.json")
rootFilepath = os.path.split(propertiesJSONFilepath)[0]
os.chdir(str(rootFilepath))
whitelist = {}
playerBans = {}

MCSCDatabase = sqlite3.connect("mcsc_data.db")
MCSC_Cursor = MCSCDatabase.cursor()

class HardwareSpec():
	'HardwareSpec() -> Memory Management \n \n Extra Utilities for Memory Management '
	def getByteSize(bytes, suffix="B"):
		'getByteSize(bytes) -> String \n \n Returns the total measurement of bytes either in Megabytes, or Gigabytes as a string'
		totalBytes = int(bytes)
		if totalBytes >= int(1048576) and totalBytes < int(1073741824):
			unit = "M"
			TotalMB = int(totalBytes) / (int(1024) * int(1024))
			return str(f"{TotalMB:.2f}{unit}{suffix}")
		if totalBytes >= int(1073741824) and totalBytes < int(1099511627775):
			unit = "G"
			TotalGB = int(totalBytes) / (int(1024) * int(1024) * int(1024))
			return str(f"{TotalGB:.2f}{unit}{suffix}")
	def getByteSizeInt(bytes):
		'getByteSizeInt(bytes) -> Integer \n \n Returns the total measurement of bytes either in Megabytes, or Gigabytes as a tuple. \n \n Tuple Reference \n ================= \n index 0: Integer value \n index 1: Measurement Scale'
		totalbytes = int(bytes)
		if totalbytes >= int(1048576) and totalbytes < int(1073741824):
			TotalMB = int(totalbytes) / (int(1024) * int(1024))
			return (float(f"{TotalMB:.2f}"),"MB")
		if totalbytes >= int(1073741824) and totalbytes < int(1099511627775):
			TotalGB = int(totalbytes) / (int(1024) * int(1024) * int(1024))
			return (float(f"{TotalGB:.2f}"),"GB")
	def getPhysicalMemory(suffix="B"):
		'getPhysicalMemory() -> Hardware Scale \n \n Returns the amount of physical memory installed'
		TotalBytes = int(psutil.virtual_memory().total)
		if TotalBytes >= int(1048576) and TotalBytes < int(1073741824):
			unit = "M"
			TotalMB = int(TotalBytes) / (int(1024) * int(1024))
			RoundedMB = round(TotalMB)
			PhysicalMemMB = math.trunc(int(RoundedMB))
			return f'{PhysicalMemMB}{unit}{suffix}'
		if TotalBytes >= int(1073741824) and TotalBytes < int(1099511627775):
			unit = "G"
			TotalGB = int(TotalBytes) / (int(1024) * int(1024) * int(1024))
			RoundedGB = round(TotalGB)
			PhysicalMemGB = math.trunc(int(RoundedGB))
			return f'{PhysicalMemGB}{unit}{suffix}'
		return
	def ServerQuery_onServerStart_MemoryAllocate(ScaledMemInt=0,ScaledMemSize=None,MemoryScaleSize=None):
		#We need to properly measure the amount of ScaledMemInt into MemoryScaleSize(i.e. 32GB in Megabytes)
		#Simple Math time xD
		ScaledMemByteSize = str(ScaledMemSize)
		if ScaledMemByteSize == "GB":
			#We need the total amount of scaled memory in bytes
			ScaledMemIntinbytes = int(ScaledMemInt) * int(1**9)
			#We need to scale the bytes in the value of MemoryScaleSize
			ExpectedScaleSize = str(MemoryScaleSize)
			if ExpectedScaleSize == "MB":
				#Scale the bytes in megabytes
				TotalScaledMemMB = int(ScaledMemIntinbytes) / (int(1024) * int(1024))
				#We need it as a whole number
				RoundedScaledMemMB = round(TotalScaledMemMB)
				ScaledMeminMB = math.trunc(int(RoundedScaledMemMB))
				return (float(ScaledMemInt),str(ScaledMemSize),float(f'{ScaledMeminMB}'))
	
class InternetHost():
	'InternetHost() -> Internet Connection \n \n Extra Utilities for Internet Connection'
	global ConsoleWindow
	def connectionCheck():
		'connectionCheck() -> Socket Connection \n \n Creates a Socket Connection. This is primarily used for checking if the local host is connected to the internet. \n If the socket connection is successfully connected, then it returns true. Otherwise, an exception is raised.'
		try:
			result = socket.create_connection(('8.8.8.8', 53),timeout=8)
			result.close()
			return True
		except (OSError,ExceptionGroup) as e:
			print(e)
			ConsoleWindow.displayException(e)
			return False
	def getIPV4():
		'getIPV4() -> Local IP Address \n \n Returns the IP Address of the Local Host Computer'
		try:
			if InternetHost.connectionCheck() == True:
				Socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				try:
					Socket.connect(('10.255.255.255',1))
					IP = Socket.getsockname()[0]
				except Exception:
					IP = '127.0.0.1'
				finally:
					Socket.close()
				return IP
			else:
				ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter API - Internet Host]: Unable to connect to the Internet(REASON: No Connection)")
				return
		except socket.error as e:
			ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter API - Internet Host]: Unable to connect to the Internet(REASON: Exception raised, detailed walkthrough below)")
			ConsoleWindow.displayException(e)
			return
	def getPublicIP():
		'getPublicIP() -> Public IP Address \n \n Returns the Public IP Address of the Local Host'
		try:
			public_ip = requests.get('https://api.ipify.org',timeout=5)
			if public_ip.status_code == 200:
				return public_ip.text.strip()
		except requests.RequestException as e:
			ConsoleWindow.displayException(e)
			return

class ServerFileIO():
	'ServerFileIO -> File Operation Class \n \n ServerFileIO has Core Components of Minecraft Server Crafter. Its primarily File Operations, and Database Queries.'
	def __init__(self):
		PropertiesFileSearchThread = None
		BannedPlayers_SearchThread = None
		BannedIPs_SearchThread = None
		ServerJarSelection = None
		WhitelistPlayers_SearchThread = None

	def loadJSONProperties(): #Minecraft Server Properties in its own json
		'loadJSONProperties() -> loads properties.json \n \n Loads the properties.json data, and updates the MinecraftServerProperties JSON model in memory'
		#load the json file
		with open(str(rootFilepath) + "/properties.json","r") as readJSON:
			dataDump = json.load(readJSON)
			for key, val in dataDump.items():
				MinecraftServerProperties[key] = val
			print("[Minecraft Server Crafter]: Properties loaded. Rebuilding...")
			#Scan the payload for true or false
			for key, val in MinecraftServerProperties.items():
				#Staticlly set the ip with the IP address
				MinecraftServerProperties["server-ip"] = str(InternetHost.getIPV4())
			#Apply update to the dictionary
			MinecraftServerProperties.update()
			print("[Minecraft Server Crafter]: Structure Rebuilt Successfully.")
		return
	
	def exportPropertiestoJSON(): #Triggers when the application closes. Save feature
		'exportPropertiestoJSON() -> saves to properties.json \n \n Saves the MinecraftServerProperties JSON model to properties.json'
		print("[Minecraft Server Crafter]: Exporting Properties...")
		with open(str(rootFilepath) + "/properties.json","w") as writeJSON:
			json.dump(MinecraftServerProperties,writeJSON,indent=4)
		print("[Minecraft Server Crafter]: Properties Saved.")
		return
	
	def importPropertiestoJSON(serverjarpath): #Converts server.properties to properties.json
		'importPropertiestoJSON(serverjarpath) -> loads server.properties \n \n Updates the MinecraftServerProperties JSON model based off of the server.properties(while skipping the header)'
		#We need the properties file that the minecraft server looks it
		with open(str(serverjarpath) + "/server.properties","r") as propertiesFileLineCounter:
			#We need to know how many lines there are
			lineCounter = int(0)
			for count, line in enumerate(propertiesFileLineCounter):
				lineCounter = count + int(1)
				pass
			propertiesFileLineCounter.close()
		with open(str(serverjarpath) + "/server.properties", "r") as propertiesFile:
			#We skip the first 2 lines cuz its useless
			dataDump = propertiesFile.readlines()[2:int(lineCounter)]
			dataDump = [line.rstrip("\n") for line in dataDump]
			#Now we put it in the MinecraftServerProperties dictionary by iterating the list
			for item in dataDump:
				key,value = item.split("=")
				#Handling cases where the value is empty or missing
				if value == "":
					value = None
				MinecraftServerProperties[key] = value
			propertiesFile.close()
		return

	def scanJarForServerType():
		'scanJarForServerType() -> Search Query \n \n Searches the current jar file for the type of server it is'
		global ServerJarSelection
		data_set = {}
		with zipfile.ZipFile(str(ServerJarSelection.getFilepathString()),"r") as currentWorkingJar:
			#We need to read a manifest file
			with currentWorkingJar.open("META-INF/MANIFEST.MF","r") as ManifestFile_raw:
				for line in ManifestFile_raw.readlines():
					line = line.decode("utf-8").strip()
					if line:
						try:
							key,val = line.split(":",1)
							data_set[key] = val.strip()
						except ValueError:
							pass
				ManifestFile_raw.close()
			currentWorkingJar.close()
		#Whats the main class called?
		mainClassQuery = data_set.get("Main-Class")
		while True:
			if mainClassQuery.startswith("net.minecraft"):
				serverType = "Minecraft Vanilla"
				MinecraftServerType["name"] = "Minecraft Vanilla"
				MinecraftServerType.update()
				break
			else:
				if mainClassQuery.startswith("net.fabricmc"):
					serverType = "Fabric"
					MinecraftServerType["name"] = "Fabric"
					MinecraftServerType.update()
					break
				else:
					if mainClassQuery.startswith("io.papermc"):
						serverType = "Paper"
						MinecraftServerType["name"] = "Paper"
						MinecraftServerType.update()
						break
					else:
						if mainClassQuery.startswith("org.bukkit.craftbukkit"):
							serverType = "CraftBukkit"
							MinecraftServerType["name"] = "CraftBukkit"
							MinecraftServerType.update()
							break
						else:
							break
		return serverType
	
	def addPlayerToWhitelist(playerName):
		'addPlayerToWhitelist(playerName) -> Database Query \n \n Logic for adding a player to the Whitelist Table'
		global ConsoleWindow

		try:
			parseAPI = requests.get("https://api.mojang.com/users/profiles/minecraft/" + str(playerName))
			if parseAPI.status_code == 200:
				playerInfo = parseAPI.json()
				#We need to convert the trimmed uuid to a full uuid
				playerUUID = playerInfo["id"]
				fulluuid = uuid.UUID(str(playerUUID))
				playerInfo["id"] = str(fulluuid)
				playerData = {playerInfo["name"]: playerInfo["id"]}
				#Add to the whitelist_Table
				insertquery = "INSERT OR REPLACE INTO whitelist_Table VALUES (?, ?)"
				for key, value in playerData.items():
					MCSC_Cursor.execute(insertquery,(value,key))
					del playerData
				ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: Added " + str(playerInfo["name"]) + " to Whitelist")
				return
			else:
				#Error handling from here on
				if parseAPI.status_code == 204:
					#No Content
					raise Exception("[Minecraft Server Crafter]: Mojang API returned 204: No Content Raised")
				else:
					if parseAPI.status_code == 400:
						#Bad Request
						errorInformation = parseAPI.json()
						raise Exception("[Minecraft Server Crafter]: Mojang API returned with " + str(errorInformation["error"]) + ".\n Message from API: " + str(errorInformation["errorMessage"]))
					else:
						if parseAPI.status_code == 405:
							#Method Not Allowed
							errorInformation = parseAPI.json()
							raise Exception("[Minecraft Server Crafter]: Mojang API returned with " + str(errorInformation["error"]) + ".\n Message from API: " + str(errorInformation["errorMessage"]))
						else:
							if parseAPI.status_code == 429:
								#Too many requests
								errorInformation = parseAPI.json()
								raise Exception("[Minecraft Server Crafter]: Mojang API returned with " + str(errorInformation["error"]) + ".\n Message from API: " + str(errorInformation["errorMessage"]))
		except Exception as e:
			ConsoleWindow.displayException(e)
			if errorInformation:
				ConsoleWindow.updateConsole(END,"Mojang API Error - Additional Information\n =================== \n" + str(errorInformation))
			return

	def removePlayerfromWhitelist(playerName):
		'removePlayerfromWhitelist(playerName) -> Database Query \n \n Logic for removing a player from the whitelist table'
		global ConsoleWindow

		try:
			deleteQuery = "DELETE FROM whitelist_Table WHERE name = ?"
			MCSC_Cursor.execute(deleteQuery,(playerName,))
			ConsoleWindow.updateConsole(END, "[Minecraft Server Crafter]: Removed " + str(playerName) + " from Whitelist")
			return
		except sqlite3.Error as e:
			#Undo Changes
			ConsoleWindow.displayException(e)
			MCSCDatabase.rollback()
			return
	
	def importWhitelistfromJSON():
		'importWhitelistfromJSON() -> JSON Query \n \n Logic for importing the whitelist.json to the whitelist_Table in the Database file'
		#We need to get the whitelist from json
		global ServerJarSelection
		global ConsoleWindow

		#We need the server directory in order to get the whitelist.json
		ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: Importing whitelist JSON...")
		whitelistFileDirectory = ServerJarSelection.getcurrentpath()
		with open(str(whitelistFileDirectory) + "/whitelist.json","r") as whitelistJson:
			datadump = json.load(whitelistJson)
			if datadump:
				for item in datadump:
					whitelist[item["name"]] = item["uuid"]
				if whitelist:
					#We need to put it in the whitelist table
					insertQuery = "INSERT OR REPLACE INTO whitelist_Table VALUES (?, ?)"
					for key,value in list(whitelist.items()):
						MCSC_Cursor.execute(insertQuery, (value,key))
						del whitelist[key]
						continue
					ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: Whitelist.json loaded.")
				else:
					return
			else:
				#Nothing is in the json file. Its a empty list
				return
			whitelistJson.close()
		return
	
	def exportWhitelistfromDatabase():
		'exportWhitelistfromDatabase() -> Database Query \n \n Logic for exporting the whitelist_Table in the Database file to whitelist.json'
		global ServerJarSelection
		global ConsoleWindow

		#We need to parse the whitelist table
		ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: Exporting Whitelist Table...")
		MCSC_Cursor.execute("SELECT uuid, name FROM whitelist_Table")
		rows = MCSC_Cursor.fetchall()
		for row in rows:
			uuid, name = row
			whitelist[str(name)] = str(uuid)
		#We need to then turn it into a list
		formattedwhitelist = [{"uuid": uuid, "name": name} for name, uuid in whitelist.items()]
		serverdirectory = ServerJarSelection.getcurrentpath()
		with open(str(serverdirectory) + "/whitelist.json","w") as whitelistWrite:
			json.dump(formattedwhitelist,whitelistWrite,ensure_ascii=False,indent=4)
			whitelistWrite.close()
		ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: Whitelist Table has been successfully saved to JSON")
		return
	
	def populateWhitelist_Listbox():
		'populateWhitelist_Listbox() -> Database Query \n \n Logic for displaying the whitelisted players thats in the whitelist_Table in the Listbox widget'
		global WhitelistListbox

		#Is the listbox already populated?
		challengeWhitelistInt = WhitelistListbox.size()
		if challengeWhitelistInt < 0:
			for i in enumerate(challengeWhitelistInt):
				WhitelistListbox.delete(i)
		#Get all of the player names in the whitelist table
		MCSC_Cursor.execute("SELECT name FROM whitelist_Table")
		WhitelistedPlayers = MCSC_Cursor.fetchall()
		WhitelistedPlayers = [name[0] for name in WhitelistedPlayers]
		for item in WhitelistedPlayers:
			WhitelistListbox.insert(END,str(item))
		return
	
	def removeFromWhitelist():
		'removeFromWhitelist() -> Listbox Elements \n \n Updates the listbox elements. This function removes players from both the whitelist_Table in the database file and the Listbox'
		#Remove player from whitelist listbox
		global WhitelistListbox
		global ConsoleWindow
		whitelistChoice = WhitelistListbox.get()
		ServerFileIO.removePlayerfromWhitelist(str(whitelistChoice))
		WhitelistListbox.delete(WhitelistListbox.curselection())
		ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: Whitelist updated.")
		return
	
	#Banning Logic

	def issueBanbyName(PlayerName,banReason):
		'issueBanbyName(PlayerName,banReason) -> Database Query \n \n Issues a ban with the given PlayerName and includes the reason of the ban'
		global ConsoleWindow

		try:
			parseAPIQuery = requests.get("https://api.mojang.com/users/profiles/minecraft/" + str(PlayerName))
			if parseAPIQuery.status_code == 200:
				PlayerInfo = parseAPIQuery.json()
				#turn the id as a UUID object
				playeruuid = PlayerInfo["id"]
				uuidFull = uuid.UUID(str(playeruuid))
				PlayerInfo["id"] = str(uuidFull)
				#Get a timestamp
				currentTime = datetime.datetime.now()
				timeOffset = time.strftime('%z', time.gmtime())
				Timestamp = currentTime.strftime("%Y-%m-%d %H:%M:%S") + ' ' + timeOffset
				#And then finally
				BanInfo = [{"uuid": str(PlayerInfo["id"]),"name": str(PlayerInfo["name"]),"created": str(Timestamp),"source": "Minecraft Server Crafter","expires": "forever","reason": str(banReason)}]
				#Add to Table
				for item in BanInfo:
					MCSC_Cursor.execute("INSERT OR REPLACE INTO bannedPlayers_Table VALUES (?,?,?,?,?,?)",(item['uuid'],item['name'],item['created'],item['source'],item['expires'],item['reason']))
					MCSCDatabase.commit()
				ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: Ban Hammer was dropped on " + str(PlayerName) + ". REASON: " + str(banReason))
				return
			else:
				if parseAPIQuery.status_code == 204:
					#No Content
					raise Exception("[Minecraft Server Crafter]: Mojang API returned 204: No Content Raised")
				else:
					if parseAPIQuery.status_code == 400:
						#Bad Request
						errorInformation = parseAPIQuery.json()
						raise Exception("[Minecraft Server Crafter]: Mojang API returned with " + str(errorInformation["error"]) + ".\n Message from API: " + str(errorInformation["errorMessage"]))
					else:
						if parseAPIQuery.status_code == 405:
							#Method Not Allowed
							errorInformation = parseAPIQuery.json()
							raise Exception("[Minecraft Server Crafter]: Mojang API returned with " + str(errorInformation["error"]) + ".\n Message from API: " + str(errorInformation["errorMessage"]))
						else:
							if parseAPIQuery.status_code == 429:
								#Too many requests
								errorInformation = parseAPIQuery.json()
								raise Exception("[Minecraft Server Crafter]: Mojang API returned with " + str(errorInformation["error"]) + ".\n Message from API: " + str(errorInformation["errorMessage"]))

		except Exception as e:
			ConsoleWindow.displayException(e)
			if errorInformation:
				ConsoleWindow.updateConsole(END,"Mojang API Error - Additional Information\n =================== \n" + str(errorInformation))
			return
		
	def importplayerBansFromJSON():
		'importplayerBansFromJSON() -> JSON Query \n \n Logic for importing banned-players json file to bannedPlayers_Table in the database file.'
		global ServerJarSelection
		global ConsoleWindow

		#We need the server directory
		serverDir = ServerJarSelection.getcurrentpath()
		with open(str(serverDir) + "/banned-players.json","r") as bannedPlayersJSON:
			payloadData = json.load(bannedPlayersJSON)
			if payloadData:
				#Add to table
				insertQuery = "INSERT OR REPLACE INTO bannedPlayers_Table (uuid,name,created,source,expires,reason)"
				for item in payloadData:
					uuid = item['uuid']
					name = item['name']
					created = item['created']
					source = item['source']
					expires = item['expires']
					reason = item['reason']

					MCSC_Cursor.execute(insertQuery, (uuid,name,created,source,expires,reason))
					MCSCDatabase.commit()
				ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: Player Bans JSON successfully imported.")
			else:
				ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: The Player Bans JSON is empty so we don't need to do anything")
			bannedPlayersJSON.close()
		return
	
	def exportplayerBansToJSON():
		'exportplayerBansToJSON() -> Database Query \n \nLogic for exporting the bannedPlayers_Table to banned-players JSON file'
		#Get the player bans table from database
		global ServerJarSelection
		global ConsoleWindow

		serverDir = ServerJarSelection.getcurrentpath()
		bannedPlayers = []
		ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: Exporting player bans table...")
		MCSC_Cursor.execute("SELECT uuid, name, created, source, expires, reason FROM bannedPlayers_Table")
		bannedPlayersData = MCSC_Cursor.fetchall()
		for row in bannedPlayersData:
			playerData = {"uuid": row["uuid"],"name": row["name"],"created": row["created"],"source": row["source"],"expires": row["expires"],"reason": row["reason"]}
			bannedPlayers.append(playerData)
		with open(str(serverDir) + "/banned-players.json","w") as bannedPlayersWrite:
			json.dump(bannedPlayers,bannedPlayersWrite, indent=2)
			bannedPlayersWrite.close()
		ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: Player Bans Table has been successfully exported to JSON")
		return
	
	def pardonbyName(PlayerName):
		'pardonbyName(PlayerName) -> Database Query \n \n Logic for pardoning a player by removing them from the bannedPlayers_Table in the database file'
		global ConsoleWindow

		#Delete the player name from the database table
		selectQuery = "SELECT COUNT(*) FROM bannedPlayers_Table WHERE name = ?"
		MCSC_Cursor.execute(selectQuery,(PlayerName,))
		result = MCSC_Cursor.fetchone()
		if result[0] == 1:
			deleteQuery = "DELETE FROM bannedPlayers_Table WHERE name = ?"
			MCSC_Cursor.execute(deleteQuery, (PlayerName,))
			MCSCDatabase.commit()
			ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: Pardoned " + str(PlayerName))
			return
		else:
			ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: " + str(PlayerName) + " isn't found in the Ban Table.")
			return
	
	def importIPBansFromJSON():
		'importIPBansFromJSON() -> JSON Query \n \n Logic for importing banned-ips JSON file to bannedIPs_Table in the database file'
		global ServerJarSelection
		global ConsoleWindow

		ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: Importting IP bans from JSON...")
		serverDirectory = ServerJarSelection.getcurrentpath()
		with open(str(serverDirectory) + "/banned-ips.json","r") as bannedipsRead:
			banned_ips = json.load(bannedipsRead)
			if banned_ips:
				insertQuery = "INSERT OR REPLACE INTO bannedIPs_Table (ip,created,source,expires,reason)"
				for entry in banned_ips:
					ip = entry['ip']
					created = entry['created']
					source = entry['source']
					expires = entry['expires']
					reason = entry['reason']
				MCSC_Cursor.execute(insertQuery, (ip,created,source,expires,reason))
				MCSCDatabase.commit()
				ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: IP Bans has been imported from JSON file.")
			else:
				ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: The IP Bans JSON is empty, so we don't need to do anything")
			bannedipsRead.close()
		return
	
	def exportIPBansToJSON():
		'exportIPBansToJSON() -> Database Query \n \n Logic for exporting bannedIPs_Table in the database file to banned-ips JSON file.'
		global ServerJarSelection
		global ConsoleWindow

		ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: Exportting IP Bans Table...")
		serverdirectory = ServerJarSelection.getcurrentpath()
		selectQuery = "SELECT ip, created, source, expires, reason FROM bannedIPs_Table"
		MCSC_Cursor.execute(selectQuery)
		data = MCSC_Cursor.fetchall()
		#Transform the data into the desired format
		banned_ips = []
		for entry in data:
			ip, created, source, expires, reason = entry
			banned_ips.append({'ip': ip,'created': created, 'source': source, 'expires': expires, 'reason': reason})
		with open(str(serverdirectory) + "/banned-ips.json","w") as banIPWrite:
			json.dump(banned_ips,banIPWrite,indent=2)
		ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: IP Bans Table successfully exported, and saved to JSON file.")
		return
	
	def issueIPBan(ipAddress,reason):
		'issueIPBan(ipAddress,reason) -> Database Query \n \n Logic for banning an specific IP Address with the given ban reason'
		global ConsoleWindow
		
		try:
			ip = str(ipAddress)
			#Get a timestamp
			currentTime = datetime.datetime.now()
			timeOffset = time.strftime('%z', time.gmtime())
			Timestamp = currentTime.strftime("%Y-%m-%d %H:%M:%S") + ' ' + timeOffset
			#And then finally
			BanInfo = [{"ip": str(ip),"created": str(Timestamp),"source": "Minecraft Server Crafter","expires": "forever","reason": str(reason)}]
			#Add to Table
			for item in BanInfo:
				MCSC_Cursor.execute("INSERT OR REPLACE INTO bannedIPs_Table VALUES (?,?,?,?,?)",(item['ip'],item['created'],item['source'],item['expires'],item['reason']))
				MCSCDatabase.commit()
			ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: Ban Hammer was dropped on " + str(ip) + ". REASON: " + str(reason))
			return

		except ValueError as e:
			ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: An exception was raised. Heres a detailed walkthrough:")
			ConsoleWindow.displayException(e)
			MCSCDatabase.rollback()
			return
	
	def pardonbyIP(ipAddress):
		'pardonbyIP(ipAddress) -> Database Query \n \n Pardons an IP Address by removing them from the bannedIPs_Table'
		global ConsoleWindow

		#Delete the player name from the database table
		selectQuery = "SELECT COUNT(*) FROM bannedIPs_Table WHERE ip = ?"
		MCSC_Cursor.execute(selectQuery,(ipAddress,))
		result = MCSC_Cursor.fetchone()
		if result[0] == 1:
			deleteQuery = "DELETE FROM bannedIPs_Table WHERE ip = ?"
			MCSC_Cursor.execute(deleteQuery, (ipAddress,))
			MCSCDatabase.commit()
			ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: Pardoned " + str(ipAddress))
			return
		else:
			ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: " + str(ipAddress) + " isn't found in the Ban Table.")
			return
		
	def populateBannedPlayers_Listbox():
		'populateBannedPlayers_Listbox -> Database Query \n \n Logic for displaying the Banned Players in the Listbox.'
		global BannedPlayerNamesListbox

		#Is the player bans populated already?
		challengePlayerbansInt = BannedPlayerNamesListbox.size()
		if challengePlayerbansInt < 0:
			for i in enumerate(challengePlayerbansInt):
				BannedPlayerNamesListbox.delete(i)
		#Get all of the player names in the banned Players table
		MCSC_Cursor.execute("SELECT name FROM bannedPlayers_Table")
		bannedPlayersNames = MCSC_Cursor.fetchall()
		bannedPlayersNames = [name[0] for name in bannedPlayersNames]
		for item in bannedPlayersNames:
			BannedPlayerNamesListbox.insert(END,str(item))
		return
	
	def populateBannedIPs_Listbox():
		'populateBannedIPs_Listbox() -> Database Query \n \n Logic for displaying the Banned IPs in the Listbox.'
		global BannedIPsListbox

		#Is the IP Bans already populated?
		challengeIPBansInt = BannedIPsListbox.size()
		if challengeIPBansInt < 0:
			for i in enumerate(challengeIPBansInt):
				BannedIPsListbox.delete(i)
		#Get all of the ips in the banned ips table
		MCSC_Cursor.execute("SELECT ip FROM bannedIPs_Table")
		bannedIPs = MCSC_Cursor.fetchall()
		bannedIPs = [name[0] for name in bannedIPs]
		for item in bannedIPs:
			BannedIPsListbox.insert(END,str(item))
		return
	
	def attachServerJar():
		'attachServerJar() -> file process \n \nThe basic setup for attaching the minecraft server jar file to Minecraft Server Crafter. \nIf the given server directory has server.properties, banned-players.json, and banned-ips.json, then they are imported to Minecraft Server Crafter. \nOtherwise, these operations are skipped.'
		global root
		global root_tabs
		global ConsoleWindow
		global jar_filenamePath
		global currentjar_SelectedPath
		global ServerTypeImage
		global ServerJarSelection

		root_tabs.set("Console Shell")
		ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: Attaching Jar file(File Operations can take a few seconds, and are operating in the background. Please do not close Minecraft Server Crafter during these operations)...")
		#We need to first select the initial directory for selecting a server jar
		startingDir = str(rootFilepath)
		initial_dir = filedialog.askdirectory(parent=root, title="Select Server Directory",initialdir=startingDir,mustexist=True)
		initial_dir = str(initial_dir) + "/"
		ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter API - ServerFileIO]: Scanning for server.properties...")
		if os.path.isfile(str(initial_dir) + "server.properties") == True:
			ConsoleWindow.updateConsole(END, "[Minecraft Server Crafter API - ServerFileIO]: Properties file detected. Importing...")
			ServerFileIO.importPropertiestoJSON(initial_dir)
			print(MinecraftServerProperties)
			ConsoleWindow.updateConsole(END, "[Minecraft Server Crafter API - ServerFileIO]: Import Successful. Saving new JSON data...")
			ServerFileIO.exportPropertiestoJSON()
			ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter API - ServerFileIO]: Properties Saved. Finalizing...")
			ServerFileIO.loadJSONProperties()
			ConsoleWindow.updateConsole(END, "[Minecraft Server Crafter API - ServerFileIO]: Structure Rebuilt Successfully. Continuing Operation.")
		else:
			ConsoleWindow.updateConsole(END, "[Minecraft Server Crafter API - ServerFileIO]: No server.properties detected. Skipping...")
			return
		
		try:
			if not os.path.exists(initial_dir):
				#User selected a option but then backed out of it
				raise Exception("[Minecraft Server Crafter - ErrorReporting]: The Server Directory doesn't exist. Will not proceed.")
			if initial_dir == "/":
				#User didn't attempt to select a directory outside of minecraft server crafter's root directory
				raise Exception("[Minecraft Server Crafter - ErrorReporting]: The Server Directory and the Minecraft Server Crafter are the same. Will not proceed.")
			else:
				#Mod/Plugin detection
				jar_filenamePath = initial_dir
				#Update the view
				global ServerJarSelection
				os.chdir(jar_filenamePath)
				ServerJarSelection = FileSelectWindow(root)
				ServerJarSelection.passrootDirectory(rootFilepath)
				ServerJarSelection.updateView(initial_dir)
				ServerJarSelection.haltbackgroundexecution()
				currentjar_SelectedPath = ServerJarSelection.getcurrentpath()
				jar_filenamePath = ServerJarSelection.getFilepathString()
			
				if os.path.isfile(str(initial_dir) + "whitelist.json") == True:
					ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter API - ServerFileIO]: Whitelist File detected.")
					ServerFileIO.importWhitelistfromJSON()
					ServerFileIO.populateWhitelist_Listbox()
				else:
					ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter API - ServerFileIO]: No whitelist.json detected. Skipping...")
				if os.path.isfile(str(initial_dir) + "banned-players.json") == True:
					ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter API - ServerFileIO]: Banned Players File detected.")
					ServerFileIO.importplayerBansFromJSON()
					ServerFileIO.populateBannedPlayers_Listbox()
				else:
					ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter API - ServerFileIO]: No banned-players.json detected. Skipping...")
				if os.path.isfile(str(initial_dir) + "banned-ips.json") == True:
					ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter API - ServerFileIO]: Banned IPs File detected.")
					ServerFileIO.importIPBansFromJSON()
					ServerFileIO.populateBannedIPs_Listbox()
				else:
					ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter API - ServerFileIO]: No banned-ips.json detected. Skipping...")
				if ServerJarSelection.getClosedWindowBool() == True:
					#The window was closed
					ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: Window Closed. Will not proceed.")
					return
				else:
					#We need to do somethings
					#Step 1: Get the name of the file selected. We need to know what type of server it is.
					selected_file = ServerJarSelection.getFilepathString()
					selected_file = os.path.basename(selected_file)
					fileCheck = [name for name in possibleJarNames if selected_file.startswith(name)]
					filenameQuery = ''.join(fileCheck)
					#Is it a fork?
					detectedClass = str(ServerFileIO.scanJarForServerType())
					for file in selected_file:
						if filenameQuery == "server" or filenameQuery == "minecraft-" and detectedClass == "Minecraft Vanilla": #The default name for the Minecraft Vanilla Server is server.jar
							#We dont need to do anything. Its a vanilla server
							ServerTypeImageData = CTkImage(dark_image=Image.open(str(rootFilepath) + "/base/ui/minecraft_vanilla_source.png"),size=(100,100))
							ServerTypeImage.configure(image=ServerTypeImageData,text_color="white")
							MCSC_Framework.onMainWindow_setTabState(root_tabs,"Server Properties File",NORMAL)
							MCSC_Framework.onMainWindow_setTabState(root_tabs,"Whitelisting",NORMAL)
							MCSC_Framework.onMainWindow_setTabState(root_tabs,"Banned Players",NORMAL)
							launchServerBtn.configure(state=NORMAL)
							ConsoleWindow.updateConsole(END,"<Minecraft Server Crafter>: The Minecraft Vanilla server Jar has been selected. ")
							return
						else:
							if filenameQuery == "purpur-" and detectedClass == "Paper":
								#Purpur is based off of a fork of paper
								ServerTypeImageData = CTkImage(dark_image=Image.open(str(rootFilepath) + "/base/ui/purpur_source.png"),size=(100,100))
								ServerTypeImage.configure(image=ServerTypeImageData,text_color="white")
								MCSC_Framework.onMainWindow_setTabState(root_tabs,"Server Properties File",NORMAL)
								MCSC_Framework.onMainWindow_setTabState(root_tabs,"Whitelisting",NORMAL)
								MCSC_Framework.onMainWindow_setTabState(root_tabs,"Banned Players",NORMAL)
								launchServerBtn.configure(state=NORMAL)
								ConsoleWindow.updateConsole(END,"<Minecraft Server Crafter>: Purpur, a fork of Paper, has been selected.")
								return
							else:
								if filenameQuery == "spigot-" and detectedClass == "CraftBukkit":
									#Spigot is a fork of CraftBukkit
									ServerTypeImageData = CTkImage(dark_image=Image.open(str(rootFilepath) + "/base/ui/spigot_source.png"),size=(100,100))
									ServerTypeImage.configure(image=ServerTypeImageData,text_color="white")
									MCSC_Framework.onMainWindow_setTabState(root_tabs,"Server Properties File",NORMAL)
									MCSC_Framework.onMainWindow_setTabState(root_tabs,"Whitelisting",NORMAL)
									MCSC_Framework.onMainWindow_setTabState(root_tabs,"Banned Players",NORMAL)
									launchServerBtn.configure(state=NORMAL)
									ConsoleWindow.updateConsole(END,"<Minecraft Server Crafter>: Spigot, a fork of CraftBukkit, has been selected.")
									return
								else:
									if filenameQuery == "paper-" and detectedClass == "Paper":
										ServerTypeImageData = CTkImage(dark_image=Image.open(str(rootFilepath) + "/base/ui/paper_source.png"),size=(100,100))
										ServerTypeImage.configure(image=ServerTypeImageData,text_color="blue")
										MCSC_Framework.onMainWindow_setTabState(root_tabs,"Server Properties File",NORMAL)
										MCSC_Framework.onMainWindow_setTabState(root_tabs,"Whitelisting",NORMAL)
										MCSC_Framework.onMainWindow_setTabState(root_tabs,"Banned Players",NORMAL)
										launchServerBtn.configure(state=NORMAL)
										ConsoleWindow.updateConsole(END,"<Minecraft Server Crafter>: Paper has been selected.")
										return
									else:
										if filenameQuery == "fabric-" and detectedClass == "Fabric":
											ServerTypeImageData = CTkImage(dark_image=Image.open(str(rootFilepath) + "/base/ui/fabric_source.png"),size=(100,100))
											ServerTypeImage.configure(image=ServerTypeImageData,text_color="white")
											MCSC_Framework.onMainWindow_setTabState(root_tabs,"Server Properties File",NORMAL)
											MCSC_Framework.onMainWindow_setTabState(root_tabs,"Whitelisting",NORMAL)
											MCSC_Framework.onMainWindow_setTabState(root_tabs,"Banned Players",NORMAL)
											launchServerBtn.configure(state=NORMAL)
											ConsoleWindow.updateConsole(END,"<Minecraft Server Crafter>: Fabric has been selected.")
											return
										else:
											if filenameQuery == "craftbukkit-" and detectedClass == "CraftBukkit":
												ServerTypeImageData = CTkImage(dark_image=Image.open(str(rootFilepath) + "/base/ui/craftbukkit_source.png"),size=(100,100))
												ServerTypeImage.configure(image=ServerTypeImageData,text_color="blue")
												MCSC_Framework.onMainWindow_setTabState(root_tabs,"Server Properties File",NORMAL)
												MCSC_Framework.onMainWindow_setTabState(root_tabs,"Whitelisting",NORMAL)
												MCSC_Framework.onMainWindow_setTabState(root_tabs,"Banned Players",NORMAL)
												launchServerBtn.configure(state=NORMAL)
												ConsoleWindow.updateConsole(END,"<Minecraft Server Crafter>: CraftBukkit has been selected.")
												return
											else:
												MCSC_Framework.onMainWindow_setTabState(root_tabs,"Server Properties File",NORMAL)
												MCSC_Framework.onMainWindow_setTabState(root_tabs,"Whitelisting",NORMAL)
												MCSC_Framework.onMainWindow_setTabState(root_tabs,"Banned Players",NORMAL)
												launchServerBtn.configure(state=NORMAL)
												ConsoleWindow.updateConsole(END,"<Minecraft Server Crafter>: The Server jar has been selected.")
												return
					
		except Exception as e:
			#Detailed Walkthrough
			ConsoleWindow.displayException(e)
			return
	
	def exportJSONtoProperties(): #Applies Changes from the JSON data to the server.properties file when a jar is present
		'exportJSONtoProperties(serverjarpath) -> saves to serverjarpath \n \n Saves the MinecraftServerProperties JSON model from memory to server.properties \n while retaining the server.properties model and only updating the values'
		global ServerJarSelection
		#First we get the Json file data
		with open(str(rootFilepath) + "/properties.json", "r") as jsonPayload:
			raw_data = json.load(jsonPayload)
			jsonPayload.close()
		payload_dict = {}
		payload_dict = raw_data
		#We need to use the variable ServerJarSelection
		ServerDirectory = ServerJarSelection.getcurrentpath()
		with open(ServerDirectory + "/server.properties","r+") as propertiesFile:
			lines = propertiesFile.readlines()
			for key,value in payload_dict.items():
				for line in lines[2:]:
					if line.startswith(key):
						value = payload_dict.get(key)
						if value is None:
							value = ""
							propertiesFile.write(f"{key}={value}\n")
							continue
						else:
						#Now we just put in the key value pair
							propertiesFile.write(f"{key}={value}\n")
							continue
			propertiesFile.close()
		return
	
	def importPropertiesfromFile():
		'importPropertiesfromFile() -> File Operation \n \n Prompts the User to select the server directory for importing a server.properties file to JSON Model'
		global ConsoleWindow
		global root_tabs
		root_tabs.set("Console Shell")
		try:
			askPropertiesFile = filedialog.askdirectory(parent=root,initialdir=str(rootFilepath),title="Select Server Directory with the server.properties File")
			if os.path.isfile(str(askPropertiesFile) + "/server.properties") == False:
				raise FileNotFoundError("[Minecraft Server Crafter]: [Error-32] Server.properties does not exist. This usually means either its a new server, or user did not give the correct path")
			else:
				ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: Loading server.properties to JSON Model...")
				ServerFileIO.importPropertiestoJSON(askPropertiesFile)
				ServerFileIO.loadJSONProperties()
				ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: JSON Model has been updated, and values has been updated.")
				return
		except FileNotFoundError as e:
			ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: Exception raised. Here's a detailed walkthrough below")
			ConsoleWindow.displayException(e)
			return
		
	def exportToJSONModel():
		'exportToJSONModel() -> Save operation \n \n Exports the Properties JSON Model to properties.json'
		global ConsoleWindow
		global root_tabs
		root_tabs.set("Console Shell")
		#We need to update values
		MinecraftServerProperties["enable-jmx-monitoring"] = jmxMonitoringBool.get()
		MinecraftServerProperties["rcon.port"] = rconportIntVar.get()
		MinecraftServerProperties["level-seed"] = levelSeedStringVar.get()
		MinecraftServerProperties["gamemode"] = gamemodeStringVar.get()
		MinecraftServerProperties["enable-command-block"] = usecmdBlocksBoolVar.get()
		MinecraftServerProperties["enable-query"] = togglequery.get()
		MinecraftServerProperties["generator-settings"] = generatorsettingsvar.get()
		MinecraftServerProperties["level-name"] = WorldNameStringVar.get()
		MinecraftServerProperties["query.port"] = queryportIntVar.get()
		MinecraftServerProperties["pvp"] = isPVPBool.get()
		MinecraftServerProperties["generate-structures"] = structureGeneration.get()
		MinecraftServerProperties["difficulty"] = worldDifficultyVar.get()
		MinecraftServerProperties["network-compression-threshold"] = NetworkCompressionIntVar.get()
		MinecraftServerProperties["max-tick-time"] = ticktimeIntVar.get()
		MinecraftServerProperties["require-resource-pack"] = resourcePackRequirementBool.get()
		MinecraftServerProperties["max-players"] = maxplayersIntVar.get()
		MinecraftServerProperties["use-native-transport"] = nativeTransport.get()
		MinecraftServerProperties["online-mode"] = toggleOnlineMode.get()
		MinecraftServerProperties["enable-status"] = statusBool.get()
		MinecraftServerProperties["allow-flight"] = canFly.get()
		MinecraftServerProperties["broadcast-rcon-to-ops"] = broadcastrconBool.get()
		MinecraftServerProperties["view-distance"] = viewDistanceIntVar.get()
		MinecraftServerProperties["resource-pack-prompt"] = resourcePackPromptStringVar.get()
		MinecraftServerProperties["server-ip"] = IPAddressEntry.get()
		MinecraftServerProperties["allow-nether"] = netherDimension.get()
		MinecraftServerProperties["server-port"] = serverportIntVar.get()
		MinecraftServerProperties["enable-rcon"] = togglerconBool.get()
		MinecraftServerProperties["sync-chunk-writes"] = chunkwriteSyncingBool.get()
		MinecraftServerProperties["op-permission-level"] = opPermissionlvlIntVar.get()
		MinecraftServerProperties["prevent-proxy-connections"] = proxyBlockingBool.get()
		MinecraftServerProperties["hide-online-players"] = onlinePlayersHiddenBool.get()
		MinecraftServerProperties["entity-broadcast-range-percentage"] = entitybroadcastRangeIntVar.get()
		MinecraftServerProperties["simulation-distance"] = simulationDistanceIntVar.get()
		MinecraftServerProperties["rcon.password"] = rconPasswordStringVar.get()
		MinecraftServerProperties["player-idle-timeout"] = playertimeoutIntVar.get()
		MinecraftServerProperties["force-gamemode"] = strictGamemodeBool.get()
		MinecraftServerProperties["rate-limit"] = ratelimitIntvar.get()
		MinecraftServerProperties["hardcore"] = isHardcoreWorldBool.get()
		MinecraftServerProperties["white-list"] = whitelistedBool.get()
		MinecraftServerProperties["broadcast-console-to-ops"] = broadcastConsoleBool.get()
		MinecraftServerProperties["spawn-npcs"] = npcSpawning.get()
		MinecraftServerProperties["spawn-animals"] = animalSpawning.get()
		MinecraftServerProperties["function-permission-level"] = functionPermissionlvlIntvar.get()
		MinecraftServerProperties["level-type"] = worldtypeStringVar.get()
		MinecraftServerProperties["spawn-monsters"] = enemySpawning.get()
		MinecraftServerProperties["enforce-whitelist"] = strictedWhitelistBool.get()
		MinecraftServerProperties["spawn-protection"] = spawnprotectionRadiusInt.get()
		MinecraftServerProperties["max-world-size"] = worldsizeInt.get()
		MinecraftServerProperties["enforce-secure-profile"] = strictProfileBool.get()
		MinecraftServerProperties["max-chained-neighbor-updates"] = neighborupdatesIntVar.get()
		MinecraftServerProperties["initial-disabled-packs"] = disableddataPackStringVar.get()
		MinecraftServerProperties["initial-enabled-packs"] = enableddatapacksStringVar.get()
		MinecraftServerProperties["log-ips"] = isIPLogging.get()
		#Update the dictionary
		MinecraftServerProperties.update()
		ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: Saving JSON Model...")
		ServerFileIO.exportPropertiestoJSON()
		ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: Properties Saved.")
		return
	
	def convertJSONPropertiestoPropertiesFile(filepath,bypassSaveLocation=False):
		'convertJSONPropertiestoPropertiesFile(filepath) -> properties.json => server.properties \n \nConverts the properties.json Model to server.properties. \nIf bypassSaveLocation is True, the server.properties \n file is written to filepath of the server directory without asking for an save location'
		global ConsoleWindow
		global root_tabs
		ServerFileIO.exportToJSONModel()
		ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: Converting JSON Model...")
		#First we get the Json file data
		with open(str(rootFilepath) + "/properties.json", "r") as jsonPayload:
			raw_data = json.load(jsonPayload)
			jsonPayload.close()
		payload_dict = {}
		payload_dict = raw_data
		del payload_dict['debug'] #Weird inclusion in the json. This inclusion is on Mojangs end. This option was added back in beta 1.9, but then was later removed from the properties file
		#We need to use the variable ServerJarSelection
		if bypassSaveLocation == False:
			askSaveLocation = filedialog.askdirectory(initialdir=filepath,parent=root,title="Select Server Directory")
			if askSaveLocation == None:
				return
			if os.path.isfile(str(askSaveLocation) + "/server.properties") != True:
				#Lets make one with the header
				with open(str(askSaveLocation) + "/server.properties","w") as generatePropertiesFile:
					#A cheaty way of doing this, but ¯\_(ツ)_/¯
					generatePropertiesFile.write("#Minecraft server properties\n#Fri Aug 18 11:20:03 EDT 2023\n")
					generatePropertiesFile.close()
				with open(str(askSaveLocation) + "/server.properties","a") as propertiesfile:
					for key,value in payload_dict.items():
						if value == None:
							value = ""
						propertiesfile.write(f"{key}={value}\n")
					propertiesfile.close()
				ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: JSON Model Converted. Verify Settings before launching a server.")
				return
			else:
				if os.path.isfile(str(askSaveLocation) + "/server.properties") == True:
					with open(str(askSaveLocation) + "/server.properties","w") as propertiesFile:
						#A cheaty way of doing this but ¯\_(ツ)_/¯
						propertiesFile.write("#Minecraft server properties\n#Fri Aug 18 11:20:03 EDT 2023\n")
						for Key,val in payload_dict.items():
							if val == None:
								val = ""
							propertiesFile.write(f"{Key}={val}\n")
					#Merge the properties
				ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: JSON Model Converted. Verify Settings before launching a server.")
				return
		else:
			#We need to save the file in the given directory
			if os.path.isfile(str(filepath) + "/server.properties") != True:
				#Lets make one with the header
				with open(str(filepath) + "/server.properties","w") as generatePropertiesFile:
					#A cheaty way of doing this, but ¯\_(ツ)_/¯
					generatePropertiesFile.write("#Minecraft server properties\n#Fri Aug 18 11:20:03 EDT 2023\n")
					generatePropertiesFile.close()
				with open(str(filepath) + "/server.properties","a") as propertiesfile:
					for key,value in payload_dict.items():
						if value == None:
							value = ""
						propertiesfile.write(f"{key}={value}\n")
					propertiesfile.close()
				ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: JSON Model Converted. Verify Settings before launching a server.")
				return
			else:
				if os.path.isfile(str(filepath) + "/server.properties") == True:
					with open(str(filepath) + "/server.properties","w") as propertiesFile:
						#A cheaty way of doing this but ¯\_(ツ)_/¯
						propertiesFile.write("#Minecraft server properties\n#Fri Aug 18 11:20:03 EDT 2023\n")
						for Key,val in payload_dict.items():
							if val == None:
								val = ""
							propertiesFile.write(f"{Key}={val}\n")
					#Merge the properties
				ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: JSON Model Converted. Verify Settings before launching a server.")
				return
		
	def ResourcePackCall_generateSHA1(url=None):
		'ResourcePackCall_generateSHA1(url) -> Tuple List \n \nDownloads the Resource Pack from the direct download url, hashes the file and file contents and stored into a list object into its index value.\n \nTuple List Index Reference\n========================\n \nIndex value 0 - 1st Zipfile hash \n \nIndex Value 1 - 1st Zipfile Contents Hash \n \nIndex value 2 - 2nd Zipfile hash \n \nIndex Value 3 - 2nd Zipfile Contents Hash \n \nIndex Value 4 - Verification Bool'
		#We need to download the zipfile and generate a sha1 from url
		global ConsoleWindow
		global root_tabs

		root_tabs.set("Console Shell")

		ConsoleWindow.updateConsole(END, "[Minecraft Server Crafter]: Downloading Resource Pack from: " + str(url))
		try:
        	# Create two temporary files
			with NamedTemporaryFile(delete=False) as temp_file1, NamedTemporaryFile(delete=False) as temp_file2:
				# Download the file twice into the temporary files
				response1 = requests.get(url, stream=True)
				response2 = requests.get(url, stream=True)
				if response1.status_code != 200 or response2.status_code != 200:
					raise ValueError(f"Failed to download file from URL: {url}")

				for chunk1, chunk2 in zip(response1.iter_content(chunk_size=65536), response2.iter_content(chunk_size=65536)):
					temp_file1.write(chunk1)
					temp_file2.write(chunk2)

				# Calculate hashes from both downloads
				sha1_hash1 = hashlib.sha1()
				sha1_hash2 = hashlib.sha1()

				with open(temp_file1.name, "rb") as file1, open(temp_file2.name, "rb") as file2:
					while True:
						data1 = file1.read(65536)
						data2 = file2.read(65536)
						if not data1 or not data2:
							break
						sha1_hash1.update(data1)
						sha1_hash2.update(data2)

				# Get the final hash values
				hash1 = sha1_hash1.hexdigest()
				hash2 = sha1_hash2.hexdigest()

				# Verify the hashes
				verification_result = hash1 == hash2
				
				ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: File has been downloaded and verified.")
				return [hash1, {"contents_hash": sha1_hash1.hexdigest()}, hash2, {"contents_hash": sha1_hash2.hexdigest()}, verification_result]

		except ValueError as e:
			# Error handling code
			ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: Exception Raised. Heres a detailed walkthrough: ")
			ConsoleWindow.displayException(e)
			return (None, None, None, None, False)
	
	def askAddWhitelistPlayer():
		'askAddWhitelistPlayer() -> User Input Operation \n \n Prompts the user to input a player name to add to the whitelist'
		global WhitelistListbox
		global ConsoleWindow
		#Push a input dialog
		challengeDialog = CTkInputDialog(text="What is the player's name you want to add?",title="Minecraft Server Crafter - Add Whitelist Player Challenge")
		challengeDialog_playername = challengeDialog.get_input()
		if challengeDialog_playername == None:
			return
		#Add to whitelist table
		ServerFileIO.addPlayerToWhitelist(str(challengeDialog_playername))
		#Update the listbox
		WhitelistListbox.delete(0,END)
		ServerFileIO.populateWhitelist_Listbox()
		ConsoleWindow.updateConsole(END,"[Minecraft Server Crafter]: Whitelist updated.")
		return
	
	def askBanPlayerName():
		'askBanPlayerName() -> User Input Operation \n \n Prompts the user to input a player name to ban the given name. When a name is provided, it then prompts the user to give a reason of the ban.'
		global ConsoleWindow
		challengedialog_player = CTkInputDialog(title="Minecraft Server Crafter - Issue Player Ban",text="What's the Player Name that you want to ban?")
		banName = challengedialog_player.get_input()
		if banName == None:
			return
		challengedialog_Banreason = CTkInputDialog(title="Minecraft Server Crafter - Issue Player Ban - Ban Reason",text="Why do want to ban " + str(banName) + "?")
		BanReason = challengedialog_Banreason.get_input()
		ServerFileIO.issueBanbyName(str(banName),str(BanReason))
		ServerFileIO.populateBannedPlayers_Listbox()
		return
	
	def askIPBan():
		'askBanPlayerName() -> User Input Operation \n \n Prompts the user to input an IP Address to ban the given IP. When a IP Address is provided, it then prompts the user to give a reason of the ban.'
		global ConsoleWindow
		challengedialog_ip = CTkInputDialog(title="Minecraft Server Crafter - Issue IP Ban",text="What's the IP Address that you want to ban?")
		banIP = challengedialog_ip.get_input()
		if banIP == None:
			return
		challengedialog_banreason = CTkInputDialog(title="Minecraft Server Crafter - Issue IP Ban - Ban Reason",text="Why do want to ban " + str(banIP) + "?")
		banreason = challengedialog_banreason.get_input()
		ServerFileIO.issueIPBan(banIP,str(banreason))
		ServerFileIO.populateBannedIPs_Listbox()
		return
	
	def PardonName():
		'PardonName() -> Listbox Element \n \n Updates the listbox. When the user pardons a player, it both updates the listbox and the table in the database file'
		#We need to get the player's name from the listbox that we are pardoning
		selectedName = BannedPlayerNamesListbox.get()
		ServerFileIO.pardonbyName(str(selectedName))
		BannedPlayerNamesListbox.delete(BannedPlayerNamesListbox.curselection())
		ServerFileIO.populateBannedPlayers_Listbox()
		return
	
	def PardonIP():
		'PardonName() -> Listbox Element \n \n Updates the listbox. When the user pardons a ip address, it both updates the listbox and the table in the database file'
		selectedIP = BannedIPsListbox.get()
		ServerFileIO.pardonbyIP(str(selectedIP))
		BannedIPsListbox.delete(BannedIPsListbox.curselection())
		ServerFileIO.populateBannedIPs_Listbox()
		return

ServerFileIO.loadJSONProperties()

VersionRelease = str(versionType)
VersionNumber = str(version)
releaseVersion = " - Version: " + str(VersionRelease) + "-" + str(VersionNumber)
InstalledMemory = HardwareSpec.getByteSizeInt(psutil.virtual_memory().total)
ScaledMem = InstalledMemory[0]
roundedMem = round(ScaledMem)
truncatedMem = math.trunc(roundedMem)
physicalMem = int(truncatedMem)
if InstalledMemory[1] == "MB":
	#Scale it in Megabytes
	MemoryAllocationCap = int(truncatedMem) - 5120
	#For a decent server, the minium amount of memory is 2GB(2048)
	MiniumMemory = 2048
if InstalledMemory[1] == "GB":
	#Scale it in Gigabytes
	MemoryAllocationCap = int(truncatedMem) - 5
	MiniumMemory = 2
currentMemoryMinimum = int(4)
currentMemoryMax = int(4)


class MCSC_Framework():
	def onMainWindow_setTabState(widget,tabName,state):
		selectedWidget = widget
		selectedWidget._segmented_button._buttons_dict[str(tabName)].configure(state=str(state))
		return
	def onMainWindow_onExit():
		ServerFileIO.exportPropertiestoJSON()
		root.destroy()
		sys.exit(0)

	def onMainWindow_openResourcePackConfig():
		resourcePackConfig = ResourcePackWindow(root)
		return
	def onMainWindow_openMOTDConfig():
		motdConfig = MOTDWindow(root)
		return
	def setup_STDOUT_REDIRECTION(widget,tag):
		stdoutRedirect = TextRedirector(widget,tag=str(tag))
		sys.stdout = stdoutRedirect
		return

root = CTk()
root.title("Minecraft Server Crafter" + str(releaseVersion))
root.geometry("620x279")
root.protocol('WM_DELETE_WINDOW', MCSC_Framework.onMainWindow_onExit)
root.resizable(False,False)
#Check the Operating System for the main window icon
if sys.platform.startswith("win32"):
	root.iconbitmap(str(rootFilepath) + "/base/ui/minecraftservercrafter.ico")
if sys.platform.startswith("linux"):
	root.iconbitmap("@" + str(rootFilepath) + "/base/ui/minecraftservercrafter-icon.xbm")
if sys.platform.startswith("darwin"):
	#Unsure if this will work, will pay close attention to Mac Users
	root.iconbitmap(str(rootFilepath) + "/base/ui/Mac_icon-minecraftservercrafter.icns")
#We need to put in a tab view

root_tabs = CTkTabview(root,width=250)
root.rowconfigure(0,weight=1)
root.columnconfigure(2,weight=1)
root_tabs.grid(row=0,column=2,sticky="nsew")
root_tabs.add("Console Shell")
root_tabs.add("Server Properties File")
root_tabs.add("Whitelisting")
root_tabs.add("Banned Players")
root_tabs.add("Minecraft Server Crafter Settings")

#Statically let the appearance mode to Dark Mode
set_appearance_mode("dark")

class TextRedirector(object):
	def __init__(self, widget,tag="stdout"):
		self.widget = widget
		self.tag = tag
	
	def write(self,string):
		self.widget.configure(state=NORMAL)
		self.widget.insert(END,string,(self.tag))
		self.widget.configure(state=DISABLED)

class ConsoleShell(CTkFrame):
	def __init__(self,parent):
		self.parent = parent
		process2 = None
		outputThread = None
		self.pauseEvent = threading.Event()

		self.root = CTkCanvas(self.parent)
		self.root.grid(row=0,column=0,sticky="nsew")
		self.ConsoleCanvas = CTkCanvas(self.root)
		self.ConsoleCanvas.grid(row=0,column=0,sticky="nsew")
		self.ConsoleOut = CTkTextbox(self.ConsoleCanvas, width=400, corner_radius=0,state="disabled",bg_color="black")
		self.ConsoleOut.pack(fill=BOTH,expand=True,anchor="center")
		self.ConsoleOut.tag_config("stderr",foreground="#b22222")
		self.InputCanvas = CTkCanvas(self.root)
		self.InputCanvas.grid(row=1,column=0,sticky="nsew")
		self.ConsoleIn = CTkEntry(self.InputCanvas,placeholder_text="Input a command",bg_color="black")
		self.ConsoleIn.pack(fill=X,ipadx=200,side=LEFT)
		self.SendBtn = CTkButton(self.InputCanvas,text="Send",bg_color="black",command=lambda:self.ServerProcess_OnTransmitInput())
		self.SendBtn.pack(side=RIGHT)
		self.root.rowconfigure(0,weight=1)
		self.root.rowconfigure(1,weight=2)
		self.root.columnconfigure(0,weight=1)

	def SaveConsoleToFile(self,start,end):
		global root_tabs
		'SaveConsoleToFile(startingIndex,EndingIndex) -> File Operation \n \n Saves the Console Shell Text to a log file.'

		root_tabs.set("Console Shell")
		#Get whats all in the Console
		self.updateConsole(END,"[Minecraft Server Crafter]: Saving Console Log...")
		self.ConsoleOut.configure(state="normal")
		data = self.ConsoleOut.get(start,end)
		file = filedialog.asksaveasfile(mode='w',defaultextension='.log',filetypes=[("Log File",".log")],confirmoverwrite=True)
		if file is None:
			return
		file.write(data)
		file.close()
		self.ConsoleOut.configure(state="disabled")
		self.updateConsole(END,"[Minecraft Server Crafter]: Console Log saved.")
		return
	
	def displayException(self,exception):
		'displayException(exception) -> Exception Trace \n \n Sends any exceptions given from python to the Console Shell instead.'
		self.exceptionDetailData = traceback.extract_tb(exception.__traceback__)
		self.filepath,self.lineNumber,self.functionName,self.line = self.exceptionDetailData[-1]
		self.exceptionDetails = f"[Minecraft Server Crafter - ErrorReporting]: [Error-301]\n \n=====BEGINNING OF WALKTHROUGH===== \n \nException Type: {type(exception).__name__} \nFilepath Location: {self.filepath} \nLine Number: {self.lineNumber} \nFunction Name: {self.functionName} \nLine Contents: {self.line}\nMessage: {str(exception)} \n \n=====END OF WALKTHROUGH===== \n \n"
		self.updateConsole(END,self.exceptionDetails)
		traceback.print_exception(exception)
		return

	def updateConsole(self,index,string):
		'updateConsole(index,string) -> Console Output \n \n Prints the given string to the ConsoleShell'
		self.ConsoleOut.configure(state="normal")
		self.ConsoleOut.insert(index,str(string) + '\n')
		self.ConsoleOut.configure(state="disabled")
		self.ConsoleOut.see(END)
		return
	
	def ServerProcess_OnTransmitInput(self):
		'ServerProcess_OnTransmitInput() -> Server Input \n \nPasses input to stdin of the Minecraft Server on its own Thread. \nIf the server isn\'t running, nothing is sent to the subprocess.'
		def SendInput():
			serverRunning = outputThread.is_alive()
			if process2.returncode is None and serverRunning == True:
				inputQuery = str(self.ConsoleIn.get())
				self.updateConsole(END, "[Minecraft Server Crafter]: <User-Input>: " + str(inputQuery))
				process2.stdin.write(str(inputQuery))
				process2.stdin.write('\n')  # Add a newline character to simulate pressing Enter
				process2.stdin.flush()
				self.ConsoleIn.delete(0,END)
				for line in process2.stdout:
					self.updateConsole(END, "[Minecraft Server Crafter]: <Server-IO>: " + line.strip())

			else:
				self.updateConsole(END, '[Minecraft Server Crafter]: Server is not running. Will not proceed')
				self.ConsoleIn.delete(0, END)
				return

		global process2
		global outputThread

		try:
			inputThread = threading.Thread(target=SendInput)
			inputThread.start()
		except SystemExit:
			inputThread.join()
	
	def beginServerProcess(self, memoryAllocation=False, initialMemory=0, maxMemory=0):
		'beginServerProcess(memoryAllocation=False,initialMemory=0,maxMemory=0) -> Server Startup \n \n Begins the Minecraft Server. If memoryAllocation is True, then memory allocation(measured in MB) for the Java VM is included in building the java command, otherwise its exempted. \n The initialMemory parameter sets the minimum memory, and the maxMemory sets the maxium memory.'
		def print_output(process):
			for line in process2.stdout:
				self.updateConsole(END,"[Minecraft Server Crafter]: <Server-IO>: " + line.strip())
				time.sleep(0.1)
			returnCode = process.wait()
			self.updateConsole(END,"Command exited with the return code " + str(returnCode))
		global ServerJarSelection
		global root_tabs
		global process2
		global outputThread
		global jar_filenamePath
		global MemoryAllocationCap

		root_tabs.set("Console Shell")
		self.killEvent = False
		#We need to do some magic
		selectedJarString = os.path.split(str(ServerJarSelection.getFilepathString()))
		serverDirectory = str(selectedJarString[0])
		selectedJar = str(selectedJarString[1])
		if memoryAllocation:
			currentScaledMemory = str(InstalledMemory[1])
			if currentScaledMemory == "GB":
				#We need to scale the command so it measures the values in GB
				cmd = ['java', f'-Xms{initialMemory}G', f'-Xmx{maxMemory}G', '-jar', str(selectedJar), '-nogui']
			if currentScaledMemory == "MB":
				#We need to scale the command so it measures the values in MB
				cmd = ['java', f'-Xms{initialMemory}M', f'-Xmx{maxMemory}M', '-jar', str(selectedJar), '-nogui']
		else:
			cmd = ['java', '-jar', str(selectedJar), '-nogui']
		self.updateConsole(END,"[Minecraft Server Crafter]: Using java command: " + str(cmd))
		time.sleep(0.1)
		#Update the server.properties file
		self.updateConsole(END,"[Minecraft Server Crafter]: Pre-Server Startup Phase: Updating server.properties...")
		time.sleep(0.1)
		ServerFileIO.convertJSONPropertiestoPropertiesFile(str(serverDirectory),bypassSaveLocation=True)
		#Update the JSON Bans
		self.updateConsole(END,"[Minecraft Server Crafter]: Pre-Server Startup Phase: Updating JSON Bans[1/2]...")
		time.sleep(0.1)
		ServerFileIO.exportplayerBansToJSON()
		self.updateConsole(END,"[Minecraft Server Crafter]: Pre-Server Startup Phase: Updating JSON Bans[2/2]...")
		time.sleep(0.1)
		ServerFileIO.exportIPBansToJSON()
		#Update Whitelist
		self.updateConsole(END,"[Minecraft Server Crafter]: Pre-Server Startup Phase: Update Whitelist...")
		time.sleep(0.1)
		ServerFileIO.exportWhitelistfromDatabase()
		# All done!
		self.updateConsole(END,"[Minecraft Server Crafter]: Starting Server...")
		# Launch the server
		try:
			#Run the command
			process2 = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.PIPE,text=True)
			outputThread = threading.Thread(target=print_output,args=(process2,))
			outputThread.start()

		except Exception as e:
			# Handle exceptions
			self.displayException(e)
		
		
class ResourcePackWindow():
	def closeWindow(self): #original, I know xD
		self.root.grab_release()
		self.root.destroy()
		return
	
	def updateResourcePackValues(self):
		global ConsoleWindow
		global root_tabs

		root_tabs.set("Console Shell")
		#We need to update the values for the resource pack information
		MinecraftServerProperties.update({'resource-pack': str(self.resourcePackEntry.get())})
		MinecraftServerProperties.update({'resource-pack-sha1': str(self.resourcePackSHA1StringVar.get())})
		ConsoleWindow.updateConsole(END,"<Minecraft Server Crafter>: Resource Pack Values Updated Successfully.")
		self.closeWindow()
		return
	
	def ResourcePackCalling_VerifyupdateWindow(self,url=None):
		#We need to generate the sha1 and confirm if its valid
		self.Hashes = ServerFileIO.ResourcePackCall_generateSHA1(url=url)
		self.fileHash = self.Hashes[0]
		self.integrityCheck = self.Hashes[4]
		if self.integrityCheck == True:
			#Valid Hash
			self.resourcePackSHA1StringVar.set(self.fileHash)
			self.resourcePackVerifier.configure(text="\u2714\uFE0F",text_color="green")
			self.applybtn.configure(state=NORMAL)
			return
		if self.integrityCheck == False:
			#Invalid Hash
			self.resourcePackVerifier.configure(text="\u274C",text_color="red")
			return
		
	def getHash(self,url=None):
		#We need access of the generateSHA1 tuple in the ServerFileIO class
		self.hash = ServerFileIO.ResourcePackCall_generateSHA1(url=url)
		return self.hash
	def __init__(self,parent):
		self.parent = parent

		#Create widget
		
		self.root = CTkToplevel()
		self.root.title("Resource Pack Configuration")
		self.root.geometry("450x90")
		self.root.grid_columnconfigure((0,1,2,3,4,5,6,7,8),weight=1)
		self.root.grid_rowconfigure(0,weight=1)
		self.root.grab_set()
		self.folderHashes = {}
		self.resourcepackStringVar = StringVar(value=MinecraftServerProperties.get('resource-pack'))
		self.resourcePackLabel = CTkLabel(self.root,anchor=W,text="Resource Pack URL: ")
		self.resourcePackLabel.grid(row=0,column=0,sticky=W)
		self.resourcePack_tip = CTkToolTip(self.resourcePackLabel,"server.properties setting: 'resource-pack'")
		self.resourcePackEntry = CTkEntry(self.root,textvariable=self.resourcepackStringVar)
		self.resourcePackEntry.grid(row=0,column=1,columnspan=9,sticky=EW)
		self.resourcePackEntry_tip = CTkToolTip(self.resourcePackEntry,"Usage: You must put in a valid direct download link(Curseforge, Dropbox, Mediafire, etc),\notherwise the SHA-1 Hash for the Resource Pack won't generate, or be invalid.")
		self.resourcePackSHA1Label = CTkLabel(self.root,anchor=W,text="Resource Pack SHA-1: ")
		self.resourcePackSHA1Label.grid(row=1,column=0,sticky=W)
		self.resourcePackLabel_tip = CTkToolTip(self.resourcePackSHA1Label,"server.properties setting: 'resource-pack-sha1'")
		self.resourcePackSHA1StringVar = StringVar(value=MinecraftServerProperties.get('resource-pack-sha1'))
		self.resourcePackSHA1 = CTkLabel(self.root,anchor=W,text=" ",textvariable=self.resourcePackSHA1StringVar)
		self.resourcePackSHA1.grid(row=1,column=1,sticky=W)
		self.resourcePackVerifier = CTkLabel(self.root,anchor=W,text=" ",font=("Times New Roman Bold",24))
		self.resourcePackVerifier.grid(row=2,column=1,columnspan=2,sticky=E)
		self.verifybtn = CTkButton(self.root,text="Generate & Verify SHA-1",command=lambda:self.ResourcePackCalling_VerifyupdateWindow(url=self.resourcePackEntry.get()))
		self.verifybtn.grid(row=2,column=1,sticky=W)
		self.applybtn = CTkButton(self.root,text="Apply Settings & Close",state=DISABLED,command=lambda:self.updateResourcePackValues())
		self.applybtn.grid(row=2,column=0,sticky=W)
		return

class MOTDWindow():
	def updateProperties(self):
		self.CURRENTtext = self.MOTDTextbox.get("1.0",END)
		MinecraftServerProperties['motd'] = str(self.CURRENTtext)
		self.root.grab_release()
		self.root.destroy()
		return
	
	def characterLimit(self):
		self.CharCap = 59
		self.currentText = self.MOTDTextbox.get("1.0","end-1c")
		if len(self.currentText) >= self.CharCap:
			self.sliceVal = int(self.CharCap) - 1
			self.trimmedText = self.currentText[:int(self.sliceVal)]
			self.MOTDTextbox.delete("1.0",END)
			self.MOTDTextbox.insert(END,str(self.trimmedText))
			return

	def characterLimitevent(self,event):
		self.CharCap = 59
		self.currentText = self.MOTDTextbox.get("1.0","end-1c")
		if len(self.currentText) >= self.CharCap:
			self.sliceVal = int(self.CharCap) - 1
			self.trimmedText = self.currentText[:int(self.sliceVal)]
			self.MOTDTextbox.delete("1.0",END)
			self.MOTDTextbox.insert(END,str(self.trimmedText))
			return
	
	def updateCounter_event(self,event):
		self.textCurrent = self.MOTDTextbox.get("1.0","end-1c")
		self.charCounter.configure(text=f"{len(self.textCurrent)}/59 Characters Used")
		return
	
	def updateCounter(self):
		self.currentText = self.MOTDTextbox.get("1.0","end-1c")
		self.charCounter.configure(text=f"{len(self.currentText)}/59 Characters Used")
		return
	
	def newline(self):
		self.CurrentText = self.MOTDTextbox.get("1.0","end-1c")
		self.MOTDTextbox.delete("1.0",END)
		self.MOTDTextbox.insert(END,str(self.CurrentText) + "\\n")
		self.characterLimit()
		self.updateCounter()
		return
	
	def inserttextFormat(self, format):
		# Check for the format and insert the corresponding code
		if format == "Bold":
			self.MOTDTextbox.insert(END, "\\u00A7l")
			self.characterLimit()
			self.updateCounter()
		elif format == "Obfuscated":
			self.MOTDTextbox.insert(END, "\\u00A7k")
			self.characterLimit()
			self.updateCounter()
		elif format == "Strikethrough":
			self.MOTDTextbox.insert(END, "\\u00A7m")
			self.characterLimit()
			self.updateCounter()
		elif format == "Underline":
			self.MOTDTextbox.insert(END, "\\u00A7n")
			self.characterLimit()
			self.updateCounter()
		elif format == "Italics":
			self.MOTDTextbox.insert(END, "\\u00A7o")
			self.characterLimit()
			self.updateCounter()
		elif format == "Reset":
			self.MOTDTextbox.insert(END, "\\u00A7r")
			self.characterLimit()
			self.updateCounter()
		return
	
	def __init__(self,parent):
		self.parent = parent

		#Create Widget
		self.root = CTkToplevel()
		self.root.title("Message of the Day Configuration")
		self.root.geometry("545x110")
		self.root.grab_set()
		self.FormatingFrame = CTkFrame(self.root)
		self.FormatingFrame.grid(row=0,column=0,columnspan=6,rowspan=2)
		self.MOTDStringVar = StringVar(value=MinecraftServerProperties.get("motd"))
		self.MOTDTextbox = CTkTextbox(self.FormatingFrame,width=180,height=47,fg_color="#414141")
		self.MOTDTextbox.pack(fill=BOTH,expand=True,side=BOTTOM)
		self.MOTDTextbox.insert(END,self.MOTDStringVar.get())
		self.boldbtn = CTkButton(self.FormatingFrame,text="Bold",width=30,command=lambda:self.inserttextFormat("Bold"))
		self.boldbtn.pack(side=TOP,anchor=W,padx=1)
		self.obfuscatedbtn = CTkButton(self.FormatingFrame,text="Obfuscated",width=70,command=lambda:self.inserttextFormat("Obfuscated"))
		self.obfuscatedbtn.pack(before=self.boldbtn,side=RIGHT,padx=1)
		self.strikethroughbtn = CTkButton(self.FormatingFrame,text="Strikethrough",width=80,command=lambda:self.inserttextFormat("Strikethrough"))
		self.strikethroughbtn.pack(before=self.obfuscatedbtn,side=RIGHT,padx=1)
		self.underlinedbtn = CTkButton(self.FormatingFrame,text="Underlined",width=70,command=lambda:self.inserttextFormat("Underline"))
		self.underlinedbtn.pack(before=self.strikethroughbtn,side=RIGHT,padx=1)
		self.italicsbtn = CTkButton(self.FormatingFrame,text="Italics",width=70,command=lambda:self.inserttextFormat("Italics"))
		self.italicsbtn.pack(before=self.underlinedbtn,side=RIGHT,padx=1)
		self.resetFormattingbtn = CTkButton(self.FormatingFrame,width=90,text="Reset Formatting",command=lambda:self.inserttextFormat("Reset"))
		self.resetFormattingbtn.pack(before=self.italicsbtn,side=RIGHT,padx=1)
		self.newlinebtn = CTkButton(self.FormatingFrame,width=50,text="New Line",command=self.newline)
		self.newlinebtn.pack(before=self.resetFormattingbtn,side=RIGHT,padx=1)
		self.applybtn = CTkButton(self.root,text="Apply & Close",command=self.updateProperties)
		self.applybtn.grid(row=2,column=5,sticky=E,pady=4)
		self.initalCount = self.MOTDTextbox.get("1.0","end-1c")
		self.charCounter = CTkLabel(self.root,text=f"{len(self.initalCount)}/59 Characters Used")
		self.charCounter.grid(row=2,column=0,sticky=W)

		self.MOTDTextbox.bind("<Key>",self.characterLimitevent)
		self.MOTDTextbox.bind("<KeyRelease>",self.updateCounter_event)
		
		return

class PlayerListing():
	global process2
	def __init__(self,parent):
		self.parent = parent
		self.players = []

		#Create widget
		self.root = CTkFrame(self.root)
		self.root.grid(row=0,column=0)
		self.playerlistlabel = CTkLabel(self.root,text="Players List")
		self.playerlistlabel.grid(row=0,column=0)
		self.playerlist = CTkListbox(self.root)
		self.playerlist.grid(row=1,column=0)

		def callPlayerListing():
			process2.stdin.write(b'/list\n')
			process2.stdin.flush()
			serverResponse = process2.stdout.readline().decode().strip()
			listing = serverResponse.split(":")[1].strip().split(",")
			raw_list = list(listing)
			#Schedule for automation
			self.root.after(500,self.callPlayerListing)
			return raw_list

		if InternetHost.connectionCheck() == True and process2.is_alive() == True:
			#We need to fetch the player list
			listing = callPlayerListing()
			self.players = [listing]
			#Populate the listbox
			for item in self.players:
				self.playerlist.insert(END,str(item))
		return

#Console Shell Tab
ConsoleFrame = CTkFrame(root_tabs.tab("Console Shell"))
ConsoleWindow = ConsoleShell(ConsoleFrame)
ConsoleFrame.grid(row=0,column=0,sticky="nsew")

#Server Properties Tab
ServerPropertiesFrame = CTkFrame(root_tabs.tab("Server Properties File"))
ServerPropertiesFrame.pack(fill=BOTH,expand=True,anchor=W)
ServerPropertiesFrame_tabs = CTkTabview(ServerPropertiesFrame)
ServerPropertiesFrame_tabs.pack(fill=BOTH,expand=True,side=RIGHT)
ServerPropertiesFrame_tabs.add("World Settings")
ServerPropertiesFrame_tabs.add("Network & Security")
#Action Panel
ActionPanel = CTkFrame(ServerPropertiesFrame)
ActionPanel.pack(fill=Y,expand=True,side=LEFT)
#Server Type Image
ServerTypeImage = CTkLabel(ActionPanel, text="\n\n\n\nSettings Panel\n")
ServerTypeImage.grid(row=0,column=0,pady=10)
ImportPropertiesFileBtn = CTkButton(ActionPanel,text="Import Settings from File",command=ServerFileIO.importPropertiesfromFile)
ImportPropertiesFileBtn.grid(row=1,column=0)
ImportPropertiesFile_tip = CTkToolTip(ImportPropertiesFileBtn,"Imports server.properties Settings to JSON Model")
SavetoJSONFile = CTkButton(ActionPanel,text="Apply Settings to JSON",command=ServerFileIO.exportToJSONModel)
SavetoJSONFile.grid(row=2,column=0)
SavetoJSONFile_tip = CTkToolTip(SavetoJSONFile,"Saves the JSON Model to properties.json")
ConvertJSONData = CTkButton(ActionPanel,text="Convert Settings to File",command=lambda:ServerFileIO.convertJSONPropertiestoPropertiesFile(rootFilepath))
ConvertJSONData.grid(row=3,column=0)
ConvertJSONData_tip = CTkToolTip(ConvertJSONData,"Converts properties.json to server.properties, and saves it into the server directory")

#Minecraft Server Crafter Tab
MinecraftServerCrafterTabFrame = CTkFrame(root_tabs.tab("Minecraft Server Crafter Settings"))
MinecraftServerCrafterTabFrame.pack(fill=BOTH,expand=True,anchor=W)
attachJarBtn = CTkButton(MinecraftServerCrafterTabFrame,text="Attach Server Jar",command=ServerFileIO.attachServerJar)
attachJarBtn.grid(row=0,column=0)
launchServerBtn = CTkButton(MinecraftServerCrafterTabFrame,text="Launch Server",command=ConsoleWindow.beginServerProcess,state=DISABLED)
launchServerBtn.grid(row=1,column=0,pady=5)
saveConsoleLogbtn = CTkButton(MinecraftServerCrafterTabFrame,text="Export Console Shell",command=lambda:ConsoleWindow.SaveConsoleToFile(1.0,END))
saveConsoleLogbtn.grid(row=2,column=0,sticky=N)
memoryAllocatedBool = BooleanVar(value=False)
MemoryAllocation = CTkCheckBox(MinecraftServerCrafterTabFrame,text="Allocate Server Memory",variable=memoryAllocatedBool,onvalue=True,offvalue=False)
MemoryAllocation.grid(row=0,column=1)
#Memory Allocation Constraints
MemoryAllocationFrame = CTkFrame(MinecraftServerCrafterTabFrame)
MemoryAllocationFrame.grid(row=1,column=1,rowspan=4)
def showValMinimum(value):
	MemoryAllocationMiniumValueToolTip.configure(message=int(value))
#We need to set the intvar
MinimumMemoryInt = IntVar(value=currentMemoryMinimum)
MemoryAllocationMiniumLabel = CTkLabel(MemoryAllocationFrame,text="Minimum Memory Allocated")
MemoryAllocationMiniumLabel.grid(row=0,column=0,pady=4)
MemoryAllocationMiniumSlider = CTkSlider(MemoryAllocationFrame,state=DISABLED,from_= int(MiniumMemory),to= int(MemoryAllocationCap),command=showValMinimum)
MemoryAllocationMiniumSlider.grid(row=1,column=0)
MemoryAllocationMiniumSlider.set(MinimumMemoryInt.get())
#We need to show the value of the Slider
MemoryAllocationMiniumValueToolTip = CTkToolTip(MemoryAllocationMiniumSlider,message=str(MinimumMemoryInt.get()))
def showValMax(value):
	MemoryAllocationMaximumTooltip.configure(message=int(value))
#Set the intvar
MaximumMemoryInt = IntVar(value=currentMemoryMax)
MemoryAllocationMaximumLabel = CTkLabel(MemoryAllocationFrame,text="Maximum Memory Allocation")
MemoryAllocationMaximumLabel.grid(row=2,column=0,pady=4)
MemoryAllocationMaximumSlider = CTkSlider(MemoryAllocationFrame,state=DISABLED,from_= int(MemoryAllocationMiniumSlider.get()),to= int(MemoryAllocationCap),command=showValMax)
MemoryAllocationMaximumSlider.grid(row=3,column=0,pady=4)
MemoryAllocationMaximumSlider.set(MaximumMemoryInt.get())
#We need to show the value of the slider
MemoryAllocationMaximumTooltip = CTkToolTip(MemoryAllocationMaximumSlider,message=str(MaximumMemoryInt.get()))
#We need to toggle widgets when the checkbox is ticked or not
def updateWidgets():
	CheckboxIsTicked = memoryAllocatedBool.get()
	if CheckboxIsTicked == False:
		#Memory isnt getting allocated
		#Disable the sliders
		MemoryAllocationMiniumSlider.configure(state=DISABLED)
		MemoryAllocationMaximumSlider.configure(state=DISABLED)
		#Set the launch server button command
		launchServerBtn.configure(command=ConsoleWindow.beginServerProcess)
		return
	if CheckboxIsTicked == True:
		#Memory is getting allocated
		#Enable the sliders
		MemoryAllocationMiniumSlider.configure(state=NORMAL)
		MemoryAllocationMaximumSlider.configure(state=NORMAL)
		#Set the launch server button command
		launchServerBtn.configure(command=lambda:ConsoleWindow.beginServerProcess(memoryAllocation=True,initialMemory=int(MinimumMemoryInt.get()),maxMemory=int(MaximumMemoryInt.get())))
		return
MemoryAllocation.configure(command=updateWidgets)
#Players List
OnlinePlayerList = PlayerListing(MinecraftServerCrafterTabFrame)
OnlinePlayerList.grid(row=0,column=1,rowspan=4)

#World Settings Tab
WorldSettingsFrame = CTkScrollableFrame(ServerPropertiesFrame_tabs.tab("World Settings"))
WorldSettingsFrame.pack(fill=BOTH,expand=True,anchor=W)
WorldNameLabel = CTkLabel(WorldSettingsFrame,text="World Name: ")
WorldNameLabel.grid(row=0,column=0,sticky=E)
WorldNameStringVar = StringVar(value=MinecraftServerProperties.get("level-name"))
WorldNameEntry = CTkEntry(WorldSettingsFrame,textvariable=WorldNameStringVar)
WorldNameEntry.grid(row=0,column=1,sticky=W)
WorldNameEntry_tip = CTkToolTip(WorldNameLabel,"server.properties setting: 'level-name'")
levelSeedLabel = CTkLabel(WorldSettingsFrame,text="World Seed: ")
levelSeedLabel.grid(row=1,column=0,sticky=E)
levelSeedStringVar = StringVar(value=MinecraftServerProperties.get("level-seed"))
levelSeedEntry = CTkEntry(WorldSettingsFrame,textvariable=levelSeedStringVar)
levelSeedEntry.grid(row=1,column=1,sticky=W)
levelSeedEntry_tip = CTkToolTip(levelSeedLabel,"server.properties setting: 'level-seed'")
gamemodeList = ["survival","creative","adventure","spectator"]
gamemodeStringVar = StringVar(value=MinecraftServerProperties.get("gamemode"))
gamemodeListLabel = CTkLabel(WorldSettingsFrame,text="Gamemode: ")
gamemodeListLabel.grid(row=2,column=0,sticky=E)
gamemodeListComboBox = CTkComboBox(WorldSettingsFrame,values=gamemodeList,variable=gamemodeStringVar)
gamemodeListComboBox.grid(row=2,column=1,sticky=W)
gamemodeList_tip = CTkToolTip(gamemodeListLabel,"server.properties setting: 'gamemode'")
spawnprotectionRadiusInt = IntVar(value=MinecraftServerProperties.get('spawn-protection'))
spawnprotectionradiusLabel = CTkLabel(WorldSettingsFrame,text="Spawn Protection Radius: ")
spawnprotectionradiusLabel.grid(row=3,column=0,sticky=E)
spawnprotectionradiusEntry = CTkEntry(WorldSettingsFrame,textvariable=spawnprotectionRadiusInt)
spawnprotectionradiusEntry.grid(row=3,column=1,sticky=W)
spawnprotection_tip = CTkToolTip(spawnprotectionradiusLabel,"server.properties setting: 'spawn-protection'")
worldsizeInt = IntVar(value=MinecraftServerProperties.get('max-world-size'))
worldsizeLabel = CTkLabel(WorldSettingsFrame,text="World Size: ")
worldsizeLabel.grid(row=4,column=0,sticky=E)
worldsizeEntry = CTkEntry(WorldSettingsFrame,textvariable=worldsizeInt)
worldsizeEntry.grid(row=4,column=1,sticky=W)
worldsize_tip = CTkToolTip(worldsizeLabel,"server.properties settings: 'max-world-size'")
worldtypeLabel = CTkLabel(WorldSettingsFrame,text="World Type: ")
worldtypeLabel.grid(row=5,column=0,sticky=E)
worldtypeOptions = ["default","minecraft\:normal","minecraft\:flat","minecraft\:large_biomes","minecraft\:amplified","minecraft\:single_biome_surface"]
worldtypeStringVar = StringVar(value=MinecraftServerProperties.get("level-type"))
worldtypeComboBox = CTkComboBox(WorldSettingsFrame,values=worldtypeOptions,variable=worldtypeStringVar)
worldtypeComboBox.grid(row=5,column=1,sticky=W)
worldtype_tip = CTkToolTip(worldtypeLabel,"server.properties setting: 'level-type'")
worldDifficultyVar = StringVar(value=MinecraftServerProperties.get('difficulty'))
worldDifficultyList = ['peaceful','easy','normal','hard']
worldDifficultyComboBox = CTkComboBox(WorldSettingsFrame,values=worldDifficultyList,variable=worldDifficultyVar)
worldDifficultyComboBox.grid(row=6,column=1,sticky=W)
worldDifficultyLabel = CTkLabel(WorldSettingsFrame,text="Server Difficulty: ")
worldDifficultyLabel.grid(row=6,column=0,sticky=E)
worldDifficulty_tip = CTkToolTip(worldDifficultyLabel,"server.properties setting: 'difficulty'")
playercountIntVar = IntVar(value=MinecraftServerProperties.get('max-players'))
playercountLabel = CTkLabel(WorldSettingsFrame,text="Player Count: ")
playercountLabel.grid(row=7,column=0,sticky=E)
playercountEntry = CTkEntry(WorldSettingsFrame,textvariable=playercountIntVar)
playercountEntry.grid(row=7,column=1,sticky=W)
playercount_tip = CTkToolTip(playercountLabel,"server.properties setting: 'max-players'")
resourcePackPromptLabel = CTkLabel(WorldSettingsFrame,text="Resource Pack Prompt: ")
resourcePackPromptLabel.grid(row=8,column=0,sticky=E)
resourcePackPromptStringVar = StringVar(value=MinecraftServerProperties.get('resource-pack-prompt'))
resourcePackPromptEntry = CTkEntry(WorldSettingsFrame,textvariable=resourcePackPromptStringVar)
resourcePackPromptEntry.grid(row=8,column=1,sticky=W)
resourcePackPromptLabel_tip = CTkToolTip(resourcePackPromptLabel,"server.properties setting: 'resource-pack-prompt'")
generatorsettingsvar = StringVar(value=MinecraftServerProperties.get('generator-settings'))
generatorSettingsLabel = CTkLabel(WorldSettingsFrame,text="Generator Settings: ")
generatorSettingsLabel.grid(row=9,column=0,sticky=E)
generatorSettingsEntry = CTkEntry(WorldSettingsFrame,textvariable=generatorsettingsvar)
generatorSettingsEntry.grid(row=9,column=1,sticky=W)
generatorsettings_tip = CTkToolTip(generatorSettingsLabel,"server.properties setting: 'generator-settings'")
viewDistanceIntVar = IntVar(value=MinecraftServerProperties.get('view-distance'))
viewDistanceLabel = CTkLabel(WorldSettingsFrame,text="View Distance: ")
viewDistanceLabel.grid(row=10,column=0,sticky=E)
viewDistanceEntry = CTkEntry(WorldSettingsFrame,textvariable=viewDistanceIntVar)
viewDistanceEntry.grid(row=10,column=1,sticky=W)
viewDistance_tip = CTkToolTip(viewDistanceLabel,"server.properties settings: 'view-distance'")
simulationDistanceIntVar = IntVar(value=MinecraftServerProperties.get('simulation-distance'))
simulationDistanceLabel = CTkLabel(WorldSettingsFrame,text="Simulation Distance: ")
simulationDistanceLabel.grid(row=11,column=0,sticky=E)
simulationDistanceEntry = CTkEntry(WorldSettingsFrame,textvariable=simulationDistanceIntVar)
simulationDistanceEntry.grid(row=11,column=1,sticky=W)
simulationDistance_tip = CTkToolTip(simulationDistanceLabel,"server.properties setting: 'simulation-distance'")
neighborupdatesIntVar = IntVar(value=MinecraftServerProperties.get('max-chained-neighbor-updates'))
neighborupdatesLabel = CTkLabel(WorldSettingsFrame,text="Max Chained Updates: ")
neighborupdatesLabel.grid(row=12,column=0,sticky=E)
neighborupdatesEntry = CTkEntry(WorldSettingsFrame,textvariable=neighborupdatesIntVar)
neighborupdatesEntry.grid(row=12,column=1,sticky=W)
neighborupdates_tip = CTkToolTip(neighborupdatesLabel,"server.properties setting: 'max-chained-neighbor-updates'")
disableddataPackStringVar = StringVar(value=MinecraftServerProperties.get('initial-disabled-packs'))
disableddataPackLabel = CTkLabel(WorldSettingsFrame,text="Disabled Datapacks: ")
disableddataPackLabel.grid(row=13,column=0,sticky=E)
disableddataPackEntry = CTkEntry(WorldSettingsFrame,textvariable=disableddataPackStringVar)
disableddataPackEntry.grid(row=13,column=1,sticky=W)
enableddatapacksStringVar = StringVar(value=MinecraftServerProperties.get('initial-enabled-packs'))
enableddatapacksLabel = CTkLabel(WorldSettingsFrame,text="Enabled Datapacks: ")
enableddatapacksLabel.grid(row=14,column=0,sticky=E)
enableddatapacksEntry = CTkEntry(WorldSettingsFrame,textvariable=enableddatapacksStringVar)
enableddatapacksEntry.grid(row=14,column=1,sticky=W)
resourcePackConfigurationBtn = CTkButton(WorldSettingsFrame,text="Configure Resource Pack",command=MCSC_Framework.onMainWindow_openResourcePackConfig)
resourcePackConfigurationBtn.grid(row=15,column=0,sticky=W,pady=3)
MOTDConfigBtn = CTkButton(WorldSettingsFrame,text="Configure MOTD",command=MCSC_Framework.onMainWindow_openMOTDConfig)
MOTDConfigBtn.grid(row=15,column=1,sticky=W,pady=3)

#World Settings booleans
WorldSettingsBools = CTkFrame(WorldSettingsFrame)
WorldSettingsBools.grid(row=16,column=0,columnspan=2)
usecmdBlocksBoolVar = BooleanVar(value=MinecraftServerProperties.get("enable-command-block"))
commandBlockUsage = CTkCheckBox(WorldSettingsBools,onvalue=True,offvalue=False,text="Allow Command Blocks",variable=usecmdBlocksBoolVar)
commandBlockUsage.grid(row=0,column=0,sticky=W,padx=3)
cmdBlock_tip = CTkToolTip(commandBlockUsage,"server.properties setting: 'enable-command-block'")
isPVPBool = BooleanVar(value=MinecraftServerProperties.get('pvp'))
isPVP = CTkCheckBox(WorldSettingsBools,text="Allow PVP",variable=isPVPBool,onvalue=True,offvalue=False)
isPVP.grid(row=0,column=1,padx=3)
pvp_tip = CTkToolTip(isPVP,"server.properties setting: 'pvp'")
strictGamemodeBool = BooleanVar(value=MinecraftServerProperties.get('force-gamemode'))
strictGamemode = CTkCheckBox(WorldSettingsBools,text="Enforce Gamemode",variable=strictGamemodeBool,onvalue=True,offvalue=False)
strictGamemode.grid(row=1,column=0,padx=3,pady=3,sticky=W)
strictGamemode_tip = CTkToolTip(strictGamemode,"server.properties setting: 'force-gamemode'")
resourcePackRequirementBool = BooleanVar(value=MinecraftServerProperties.get('require-resource-pack'))
resourcePackRequirement = CTkCheckBox(WorldSettingsBools,text="Requires Resource Pack",variable=resourcePackRequirementBool,onvalue=True,offvalue=False)
resourcePackRequirement.grid(row=2,column=0,padx=3,sticky=NW)
resourcePackRequirement_tip = CTkToolTip(resourcePackRequirement,"server.properties setting: 'require-resource-pack'")
netherDimension = BooleanVar(value=MinecraftServerProperties.get('allow-nether'))
netherTravel = CTkCheckBox(WorldSettingsBools,text="Allow Nether",variable=netherDimension,onvalue=True,offvalue=False)
netherTravel.grid(row=1,column=1)
canFly = BooleanVar(value=MinecraftServerProperties.get('allow-flight'))
hasFlight = CTkCheckBox(WorldSettingsBools,text="Allow Flying",variable=canFly,onvalue=True,offvalue=False)
hasFlight.grid(row=2,column=1,padx=3,pady=3)
flying_tip = CTkToolTip(hasFlight, "server.properties setting: 'allow-flight'")
netherTravel_tip = CTkToolTip(netherTravel,"server.properties setting:'allow-nether'")
isHardcoreWorldBool = BooleanVar(value=MinecraftServerProperties.get("hardcore"))
isHardcore = CTkCheckBox(WorldSettingsBools,text="Hardcore World",variable=isHardcoreWorldBool,onvalue=True,offvalue=False)
isHardcore.grid(row=3,column=0,sticky=NW,padx=3)
hardcore_tip = CTkToolTip(isHardcore,"server.properties setting:'hardcore'")
onlinePlayersHiddenBool = BooleanVar(value=MinecraftServerProperties.get('hide-online-players'))
showOnlinePlayers = CTkCheckBox(WorldSettingsBools,text="Hide Online Players",variable=onlinePlayersHiddenBool,onvalue=True,offvalue=False)
showOnlinePlayers.grid(row=3,column=1,padx=3,sticky=W)
visibeOnlinePlayers = CTkToolTip(showOnlinePlayers,"server.properties setting: 'hide-online-players'")
statusBool = BooleanVar(value=MinecraftServerProperties.get('enable-status'))
toggleStatus = CTkCheckBox(WorldSettingsBools,text="Toggle Status",variable=statusBool,onvalue=True,offvalue=False)
toggleStatus.grid(row=4,column=0,padx=3,pady=3,sticky=W)
strictProfileBool = BooleanVar(value=MinecraftServerProperties.get('enforce-secure-profile'))
strictProfile = CTkCheckBox(WorldSettingsBools,text="Stricted Profiling",variable=strictProfileBool,onvalue=True,offvalue=False)
strictProfile.grid(row=5,column=0,sticky=W,padx=3)
strictProfile_tip = CTkToolTip(strictProfile,"server.properties setting: 'enforce-secure-profile'")
nativeTransport = BooleanVar(value=MinecraftServerProperties.get('use-native-transport'))
useNativeTransport = CTkCheckBox(WorldSettingsBools,text="Native Transport",variable=nativeTransport,onvalue=True,offvalue=False)
useNativeTransport.grid(row=6,column=0,sticky=W,padx=3,pady=3)
nativeTransport_tip = CTkToolTip(useNativeTransport,"server.properties setting: 'use-native-transport'")
structureGeneration = BooleanVar(value=MinecraftServerProperties.get('generate-structures'))
structureWillGenerate = CTkCheckBox(WorldSettingsBools,text="Structure Generation",variable=structureGeneration,onvalue=True,offvalue=False)
structureWillGenerate.grid(row=4,column=1,sticky=W,padx=3)
structure_tip = CTkToolTip(structureWillGenerate,"server.properties setting:'generate-structures'")
npcSpawning = BooleanVar(value=MinecraftServerProperties.get('spawn-npcs'))
NPCspawning = CTkCheckBox(WorldSettingsBools,text="Spawn NPCs",variable=npcSpawning,onvalue=True,offvalue=False)
NPCspawning.grid(row=5,column=1,sticky=W,padx=3)
npcSpawning_tip = CTkToolTip(NPCspawning,"server.properties setting: 'spawn-npcs'")
animalSpawning = BooleanVar(value=MinecraftServerProperties.get('spawn-animals'))
Animalspawning = CTkCheckBox(WorldSettingsBools,text="Spawn Animals",variable=animalSpawning,onvalue=True,offvalue=False)
Animalspawning.grid(row=6,column=1,sticky=W,padx=3)
animalspawning_tip = CTkToolTip(Animalspawning,"server.properties setting: 'spawn-animals'")
enemySpawning = BooleanVar(value=MinecraftServerProperties.get('spawn-monsters'))
Enemyspawning = CTkCheckBox(WorldSettingsBools,text="Spawn Enemies",variable=enemySpawning,onvalue=True,offvalue=False)
Enemyspawning.grid(row=7,column=1,sticky=W,padx=3)
enemyspawning_tip = CTkToolTip(Enemyspawning,"server.properties setting: 'spawn-monsters'")
broadcastConsoleBool = BooleanVar(value=MinecraftServerProperties.get('broadcast-console-to-ops'))
broadcastConsole = CTkCheckBox(WorldSettingsBools,text="Broadcast System Console",variable=broadcastConsoleBool,onvalue=True,offvalue=False)
broadcastConsole.grid(row=7,column=0,sticky=W,padx=3)
broadcastconsole_tip = CTkToolTip(broadcastConsole,"server.properties setting: 'broadcast-console-to-ops'")
#Network & Security Tab
NetworkSecurityTab = CTkScrollableFrame(ServerPropertiesFrame_tabs.tab("Network & Security"))
NetworkSecurityTab.pack(fill=BOTH,expand=True,anchor=W)
MinecraftServerIPStringVar = StringVar(value=MinecraftServerProperties.get('server-ip'))
IPAddressLabel = CTkLabel(NetworkSecurityTab,text="Server IP: ")
IPAddressLabel.grid(row=0,column=0,sticky=E)
IPAddressEntry = CTkEntry(NetworkSecurityTab,textvariable=MinecraftServerIPStringVar)
IPAddressEntry.grid(row=0,column=1,sticky=W)
IPAddress_tip = CTkToolTip(IPAddressLabel,"server.properties setting: 'server-ip'")
NetworkCompressionIntVar = IntVar(value=MinecraftServerProperties.get('network-compression-threshold'))
networkcompressionLabel = CTkLabel(NetworkSecurityTab,text="Network Compression: ")
networkcompressionLabel.grid(row=1,column=0,sticky=E)
networkCompressionEntry = CTkEntry(NetworkSecurityTab,textvariable=NetworkCompressionIntVar)
networkCompressionEntry.grid(row=1,column=1,sticky=W)
networkCompression_tip = CTkToolTip(networkcompressionLabel,"server.properties setting: 'network-compression-threshold'")
ticktimeIntVar = IntVar(value=MinecraftServerProperties.get('max-tick-time'))
ticktimeLabel = CTkLabel(NetworkSecurityTab,text="Max Tick Rate: ")
ticktimeLabel.grid(row=2,column=0,sticky=E)
ticktimeEntry = CTkEntry(NetworkSecurityTab,textvariable=ticktimeIntVar)
ticktimeEntry.grid(row=2,column=1,sticky=W)
ticktime_tip = CTkToolTip(ticktimeLabel,"server.properties setting: 'max-tick-time'")
maxplayersIntVar = IntVar(value=MinecraftServerProperties.get('max-players'))
maxplayersLabel = CTkLabel(NetworkSecurityTab,text="Max Players: ")
maxplayersLabel.grid(row=3,column=0,sticky=E)
maxplayersEntry = CTkEntry(NetworkSecurityTab,textvariable=maxplayersIntVar)
maxplayersEntry.grid(row=3,column=1,sticky=W)
maxplayers_tip = CTkToolTip(maxplayersLabel,"server.properties setting: 'max-players'")
serverportIntVar = IntVar(value=MinecraftServerProperties.get('server-port'))
serverportLabel = CTkLabel(NetworkSecurityTab,text="Server Port: ")
serverportLabel.grid(row=4,column=0,sticky=E)
serverportEntry = CTkEntry(NetworkSecurityTab,textvariable=serverportIntVar)
serverportEntry.grid(row=4,column=1,sticky=W)
serverport_tip = CTkToolTip(serverportLabel,"server.properties setting: 'server-port'")
opPermissionlvlList = ["0","1","2","3","4"]
opPermissionlvlIntVar = IntVar(value=MinecraftServerProperties.get('op-permission-level'))
opPermissionlvlLabel = CTkLabel(NetworkSecurityTab,text="Op Permission Level: ")
opPermissionlvlLabel.grid(row=5,column=0,sticky=E)
opPermissionlvlComboBox = CTkComboBox(NetworkSecurityTab,values=opPermissionlvlList,variable=opPermissionlvlIntVar)
opPermissionlvlComboBox.grid(row=5,column=1,sticky=W)
opPermissionlvl_tip = CTkToolTip(opPermissionlvlLabel,"server.properties setting: 'op-permission-level'")
entitybroadcastRangeList = [str(i) for i in range(10,1000)] #Best way of generating numbers from its set range
entitybroadcastRangeIntVar = IntVar(value=MinecraftServerProperties.get('entity-broadcast-range-percentage'))
entitybroadcastRangeLabel = CTkLabel(NetworkSecurityTab,text="Entity Broadcasting: ")
entitybroadcastRangeLabel.grid(row=6,column=0,sticky=E)
entitybroadcastRangeCombobox = CTkComboBox(NetworkSecurityTab,values=entitybroadcastRangeList,variable=entitybroadcastRangeIntVar)
entitybroadcastRangeCombobox.grid(row=6,column=1,sticky=W)
entitybroadcastRange_tip = CTkToolTip(entitybroadcastRangeLabel,"server.properties setting: 'entity-broadcast-range-percentage")
playertimeoutIntVar = IntVar(value=MinecraftServerProperties.get('player-idle-timeout'))
playertimeoutLabel = CTkLabel(NetworkSecurityTab,text="Idle Player Timeout: ")
playertimeoutLabel.grid(row=7,column=0,sticky=E)
playertimeoutEntry = CTkEntry(NetworkSecurityTab,textvariable=playercountIntVar)
playertimeoutEntry.grid(row=7,column=1,sticky=W)
playertimeout_tip = CTkToolTip(playertimeoutLabel,"server.properties setting: 'player-idle-timeout'")
ratelimitIntvar = IntVar(value=MinecraftServerProperties.get('rate-limit'))
ratelimitLabel = CTkLabel(NetworkSecurityTab,text="Rate Limit: ")
ratelimitLabel.grid(row=8,column=0,sticky=E)
ratelimitEntry = CTkEntry(NetworkSecurityTab,textvariable=ratelimitIntvar)
ratelimitEntry.grid(row=8,column=1,sticky=W)
ratelimit_tip = CTkToolTip(ratelimitLabel,"server.properties setting: 'rate-limit'")
functionPermissionlvlList = [str(x) for x in range(1,4)]
functionPermissionlvlIntvar = IntVar(value=MinecraftServerProperties.get('function-permission-level'))
functionPermissionlvlLabel = CTkLabel(NetworkSecurityTab,text="Fuction Permission Level: ")
functionPermissionlvlLabel.grid(row=9,column=0,sticky=E)
functionPermissionlvlComboBox = CTkComboBox(NetworkSecurityTab,values=functionPermissionlvlList,variable=functionPermissionlvlIntvar)
functionPermissionlvlComboBox.grid(row=9,column=1,sticky=W)
functionPermissionlvl_tip = CTkToolTip(functionPermissionlvlLabel,"server.properties setting: 'function-permission-level'")
rconPasswordStringVar = StringVar(value=MinecraftServerProperties.get('rcon.password'))
rconPasswordLabel = CTkLabel(NetworkSecurityTab,text="RCON Password: ")
rconPasswordLabel.grid(row=10,column=0,sticky=E)
rconPasswordEntry = CTkEntry(NetworkSecurityTab,textvariable=rconPasswordStringVar)
rconPasswordEntry.grid(row=10,column=1,sticky=W)
rconPassword_tip = CTkToolTip(rconPasswordLabel,"server.properties setting: 'rcon.password'")
rconportIntVar = IntVar(value=MinecraftServerProperties.get('rcon.port'))
rconportLabel = CTkLabel(NetworkSecurityTab,text="RCON Port: ")
rconportLabel.grid(row=11,column=0,sticky=E)
rconportEntry = CTkEntry(NetworkSecurityTab,textvariable=rconportIntVar)
rconportEntry.grid(row=11,column=1,sticky=W)
rconport_tip = CTkToolTip(rconportLabel,"server.properties setting: 'rcon.port'")
queryportIntVar = IntVar(value=MinecraftServerProperties.get('query.port'))
queryportLabel = CTkLabel(NetworkSecurityTab,text="Query Port: ")
queryportLabel.grid(row=12,column=0,sticky=E)
queryportEntry = CTkEntry(NetworkSecurityTab,textvariable=queryportIntVar)
queryportEntry.grid(row=12,column=1,sticky=W)
queryport_tip = CTkToolTip(queryportLabel,"server.properties setting: 'query.port'")
#Networking Tab Bools
NetworkSecurityTabBools = CTkFrame(NetworkSecurityTab)
NetworkSecurityTabBools.grid(row=13,column=0,columnspan=2,sticky=E)
togglequery = BooleanVar(value=MinecraftServerProperties.get('enable-query'))
canQueryCheck = CTkCheckBox(NetworkSecurityTabBools,text="Enable Query",variable=togglequery,onvalue=True,offvalue=False)
canQueryCheck.grid(row=0,column=1,padx=3,pady=3,sticky=W)
canquery_tip = CTkToolTip(canQueryCheck,"server.properties setting: 'enable-query'")
chunkwriteSyncingBool = BooleanVar(value=MinecraftServerProperties.get('sync-chunk-writes'))
chunkwriteSyncingCheck = CTkCheckBox(NetworkSecurityTabBools,text="Synchronized Chunk Writing",variable=chunkwriteSyncingBool,onvalue=True,offvalue=False)
chunkwriteSyncingCheck.grid(row=1,column=0,padx=3,pady=3,sticky=W)
chunkwriteSyncing_tip = CTkToolTip(chunkwriteSyncingCheck,"server.properties setting: 'sync-chunk-writes'")
proxyBlockingBool = BooleanVar(value=MinecraftServerProperties.get('prevent-proxy-connections'))
proxyBlockingCheck = CTkCheckBox(NetworkSecurityTabBools,text="Block Proxy Connections",variable=proxyBlockingBool,onvalue=True,offvalue=False)
proxyBlockingCheck.grid(row=0,column=0,padx=3,pady=3,sticky=W)
proxyblocking_tip = CTkToolTip(proxyBlockingCheck,"server.properties setting: 'prevent-proxy-connections'")
toggleOnlineMode = BooleanVar(value=MinecraftServerProperties.get('online-mode'))
isOnline = CTkCheckBox(NetworkSecurityTabBools,text="Online Mode",variable=toggleOnlineMode,onvalue=True,offvalue=False)
isOnline.grid(row=1,column=1,sticky=W,padx=3,pady=3)
isonline_tip = CTkToolTip(isOnline,"server.properties setting: 'online-mode'")
jmxMonitoringBool = BooleanVar(value=MinecraftServerProperties.get('enable-jmx-monitoring'))
jmxMonitoringCheck = CTkCheckBox(NetworkSecurityTabBools,text="Toggle JMX Monitoring",variable=jmxMonitoringBool,onvalue=True,offvalue=False)
jmxMonitoringCheck.grid(row=2,column=0,sticky=W,pady=3,padx=3)
jmxMonitoring_tip = CTkToolTip(jmxMonitoringCheck,"server.properties setting: 'enable-jmx-monitoring'")
isIPLogging = BooleanVar(value=MinecraftServerProperties.get('log-ips'))
IPLogBool = CTkCheckBox(NetworkSecurityTabBools,text="Log IPs",onvalue=True,offvalue=False,variable=isIPLogging)
IPLogBool.grid(row=2,column=1,padx=3,pady=3,sticky=W)
togglerconBool = BooleanVar(value=MinecraftServerProperties.get('enable-rcon'))
rconToggler = CTkCheckBox(NetworkSecurityTabBools,text="Enable RCON",variable=togglerconBool,onvalue=True,offvalue=False)
rconToggler.grid(row=3,column=1,padx=3,pady=3,sticky=W)
broadcastrconBool = BooleanVar(value=MinecraftServerProperties.get('broadcast-rcon-to-ops'))
rconBroadcast = CTkCheckBox(NetworkSecurityTabBools,text="Broadcast RCON",variable=broadcastrconBool,onvalue=True,offvalue=False)
rconBroadcast.grid(row=3,column=0,sticky=W,padx=3,pady=3)

#Whitelist Tab

whitelistTab = CTkFrame(root_tabs.tab("Whitelisting"))
whitelistTab.grid(row=0,column=0,sticky=N,padx=20)
whitelistedBool = BooleanVar(value=MinecraftServerProperties.get('white-list'))
isWhitelisted = CTkCheckBox(whitelistTab,text="Enable Whitelisting",variable=whitelistedBool,onvalue=True,offvalue=False)
isWhitelisted.grid(row=0,column=0,sticky=W,padx=3)
strictedWhitelistBool = BooleanVar(value=MinecraftServerProperties.get('enforce-whitelist'))
strictedWhitelistCheck = CTkCheckBox(whitelistTab,text="Enforced Whitelisting",variable=strictedWhitelistBool,onvalue=True,offvalue=False)
strictedWhitelistCheck.grid(row=0,column=1,sticky=W,padx=3,pady=3)
WhitelistFrame = CTkFrame(root_tabs.tab("Whitelisting"))
WhitelistFrame.grid(row=0,column=2,rowspan=7,padx=30)
WhitelistListbox = CTkListbox(WhitelistFrame)
WhitelistListbox.pack(fill=BOTH,expand=True,side=BOTTOM)
addPlayerbtn = CTkButton(root_tabs.tab("Whitelisting"),text="Add Player",command=ServerFileIO.askAddWhitelistPlayer)
addPlayerbtn.grid(row=1,column=0,sticky=E)
removePlayerbtn = CTkButton(root_tabs.tab("Whitelisting"),text="Remove Player",command=ServerFileIO.removeFromWhitelist)
removePlayerbtn.grid(row=2,column=0,sticky=E)

#Banning tab

BansTab = CTkScrollableFrame(root_tabs.tab("Banned Players"))
BansTab.pack(fill=BOTH,expand=True,anchor=W)
BannedPlayerNamesFrame = CTkFrame(BansTab)
BannedPlayerNamesFrame.grid(row=0,column=0,rowspan=5,sticky=W)
BannedPlayerNamesListbox = CTkListbox(BannedPlayerNamesFrame)
BannedPlayerNamesListbox.pack(fill=Y,expand=True,side=BOTTOM)
BannedPlayerNamesLabel = CTkLabel(BannedPlayerNamesFrame,text="Banned Players")
BannedPlayerNamesLabel.pack(side=TOP)
BannedIPsFrame = CTkFrame(BansTab)
BannedIPsFrame.grid(row=0,column=2,rowspan=5,sticky=W)
BannedIPsListbox = CTkListbox(BannedIPsFrame)
BannedIPsListbox.pack(fill=Y,expand=True,side=BOTTOM)
BannedIPsLabel = CTkLabel(BannedIPsFrame,text="Banned IPs")
BannedIPsLabel.pack(side=TOP)
BannedTab_ActionPanel = CTkFrame(BansTab)
BannedTab_ActionPanel.grid(row=0,column=1,rowspan=5,sticky=W)
BannedByPlayerNamebtn = CTkButton(BannedTab_ActionPanel,text="Ban by Name",command=ServerFileIO.askBanPlayerName)
BannedByPlayerNamebtn.grid(row=0,column=0)
BanByIPbtn = CTkButton(BannedTab_ActionPanel,text="Ban by IP Address",command=ServerFileIO.askIPBan)
BanByIPbtn.grid(row=1,column=0,sticky=W)
pardonPlayerNamebtn = CTkButton(BannedTab_ActionPanel,text="Pardon by Name",command=ServerFileIO.PardonName)
pardonPlayerNamebtn.grid(row=2,column=0,sticky=W)
pardonIPbtn = CTkButton(BannedTab_ActionPanel,text="Pardon by IP Address",command=ServerFileIO.PardonIP)
pardonIPbtn.grid(row=3,column=0,sticky=W)


shellVersion = "Version: " + str(VersionNumber) + "\n"

MCSC_Framework.onMainWindow_setTabState(root_tabs,"Server Properties File","disabled")
MCSC_Framework.onMainWindow_setTabState(root_tabs,"Whitelisting","disabled")
MCSC_Framework.onMainWindow_setTabState(root_tabs,"Banned Players","disabled")

ConsoleWindow.updateConsole(END,"Minecraft Server Crafter Lite - Release Build \n" + str(shellVersion))
ConsoleWindow.updateConsole(END,"To begin, go to Minecraft Server Crafter Settings > Attach Server Jar \n")

root.mainloop()
