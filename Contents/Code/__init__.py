#!/usr/local/bin/python
# coding: utf-8

from PMS import *
from PMS.Objects import *
from PMS.Plugin import *
from PMS.Shortcuts import *
from lxml import etree
import urllib,urllib2

APPLICATIONS_INDIGO_PREFIX 	= "/applications/indigo"
INDIGO_AUTHENTICATION_REALM	= u"Indigo Control Server"
VIDEO_INDIGO_PREFIX		= "/video/indigo"
ART 				= 'art-default.png'
ICON				= 'icon-default.png'
LIGHT_ON_ICON			= 'powerbutton_on.png'
LIGHT_OFF_ICON			= 'powerbutton_off.png'


def Start():
	Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
	Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
	MediaContainer.art = R(ART)
	MediaContainer.title1 = INDIGO_AUTHENTICATION_REALM
	DirectoryItem.thumb = R(ICON)
	Plugin.AddPrefixHandler(APPLICATIONS_INDIGO_PREFIX, MainMenu,"Indigo",ICON,ART)
	Plugin.AddPrefixHandler(VIDEO_INDIGO_PREFIX, MainMenu, "Indigo", ICON, ART)

def CreatePrefs():
	Prefs.Add(id="server_address",type="text",default="127.0.0.1",label="Server IP Address")
	Prefs.Add(id="server_port",type="text",default="8176",label="Server Port")
	Prefs.Add(id="server_username",type="text",default="",label="Server Username")
	Prefs.Add(id="server_password",type="text",default="",label="Server Password",option="hidden")
	Prefs.Add(id="plugin_quicktoggle",type="bool",default="false",label="Enable quick toggling of undimmable devices")
	Prefs.Add(id="plugin_brightnessincrement",type="text",default="10",label="Increments for increasing/decreasing brightness")

def ValidatePrefs():
	if(checkServer()):
		return MessageContainer("Success","IndigoServer contacted successfully.")
	else:
		return MessageContainer("Error","IndigoServer not found.  Please check your preferences.")

def MainMenu():
	theListing = MediaContainer(title1="Indigo",viewGroup="InfoList",art=R(ART),nocache=True, noHistory=False)

	# theDevices -- Indigo's "Devices" pane
	theDevices = DirectoryItem(theDevicesMenu, title="Devices")
	theDevices.subtitle = "Control individual devices"
	theDevices.summary = "A list of all devices controlled by Indigo"
	theDevices.thumb = R(ICON)
	theDevices.art = R(ART)

	# theActions -- Indigo's "Action Groups" pane
	theActions = DirectoryItem(theActionsMenu, title="Action Groups")
	theActions.subtitle = "Execute groups of actions"
	theActions.summary = "A list of all action groups within Indigo"
	theActions.thumb = R(ICON)
	theActions.art = R(ART)

	# theVariables -- Indigo's variables
	theVariables = DirectoryItem(theVariablesMenu, title="Variables")
	theVariables.subtitle = "View and edit Indigo variables"
	theVariables.summary = "A list of all variables and their values"
	theVariables.thumb = R(ICON)
	theVariables.art = R(ART)

	if(not checkServer()):
		theListing.Append(PrefsItem(title="Error",subtitle="Could not authenticate with Indigo Server",summary="Please check your server address, port, username, and password."))
	else:
		theListing.Append(Function(theDevices))
		theListing.Append(Function(theActions))
		theListing.Append(Function(theVariables))
		theListing.Append(PrefsItem(title="Preferences",subtitle="Indigo Preferences",summary="...."))	
	return theListing

def ReturnBooleanOf(theString):
	return theString.upper() == "TRUE"

def theVariablesMenu(sender):
	theHistoryBoolean=True
	theListing = MediaContainer(title1="Variables",viewGroup="InfoList",art=R(ART),nocache=True, noHistory=theHistoryBoolean)
	theVariableListing = getServerRequest("variables.xml")
	if theVariableListing[0] == True:
		theListing = getListingOfVariables(theListing, theVariableListing[1])
	else:
		theListing.Append(PrefsItem(title="Error",subtitle="Could not authenticate with Indigo Server",summary="Please check your server address, port, username, and password."))
	return theListing

def theActionsMenu(sender):
	theHistoryBoolean=True
	theListing = MediaContainer(title1="Actions",viewGroup="InfoList",art=R(ART),nocache=True, noHistory=theHistoryBoolean)
	theActionListing = getServerRequest("actions.xml")
	if theActionListing[0] == True:
		theListing = getListingOfActions(theListing, theActionListing[1])
	else:
		theListing.Append(PrefsItem(title="Error",subtitle="Could not authenticate with Indigo Server",summary="Please check your server address, port, username, and password."))
	return theListing		

