from PyQt5.QtWidgets import QApplication, QMainWindow  # Show-GUI
from PyQt5.QtCore import QTimer, QDateTime, Qt  # Timer !
from PyQt5.QtGui import QPixmap  # Images
from PyQt5 import uic, QtCore, QtWidgets, QtSerialPort
from datetime import datetime
import sys, requests, json
import re
import uuid
import numpy as np
import math
import traceback

import RPi.GPIO as GPIO
from hx711 import HX711

#url = "http://104.254.247.37:8181/" @
comScanner = "/dev/rfcomm0"
url = "http://10.20.10.103:92/"
dataScanner = ""
bufferScannerData = ""
dataWeighting = ""
bufferWeightingData = ""
weightData = 0 
userValid = False
userID = ''
wasteID = ''
DataWaste = '' 
#Wighting program
hx = HX711(13, 6)
output0 = 0
weightgain = 0
tare = 0
wightMonitoring = True
#waste Information
deviceName = "Raspberry_Pi4_001"
wasteStation = "Plastic Factory"
wasteCost = 0
wasteType = ""
WasteBG = ""
wasteCategory = ""
lastMsgID = ""

xCal = []
yCal = []
dataCalScan = ""

RequestTareData = float(0)

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("form_main.ui", self)
        
        #get data tare
        self.getTareData()
        # TIMER
        self.timer = QTimer()
        self.timer.timeout.connect(self.showTime)

        self.btnOverwrite.hide()
        self.btnAdd.hide()
        self.btnCancel.hide()
        self.btnOverwrite.hide()
        self.btnAdd.clicked.connect(self.AddWasteMeasurement)
        self.btnCancel.clicked.connect(self.CancelWasteMeasurement)
        self.btnOverwrite.clicked.connect(self.OverwriteWasteMeasurement)

        #Serial scanner
        self.serialScanner = QtSerialPort.QSerialPort(
            comScanner,
            baudRate=QtSerialPort.QSerialPort.Baud9600,
            readyRead=self.readScanner
        )
        self.serialScanner.open(QtCore.QIODevice.ReadWrite)
       
        self.tempOutputWeight = QtWidgets.QTextEdit(readOnly=True)
        """
        self.serialWeighting = QtSerialPort.QSerialPort(
            'COM8',
            baudRate=QtSerialPort.QSerialPort.Baud9600,
            readyRead=self.readWeighting
        )
        self.serialWeighting.open(QtCore.QIODevice.ReadWrite)
        """
    def getTareData(self):
        global output0  
        global weightgain
        global RequestTareData
        a_file = open("setting.json", "r")
        json_object = json.load(a_file)
        a_file.close()
        output0 = json_object["output0"]
        weightgain = json_object["gain"]
        RequestTareData = json_object["tarerequest"]
        RequestTareData = float(RequestTareData)
        print('RequestTareData', RequestTareData)
        print('RequestTareData', type(RequestTareData))
        
        
# Program Read Scanner
    @QtCore.pyqtSlot()
    def readScanner(self):
        global bufferScannerData
        global dataScanner
        dataReceive = self.serialScanner.readLine().data().decode()
        if dataReceive.find('\r') == -1:
            bufferScannerData = dataReceive
        else:
            dataReceive =  bufferScannerData + dataReceive
            bufferScannerData = ""
            dataReceive = dataReceive.strip()
            dataScanner = dataReceive
            self.processDataScanner()   

    def processDataScanner(self):
        global userID
        global wasteID
        global DataWaste

        self.txtScanner.setText(dataScanner)
        CodeIdentifier = dataScanner[0:1]
        CodeIdentifierTareData = dataScanner[0:2]
        if CodeIdentifier == "U":
            DataWaste = 1
            userID = dataScanner[1:]
            self.processUserData()
            
        elif (CodeIdentifier == "W"):
            if (DataWaste == 1):
                wasteID = dataScanner
                self.processWaste()            
            else:
                self.lblWasteCode.setText("please scan user")
                
        elif (CodeIdentifier == "T"):
            self.ChooseTareDataSet() 
            
        elif (CodeIdentifier == "C"):
            global dataCalScan
            dataCalScan = dataScanner
            self.updateCalibration()
            