def theDevicesMenu(sender):
	theHistoryBoolean=True
	theListing = MediaContainer(title1="Devices",viewGroup="InfoList",art=R(ART),nocache=True, noHistory=theHistoryBoolean)
	theDeviceListing = getServerRequest("devices.xml")
	if theDeviceListing[0] == True:
		theListing = getListingOfDevices(theListing, theDeviceListing[1])
	else:
		theListing.Append(PrefsItem(title="Error",subtitle="Could not authenticate with Indigo Server",summary="Please check your server address, port, username, and password."))
	return theListing

def thisDeviceMenu(sender,thisDeviceDictionary):
	theListing = MediaContainer(title1=thisDeviceDictionary['Name'],viewGroup="InfoList",nocache=True,noHistory=True)
	if isOnOffable(thisDeviceDictionary):
		if thisDeviceDictionary['IsOn']:
			theToggleString = "Turn off"
		else:
			theToggleString = "Turn on"
		theListing.Append(Function(DirectoryItem(deviceTogglePower,title=theToggleString),thisDeviceDictionary=thisDeviceDictionary))
	if thisDeviceDictionary['SupportsDim']:
		theListing.Append(Function(PopupDirectoryItem(deviceDim,title="Set brightness"),thisDeviceDictionary=thisDeviceDictionary))
	return theListing

def theNullMenu(sender,thisThingDictionary=None,thisVariableDictionary=None,thisActionDictionary=None,thisDeviceDictionary=None):
	theListing = MediaContainer(title1="Null",viewGroup="InfoList",nocache=True,noHistory=True)
	return theListing


def isOnOffable(thisDeviceDictionary):
	theBadTypes = ('Motion Sensor','TriggerLinc')
	if not thisDeviceDictionary['Type'] in theBadTypes:
		if thisDeviceDictionary['SupportsOnOff']:
			return True
	return False	

def isQuickToggleable(thisDeviceDictionary):
	if Prefs.Get('plugin_quicktoggle'):
		if isOnOffable(thisDeviceDictionary):
			if not thisDeviceDictionary['SupportsDim']:
				return True
	return False			

def deviceDim(sender, thisDeviceDictionary):
	theListing = MediaContainer(title1=thisDeviceDictionary['Name']+" Brightness Level",viewGroup="InfoList",nocache=True,noHistory=True)
	theListing.Append(Function(DirectoryItem(deviceSetDimLevel,title="Turn "+ thisDeviceDictionary['Name'] +" off"),thisDeviceDictionary=thisDeviceDictionary,theLevel=0))
	thePossibleValues = range(int(Prefs.Get('plugin_brightnessincrement')),100,int(Prefs.Get('plugin_brightnessincrement')))
	for thisDimLevel in thePossibleValues:
		theListing.Append(Function(DirectoryItem(deviceSetDimLevel,title="Set brightness to " + str(thisDimLevel), subtitle=thisDeviceDictionary['Name']),thisDeviceDictionary=thisDeviceDictionary,theLevel=thisDimLevel))
	theListing.Append(Function(DirectoryItem(deviceSetDimLevel,title="Turn "+ thisDeviceDictionary['Name'] +" on"),thisDeviceDictionary=thisDeviceDictionary,theLevel=100))
	return theListing

def deviceSetDimLevel(sender, thisDeviceDictionary, theLevel):
	getServerRequest(theServerPath=thisDeviceDictionary['Path'] + '?brightness=' + str(theLevel) + '&_method=put')
	return theDevicesMenu(sender)

def deviceQuickToggle(sender, thisDeviceDictionary):
	return deviceTogglePower(sender, thisDeviceDictionary)

def variableEdit(sender, thisVariableDictionary):
	theListing = MediaContainer(title=thisVariableDictionary['Name'],viewGroup="InfoList",nocache=True,noHistory=True)
	if not thisVariableDictionary['ReadOnly']:
		theListing.Append(Function(InputDirectoryItem(key=variableSetValue,title="Change value", subtitle=thisVariableDictionary['Name'],prompt="Please enter a new value for "+thisVariableDictionary['Name']),thisVariableDictionary=thisVariableDictionary))
	return theListing

def variableSetValue(sender, query, thisVariableDictionary):
	getServerRequest(theServerPath=thisVariableDictionary['Path'] + '?_method=put&value=' + str(query))
	return theVariablesMenu(sender)

def actionExecute(sender, thisActionDictionary):
	getServerRequest(theServerPath=thisActionDictionary['Path'] + '?_method=execute')
	return theActionsMenu(sender)

def deviceTogglePower(sender, thisDeviceDictionary):
	if thisDeviceDictionary['IsOn']:
		theIsOn = "0"
	else:
		theIsOn = "1"
	getServerRequest(theServerPath=thisDeviceDictionary['Path'] + '?isOn=' + theIsOn + '&_method=put')		
	return theDevicesMenu(sender)

def getListingOfVariables(theListing, theVariableXML):
	return getListingOfVariablesByType(theListing, theVariableXML)

def getListingOfActions(theListing, theActionXML):
	return getListingOfActionsByType(theListing, theActionXML)

def getListingOfDevices(theListing, theDeviceXML):
	return getListingOfDevicesByType(theListing, theDeviceXML)

def getListingOfVariablesByType(theListing, theVariableXML):
	theRootVariable = etree.fromstring(theVariableXML)
	for thisVariable in theRootVariable:
		thisVariablePath = "variables/" + urllib.quote(thisVariable.text.encode("utf-8")) + ".xml"
		thisVariableXML = getServerRequest(thisVariablePath)
		thisVariableDictionary = {}
		thisVariableDictionary['Name'] = thisVariable.text
		thisVariableDictionary['Path'] = thisVariablePath
		thisVariableDictionary['URL'] = "http://%s:%s/%s" % (Prefs.Get('server_address'),Prefs.Get('server_port'),thisVariablePath)
		if thisVariableXML[0]:
			thisVariableXMLObject = etree.fromstring(thisVariableXML[1])
			for thisElement in thisVariableXMLObject.iter():
				if thisElement.tag == "value":
					thisVariableDictionary['Value'] = thisElement.text
					if thisVariableDictionary['Value'] == None:
						thisVariableDictionary['Value'] = ""
				elif thisElement.tag == "readOnly":
					thisVariableDictionary['ReadOnly'] = ReturnBooleanOf(thisElement.text)
		# Initialize the variable editing interface.
		if not thisVariableDictionary['ReadOnly']:
			thisVariableItem = InputDirectoryItem(key=variableSetValue, title=thisVariable.text + " = " + thisVariableDictionary['Value'], summary="",prompt="Please enter a new value for "+thisVariableDictionary['Name'])
		else:
			thisVariableItem = PopupDirectoryItem(key=theNullMenu,title=thisVariable.text + " = " + thisVariableDictionary['Value'],summary="")
		theListing.Append(Function(thisVariableItem,thisVariableDictionary=thisVariableDictionary))
	return theListing

def getListingOfActionsByType(theListing, theActionXML):
	theRootAction = etree.fromstring(theActionXML)
	for thisAction in theRootAction:
		thisActionPath = "actions/" + urllib.quote(thisAction.text.encode("utf-8")) + ".xml"
		# thisActionXML = getServerRequest(thisActionPath)
		thisActionDictionary = {}
		thisActionDictionary['Name'] = thisAction.text
		thisActionDictionary['Path'] = thisActionPath
		thisActionDictionary['URL'] = "http://%s:%s/%s" % (Prefs.Get('server_address'),Prefs.Get('server_port'),thisActionPath)
		
		# Initialize the "quick execute" menu item.
		thisActionItem = DirectoryItem(key=actionExecute, title=thisAction.text, summary="")

		theListing.Append(Function(thisActionItem,thisActionDictionary=thisActionDictionary))
	return theListing
		