#program Tare data
    def ChooseTareDataSet(self):
        dataScannerNonNumber = ''.join([i for i in dataScanner if not i.isdigit()])
        print('dataScannerNonNumber',dataScannerNonNumber)
        if (dataScannerNonNumber == 'T' or dataScannerNonNumber == 'TD'):
            print('TareData')
            self.updateTareData()
            
        elif (dataScannerNonNumber == 'TS'):
            print('Tareset')
            self.TareSet()
            
    def updateTareData(self):
        global output0
        global RequestTareData
        RequestTareData = float(0)
        a_file = open("setting.json", "r")
        json_object = json.load(a_file)
        a_file.close() 
        outputOld = json_object["output0"]
        #update Data
        output0 = hx.get_weight(5)
        
        a_file = open("setting.json", "r")
        json_object = json.load(a_file)
        a_file.close()
        print(json_object)
        json_object["tarerequest"] = RequestTareData
        a_file = open("setting.json", "w")
        json.dump(json_object, a_file)
        a_file.close()
            
        time = QDateTime.currentDateTime()
        timeDisplayLogTare = time.toString('dd-MM-yyyy hh:mm:ss')
        #TareLogTxt = open('TareLog.txt', 'a')
        #TareType = 'Standard Tare'
        #TareLogTxt.write("Time tare at :" + timeDisplayLogTare + ", Tare Type : " + TareType + ", Initial Weight0 : " + str(weightData) + ", Update Weight : " + str(RequestTareData) +  ", Initial Output : " + str(outputOld) + ", Update output : " + str(output0))
        #TareLogTxt.close()
        
        TareRequetsBeban = dataScanner[:2]
        print('TareRequetsBeban ', TareRequetsBeban)
        if(TareRequetsBeban == "TD"):
            a_file = open("setting.json", "r")
            json_object = json.load(a_file)
            a_file.close() 
            outputOld = json_object["output0"]
            output0 = hx.get_weight(5)
            
            TareRequetsBeban = dataScanner[2:]
            #Write Tare Data
            OpenTareset_file = open("Tareset.json", "r")
            OpenTareset_json_object = json.load(OpenTareset_file)
            OpenTareset_file.close()
            DataTareTerdetect = OpenTareset_json_object["Data Tare"][TareRequetsBeban]
            print('json_object',DataTareTerdetect)
            RequestTareData = float(DataTareTerdetect)
            
            a_file = open("setting.json", "r")
            json_object = json.load(a_file)
            a_file.close()
            print(json_object)
            json_object["tarerequest"] = RequestTareData
            a_file = open("setting.json", "w")
            json.dump(json_object, a_file)
            a_file.close()
            
            TareType = "Get Tare"
            TareProgressLogTxt = open('TareLog.txt', 'a')
            TareProgressLogTxt.write("\nTime tare at :" + timeDisplayLogTare + ", Tare Type : " + TareType + ", Initial Weight0 : " + str(weightData) + ", Update Weight : " + str(RequestTareData) +  ", Initial Output : " + str(outputOld) + ", Update output : " + str(output0))
            TareProgressLogTxt.close()
            
    def TareSet(self):
        global dataWeighting
        global output0
        global weightgain
        dataHX = hx.get_weight(5)
        alldataWeighting = (dataHX - output0)/weightgain        
        measureWeight = float(alldataWeighting)
        digitWeight = math.floor(measureWeight)
        decimalWeight = measureWeight - digitWeight
        additionaWeight = 0.0
        if (decimalWeight > 0.75):
            additionaWeight = 1
        elif (decimalWeight >= 0.5):
            additionaWeight = 0.5
        dataWeighting = round(digitWeight + additionaWeight, 1)   
        
        SetDataTare = dataScanner[2:]
        
        #Write Tare Data
        tareset_file = open("Tareset.json", "r")
        json_objectTare = json.load(tareset_file)
        tareset_file.close() 
        
        #Write Tare in JSON
        json_objectTare["Data Tare"][SetDataTare] = dataWeighting
        tareset_file = open("Tareset.json", "w")
        json.dump(json_objectTare, tareset_file)
        tareset_file.close()
        
        time = QDateTime.currentDateTime()
        timeDisplayLogTare = time.toString('dd-MM-yyyy hh:mm:ss')
        TareLogTxt = open('TareLog.txt', 'a')
        TareType = 'Set Tare'
        TareLogTxt.write("\nTime tare at :" + timeDisplayLogTare + ", Tare Type : " + TareType + ", Initial Weight0 : " + str(weightData) + ", Update Output : " + str(output0))
        TareLogTxt.close()
    
    def updateCalibration(self):
        codeCal = dataCalScan[1:2]
        print(codeCal)            
        global xCal           
        global yCal
        if (codeCal == "S"):
            xCal.clear()
            yCal.clear()
            
        elif (codeCal == "D"):
            weighData = int(dataCalScan[2:6]) / 10
            outputData = hx.get_weight(5)
            #outputData = 10 * weighData + 15
            xCal.append(weighData)
            yCal.append(outputData)
            print(xCal)
            print(yCal)
            
        elif (codeCal == "E"):
            coefficients = np.polyfit(xCal, yCal, 1)
            xCal.clear()
            yCal.clear()
            print(xCal)
            print(yCal)
            
            global output0                   
            global weightgain 
            
            time = QDateTime.currentDateTime() 
            timeDisplay = time.toString('dd-MM-yyyy hh:mm:ss')
             
            """
            with open('calibration_log.txt', 'a') as f:
                f.writeline("\n Calibration at " + timeDisplay + " initial weight gain : " +
                            weightgain + " , initial output0 : "  + output0 + " weight gain : " +
                            coefficients[0] + " , output0 : "  + coefficients[1])
            """
            
            print("o0: " + str(output0) + "w0: " + str(weightgain) + "o0: " + str(coefficients[1]) + "w0: " + str(coefficients[0]))
            output0   =   coefficients[1]
            weightgain =   coefficients[0]
            
            a_file = open("setting.json", "r")
            json_object = json.load(a_file)
            a_file.close()
            
            json_object["output0"] = coefficients[1]             
            json_object["gain"] = coefficients[0]  
            a_file = open("setting.json", "w")
            json.dump(json_object, a_file)
            a_file.close()
            
        
    def processWaste(self):
        if userValid:     
            self.lblWasteCode.setText(wasteID)       
            self.getWasteInfo()
        else:            
            self.lblWasteCode.setText("please scan user")

    def getWasteInfo(self):
        global wasteCost
        global wasteType
        global WasteBG
        global wasteCategory
        global lastMsgID
        global wightMonitoring

        DataToken = self.getToken()
        apiURL = url + "api/v1/measurements/latest/waste/" + wasteID
        payload = ""
        headers = {
            'Authorization': 'Bearer ' + DataToken
        }
        response = requests.request("GET", apiURL, headers=headers, data=payload)
        dataAPI = response.json()
        if dataAPI['dimensionInfo']:
            wightMonitoring = False
            self.readWeightingHX() 
            lblWasteInfo = dataAPI['dimensionInfo'][0]['itemDescription'] 
            wasteType = dataAPI['dimensionInfo'][0]['wasteType']  
            wasteCategory = dataAPI['dimensionInfo'][0]['wasteCategory'] 
            WasteBG = dataAPI['dimensionInfo'][0]['businessGrp']
            wasteCost = float(dataAPI['dimensionInfo'][0]['cost'])
            lblwasteLastData =  ""
            if dataAPI['value']:
                lblwasteLastData =  dataAPI['value']['weightInKg'] 
            
            lblWasteLastMeasurement = ""   
            if dataAPI['timeStamp']:
                lblWasteLastMeasurement =  dataAPI['timeStamp']    
                intialMeasuremet = datetime.strptime(lblWasteLastMeasurement, "%Y-%m-%d %H:%M:%S")
                currentMeasurement = datetime.now()
                rangemeasurement = (currentMeasurement - intialMeasuremet).total_seconds()
                if rangemeasurement < 8 * 3600:
                    lastMsgID = dataAPI['msgId'] 
                    self.lblWarning.setText("Warning On")
                    self.btnOverwrite.show()

            self.lblWasteInfo.setText(lblWasteInfo)
            self.lblWasteType.setText(wasteType)
            self.lblWasteCategory.setText(wasteCategory)
            self.lblWasteLastMeasurement.setText(lblWasteLastMeasurement)
            self.lblWasteBG.setText(WasteBG)
            self.lblwasteLastData.setText(str(lblwasteLastData))

            self.btnAdd.show()
            self.btnCancel.show()
        else:
            self.clearWasteInfo()
            self.lblWasteCode.setText(wasteID)
            self.lblWasteInfo.setText("waste not registered")        
        
    def processUserData(self):
        global userValid
        self.clearWasteInfo()
        DataToken = self.getToken()
        apiURL = url + "api/v1/users/" + userID
        payload = ""
        headers = {
            'Authorization': 'Bearer ' + DataToken
        }
        response = requests.request("GET", apiURL, headers=headers, data=payload)
        dataAPI = response.json()
        if dataAPI['data']:
            userId = dataAPI['data']['userId']
            userRole = dataAPI['data']['userRole']
            firstName = dataAPI['data']['firstName']
            userValid = True  
            self.lblUserID.setText(userId)    
            self.lblUserName.setText(firstName)    
            self.lblUserRole.setText(userRole)
        else:
            userValid = False
            self.lblUserID.setText("")    
            self.lblUserName.setText("")    
            self.lblUserRole.setText("")         

    def getToken(Self):        
        apiURL = url + "jwt/v1/access-token"
        payload = json.dumps({
            "clientId": "3d849185-c1d5-4d40-8f72-68596f844a22",
            "clientSecret": "MBjC9hVrWO4nb9VRPJA6W4lwLpc76wHvTa0YpA6H",
            "audience": "86079f85-06d9-422c-9fd5-eef3a9ecf2df"
        })
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", apiURL, headers=headers, data=payload)
        dataAPI = response.json()
        DataToken = dataAPI['data']['jsonWebToken']
        return DataToken
    
    def clearUsernameInfo(self):
        global DataWaste
        DataWaste = 0
        self.lblUserID.setText("")    
        self.lblUserName.setText("")    
        self.lblUserRole.setText("")
        
    def clearWasteInfo(self):
        self.lblWasteCode.setText("")
        self.lblWasteInfo.setText("")
        self.lblWasteType.setText("")
        self.lblWasteCategory.setText("")
        self.lblWasteLastMeasurement.setText("")
        self.lblWasteBG.setText("")
        self.lblwasteLastData.setText("")
        self.lblWeightData.setText("")
        self.lblWarning.setText("")