def getListingOfDevicesByType(theListing, theDeviceXML):
	theRootDevice = etree.fromstring(theDeviceXML)
	for thisDevice in theRootDevice:
		
		# Get the characteristics of the device.
		thisDevicePath = "devices/" + urllib.quote(thisDevice.text.encode("utf-8")) + ".xml"
		thisDeviceXML = getServerRequest(thisDevicePath)
		thisDeviceDictionary = {}
		thisDeviceDictionary['Name'] = thisDevice.text
		thisDeviceDictionary['Path'] = thisDevicePath
		thisDeviceDictionary['URL'] = "http://%s:%s/%s" % (Prefs.Get('server_address'),Prefs.Get('server_port'),thisDevicePath)
		if thisDeviceXML[0]:
			thisDeviceXMLObject = etree.fromstring(thisDeviceXML[1])
			for thisElement in thisDeviceXMLObject.iter():
				if thisElement.tag == "addressStr":
					thisDeviceDictionary['Address'] = thisElement.text
				elif thisElement.tag == "desc":
					thisDeviceDictionary['Description'] = thisElement.text
				elif thisElement.tag == "isOn":
					thisDeviceDictionary['IsOn'] = ReturnBooleanOf(thisElement.text)
				elif thisElement.tag == "brightness":
					thisDeviceDictionary['Brightness'] = int(thisElement.text)
				elif thisElement.tag == "type":
					thisDeviceDictionary['Type'] = thisElement.text
				elif thisElement.tag == "typeSupportsDim":
					thisDeviceDictionary['SupportsDim'] = ReturnBooleanOf(thisElement.text)
				elif thisElement.tag == "typeSupportsHVAC":
					thisDeviceDictionary['SupportsHVAC'] = ReturnBooleanOf(thisElement.text)
				elif thisElement.tag == "typeSupportsIO":
					thisDeviceDictionary['SupportsIO'] = ReturnBooleanOf(thisElement.text)
				elif thisElement.tag == "typeSupportsOnOff":
					thisDeviceDictionary['SupportsOnOff'] = ReturnBooleanOf(thisElement.text)
				elif thisElement.tag == "typeSupportsSprinkler":
					thisDeviceDictionary['SupportsSprinkler'] = ReturnBooleanOf(thisElement.text)
				elif thisElement.tag == "setpointCool":
					thisDeviceDictionary['Setpoint_Cool'] = int(thisElement.text)
				elif thisElement.tag == "setpointHeat":
					thisDeviceDictionary['Setpoint_Heat'] = int(thisElement.text)
				elif thisElement.tag == "hvacCurrentMode":
					thisDeviceDictionary['Mode_HVACCurrent'] = thisElement.text
				elif thisElement.tag == "hvacFanMode":
					thisDeviceDictionary['Mode_HVACFan'] = thisElement.text
				elif thisElement.tag == "inputHumidityVals":
					thisDeviceDictionary['Humidity'] = int(thisElement.text)
				elif thisElement.tag == "inputTemperatureVals":
					thisDeviceDictionary['Temperature'] = int(thisElement.text)
		
		# Initialize the type of menu item based on preferences.
		if isQuickToggleable(thisDeviceDictionary):
			thisDeviceItem = DirectoryItem(key=deviceQuickToggle, title=thisDevice.text, summary="")
		else:
			thisDeviceItem = PopupDirectoryItem(key=thisDeviceMenu, title=thisDevice.text, summary="")

		# Set some characteristics of the menu item.
		try:
			thisDeviceItem.subtitle=thisDeviceDictionary['Description']
		except KeyError:
			thisDeviceItem.subtitle=''
		if thisDeviceDictionary['SupportsOnOff']:
			if thisDeviceDictionary['IsOn']:
				thisDeviceItem.thumb = R(LIGHT_ON_ICON)
			else:
				thisDeviceItem.thumb = R(LIGHT_OFF_ICON)

		# Append the menu item.
		theListing.Append(Function(thisDeviceItem,thisDeviceDictionary=thisDeviceDictionary))
	return theListing

def getServerRequest(theServerPath=""):
	theServerAddress = Prefs.Get('server_address')
	if theServerAddress == '' or theServerAddress == None:
		theServerAddress = "127.0.0.1"
	theServerPort = Prefs.Get('server_port')
	if theServerPort == 0 or theServerPort == None:
		theServerPort = 8176
	theServerUsername = Prefs.Get('server_username')
	theServerPassword = Prefs.Get('server_password')
	theServerRealm = INDIGO_AUTHENTICATION_REALM
	theServerURL = "http://%s:%s/%s" % (theServerAddress, theServerPort,theServerPath)

	if theServerUsername != None and theServerPassword != None:
		theAuthHandler = urllib2.HTTPDigestAuthHandler()
		theAuthHandler.add_password(theServerRealm,theServerURL,theServerUsername,theServerPassword)
		theOpener = urllib2.build_opener(theAuthHandler)
		urllib2.install_opener(theOpener)
		try:
			thePageHandle = urllib2.urlopen(theServerURL)
		except urllib2.HTTPError, theError:
			return [False, theError]
		except urllib2.URLError, theError:
			return [False, theError]			
		try:
			theXMLString = thePageHandle.read()
		except AttributeError, theError:
			return [False, theError]
		return [True, theXMLString]

	else:
		try:
			theResponse = HTTP.Request(theServerURL)
		except urllib2.HTTPError, theError:
			return [False, theError]
		except urllib2.URLError, theError:
			return [False, theError]
		try:
			theXMLString = theResponse.read()
		except AttributeError, theError:
			return [False, theError]
		return [True, theXMLString]

def checkServer():
	theResponse = getServerRequest()
	return theResponse[0]