# Program Read Weight data
    def readWeightingHX(self):
        global dataWeighting
        global output0
        global weightgain
        dataHX = hx.get_weight(5)
        alldataWeighting = (dataHX - output0)/weightgain        
        measureWeight = float(alldataWeighting)
        digitWeight = math.floor(measureWeight)
        decimalWeight = measureWeight - digitWeight
        additionaWeight = 0.0
        if (decimalWeight > 0.75):
            additionaWeight = 1
        elif (decimalWeight >= 0.5):
            additionaWeight = 0.5
            
        dataWeighting = round(digitWeight + additionaWeight, 1)   
        self.updateWeight()
        
    def updateWeight(self):
        global RequestTareData
        global weightData
        measureWeight = float(dataWeighting)
        measureWeight = measureWeight - RequestTareData
        weightData = round(measureWeight, 1)
        self.lblWeightData.setText(str(weightData) + " KG")
        
    def AddWasteMeasurement(self):
        global wightMonitoring
        wightMonitoring = True
        
        global wasteID
        global wasteStation
        global wasteType
        global wasteCategory
        global wasteCost
        global weightData
        time = QDateTime.currentDateTime() 
        measurementTime = time.toString('yyyy-MM-dd hh:mm:ss')

        msgID = str(uuid.uuid4())
        DataToken = self.getToken()
        apiURL = url + "api/v1/measurements/publish" 
        payload = json.dumps({
            "timeStamp": measurementTime,
            "name": deviceName,
            "dimensions": {
                "waste": wasteID,
                "station": wasteStation,
                "wasteType": wasteType,
                "businessGrp": WasteBG,
                "wasteCategory": wasteCategory
            },
            "value": {
                "cost": wasteCost,
                "weightInKg": weightData
            },
            "valueMetaData": {
                "msgId": msgID,
                "userId": userID
            }
        })      
        headers = {
            'Authorization': 'Bearer ' + DataToken ,
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", apiURL, headers=headers, data=payload)  
        print("insert Measurement")   
        print(DataToken)     
        print(payload)      
        print(response.text)


        wasteID = ""
        wasteStation = ""
        wasteCategory = ""
        wasteCost = 0
        weightData = 0
        self.clearWasteInfo()
        self.clearUsernameInfo()
        self.hideButton()  

    def OverwriteWasteMeasurement(self):
        global wightMonitoring
        wightMonitoring = True
        
        global wasteID
        global wasteStation
        global wasteType
        global wasteCategory
        global wasteCost
        global weightData
        global lastMsgID

        time = QDateTime.currentDateTime() 
        measurementTime = time.toString('yyyy-MM-dd hh:mm:ss')
        DataToken = self.getToken()
        apiURL = url + "api/v1/measurements/publish" 
        payload = json.dumps({
            "timeStamp": measurementTime,
            "name": deviceName,
            "dimensions": {
                "waste": wasteID,
                "station": wasteStation,
                "wasteType": wasteType,
                "businessGrp": WasteBG,
                "wasteCategory": wasteCategory
            },
            "value": {
                "cost": wasteCost,
                "weightInKg": weightData
            },
            "valueMetaData": {
                "msgId": lastMsgID,
                "userId": userID
            }
        })      
        headers = {
            'Authorization': 'Bearer ' + DataToken ,
            'Content-Type': 'application/json'
        }
        response = requests.request("PUT", apiURL, headers=headers, data=payload)  
        print(payload)      
        print("insert Measurement")
        print(response.text)

        wasteID = ""
        wasteStation = ""
        wasteCategory = ""
        wasteCost = 0
        weightData = 0
        lastMsgID = ""
        self.clearWasteInfo()
        self.clearUsernameInfo()
        self.hideButton()  

    def CancelWasteMeasurement(self):
        global wightMonitoring
        wightMonitoring = True
        
        global wasteID
        global wasteStation
        global wasteType
        global wasteCategory
        global wasteCost
        global weightData
        wasteID = ""
        wasteStation = ""
        wasteCategory = ""
        wasteCost = 0
        weightData = 0
        self.clearWasteInfo()
        self.clearUsernameInfo()
        self.hideButton()   

    def hideButton(self):
        self.btnAdd.hide()
        self.btnCancel.hide()
        self.btnOverwrite.hide()

# PROGRAM TIME     
    def startTimer(self):
        self.timer.start(1000)

    def showTime(self):
        time = QDateTime.currentDateTime() 
        timeDisplay = time.toString('dd-MM-yyyy hh:mm:ss - dddd') + str(wightMonitoring)
        self.lblTime.setText(timeDisplay)
        if wightMonitoring:
            self.showWaste()
        
    def showWaste(self):
        global output0
        global weightgain        
        global tare
        global weightData
        global RequestTareData
        dataHX = hx.get_weight(5)
        dataWeighting = (dataHX - output0)/weightgain
        measureWeight = float(dataWeighting)
        measureWeight = measureWeight - RequestTareData
        digitWeight = math.floor(measureWeight)
        decimalWeight = measureWeight - digitWeight
        additionaWeight = 0.0
        if (decimalWeight > 0.75):
            additionaWeight = 1.0
        elif (decimalWeight >= 0.5):
            additionaWeight = 0.5
        weightData = round(digitWeight + additionaWeight, 1)
 #      self.lblWeightData.setText(str(dataHX))
        self.lblWeightData.setText(str(weightData) + " KG")
        
    def closeEvent(self, event):
        self.serialScanner.close()
        print("close")
        
    def appClose(self):
        self.serialScanner.close()
        print("close")
        
    def show_exception_and_exit(exc_type,exc_value,tb):
        time = QDateTime.currentDateTime()
        timeDisplayLogError = time.toString('dd-MM-yyyy hh:mm:ss')
        ErrorTxt = open('ErrorLog.txt', 'a')
        ErrorTxt.write("\n Error Reason : " + str(exc_value) + "\n At Time : " + timeDisplayLogError + "\n")
        ErrorTxt.close()
        raw_input('Press Key to Exit')
        sys.exit(-1)
    sys.excepthook = show_exception_and_exit

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    window.startTimer()
    sys.exit(app.exec())


