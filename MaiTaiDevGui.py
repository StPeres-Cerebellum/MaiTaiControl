from PyQt5 import QtGui, QtCore
#from acq4.Manager import getManager, logExc, logMsg
#from acq4.devices.Laser.devTemplate import Ui_Form
#from acq4.devices.Laser.LaserDevGui import LaserDevGui
#from maiTaiTemplate import Ui_MaiTaiStatusWidget
import maiTaiControlTemplate
import numpy as np
from scipy import stats
from pyqtgraph.functions import siFormat
import time
from threading import *



class MaiTaiDevGui(QtGui.QMainWindow,maiTaiControlTemplate.Ui_MainWindow):
    
    listenSocketButtonChanged = QtCore.Signal(object)
    
    def __init__(self, dev):
        
        QtGui.QMainWindow.__init__(self)
        self.ui = maiTaiControlTemplate.Ui_MainWindow()
        self.ui.setupUi(self)
        
        
        #LaserDevGui.__init__(self,dev)
        self.dev = dev
        #self.dev.devGui = self  ## make this gui accessible from LaserDevice, so device can change power values. NO, BAD FORM (device is not allowed to talk to guis, it can only send signals)
        #self.ui = Ui_Form()
        #self.ui.setupUi(self)
        
        #self.calibrateWarning = self.dev.config.get('calibrationWarning', None)
        self.calibrateBtnState = 0
        
        ### configure gui
        ### hide group boxes which are not related to Mai Tai function 
        
        if self.dev.isLaserOn():
            self.onOffToggled(True)
            self.ui.turnOnOffBtn.setChecked(True)
            if self.dev.getInternalShutter():
                self.internalShutterToggled(True)
                self.ui.InternalShutterBtn.setChecked(True)
            self.ui.InternalShutterBtn.setEnabled(True)
        else:
            self.ui.InternalShutterBtn.setEnabled(False)
                
        #self.ui.MaiTaiGroup.hide()
        #self.ui.turnOnOffBtn.hide()
        
        self.wlBounds = self.dev.getWavelengthRange()
        startWL = self.dev.getWavelength()
        self.ui.wavelengthSpin_2.setOpts(suffix='m', siPrefix=True, dec=False, step=5e-9)
        self.ui.wavelengthSpin_2.setValue(startWL)
        self.ui.wavelengthSpin_2.setOpts(bounds=self.wlBounds)
        self.ui.currentWaveLengthLabel.setText(siFormat(startWL, suffix='m'))
        
        self.socketListenThread = Thread(target=self.socketListening) # listenThread
        
        self.ui.wavelengthSpin_2.valueChanged.connect(self.wavelengthSpinChanged)
        
        self.ui.turnOnOffBtn.toggled.connect(self.onOffToggled)
        self.ui.InternalShutterBtn.toggled.connect(self.internalShutterToggled)
        #self.ui.ExternalShutterBtn.toggled.connect(self.externalShutterToggled)
        #self.ui.externalSwitchBtn.toggled.connect(self.externalSwitchToggled)
        #self.ui.linkLaserExtSwitchCheckBox.toggled.connect(self.linkLaserExtSwitch)
        self.ui.alignmentModeBtn.toggled.connect(self.alignmentModeToggled)
        
        self.ui.listenToSocketBtn.clicked.connect(self.activateSocket)

        self.dev.sigOutputPowerChanged.connect(self.outputPowerChanged)
        self.dev.sigSamplePowerChanged.connect(self.samplePowerChanged)
        self.dev.sigPumpPowerChanged.connect(self.pumpPowerChanged)
        self.dev.sigRelativeHumidityChanged.connect(self.relHumidityChanged)
        self.dev.sigPulsingStateChanged.connect(self.pulsingStateChanged)
        self.dev.sigWavelengthChanged.connect(self.wavelengthChanged)
        self.dev.sigModeChanged.connect(self.modeChanged)
        self.dev.sigP2OptimizationChanged.connect(self.p2OptimizationChanged)
        self.dev.sigHistoryBufferChanged.connect(self.historyBufferChanged)
        self.dev.sigHistoryBufferPumpLaserChanged.connect(self.historyBufferPumpLaserChanged)
        self.listenSocketButtonChanged.connect(self.listenSocketButtonState)
        
    def onOffToggled(self, b):
        if b:
            self.dev.switchLaserOn()
            self.ui.turnOnOffBtn.setText('Turn Off Laser')
            self.ui.turnOnOffBtn.setStyleSheet("QLabel {background-color: #C00}") 
            self.ui.EmissionLabel.setText('Emission ON')
            self.ui.EmissionLabel.setStyleSheet("QLabel {color: #C00}")
            self.ui.InternalShutterBtn.setEnabled(True)
        else:
            self.dev.switchLaserOff()
            self.internalShutterToggled(False)
            self.ui.turnOnOffBtn.setText('Turn On Laser')
            self.ui.turnOnOffBtn.setStyleSheet("QLabel {background-color: None}")
            self.ui.EmissionLabel.setText('Emission Off')
            self.ui.EmissionLabel.setStyleSheet("QLabel {color: None}") 
            self.ui.InternalShutterBtn.setEnabled(False)
            
    def internalShutterToggled(self, b):
        if b:
            #if self.ui.linkLaserExtSwitchCheckBox.isChecked():
            #    self.dev.externalSwitchOFF()
            #    self.ui.externalSwitchBtn.setChecked(False)
            #    self.ui.externalSwitchBtn.setText('External Switch OFF')
            self.dev.openInternalShutter()
            self.ui.InternalShutterBtn.setText('Close Laser Shutter')
            self.ui.InternalShutterLabel.setText('Laser Shutter Open')
            self.ui.InternalShutterLabel.setStyleSheet("QLabel {color: #0A0}")
        elif not b:
            self.dev.closeInternalShutter()
            self.ui.InternalShutterBtn.setText('Open Laser Shutter')
            #self.ui.shutterBtn.setStyleSheet("QLabel {background-color: None}")
            self.ui.InternalShutterLabel.setText('Laser Shutter Closed')
            self.ui.InternalShutterLabel.setStyleSheet("QLabel {color: None}")
            #if self.ui.linkLaserExtSwitchCheckBox.isChecked():
            #    self.dev.externalSwitchON()
            #    self.ui.externalSwitchBtn.setChecked(True)
            #    self.ui.externalSwitchBtn.setText('External Switch ON')
    
    def externalShutterToggled(self, b):
        if b:
            self.dev.openShutter()
            self.ui.ExternalShutterBtn.setText('Close External Shutter')
            self.ui.ExternalShutterLabel.setText('External Shutter Open')
            self.ui.ExternalShutterLabel.setStyleSheet("QLabel {color: #10F}") 
        elif not b:
            self.dev.closeShutter()
            self.ui.ExternalShutterBtn.setText('Open External Shutter')   
            self.ui.ExternalShutterLabel.setText('External Shutter Closed')
            self.ui.ExternalShutterLabel.setStyleSheet("QLabel {color: None}")
    
    #def externalSwitchToggled(self,b):
    #    if b:
    #        self.dev.externalSwitchON()
    #        self.ui.externalSwitchBtn.setText('External Switch ON')
    #    elif not b:
    #        self.dev.externalSwitchOFF()
    #        self.ui.externalSwitchBtn.setText('External Switch OFF')
    
    def linkLaserExtSwitch(self,b):
        if b:
            self.ui.externalSwitchBtn.setEnabled(False)
        elif not b:
            self.ui.externalSwitchBtn.setEnabled(True)
    
    def alignmentModeToggled(self,b):
        if b:
            self.dev.acitvateAlignmentMode()
            self.ui.alignmentModeBtn.setText('Alignment Mode ON')
        elif not b:
            self.dev.deactivateAlignmentMode()
            self.ui.alignmentModeBtn.setText('Alignment Mode OFF')
            
    
    def wavelengthChanged(self,wl):
        if wl is None:
            self.ui.currentWaveLengthLabel.setText("?")
        else:
            self.ui.currentWaveLengthLabel.setText(siFormat(wl, suffix='m'))
        
    def wavelengthSpinChanged(self, value):
        self.dev.setWavelength(value)
        #if value not in self.dev.config.get('namedWavelengths', {}).keys():
        #    self.ui.wavelengthCombo.setCurrentIndex(0)
    

    def samplePowerChanged(self, power):
        if power is None:
            self.ui.samplePowerLabel.setText("?")
        else:
            self.ui.samplePowerLabel.setText(siFormat(power, suffix='W'))

    def outputPowerChanged(self, power ):
        if power is None:
            self.ui.outputPowerLabel.setText("?")
        else:
            self.ui.outputPowerLabel.setText(siFormat(power, suffix='W'))
        
        self.ui.outputPowerLabel.setStyleSheet("QLabel {color: #C00}")
        #if not valid:
        #    self.ui.outputPowerLabel.setStyleSheet("QLabel {color: #C00}")
        #else:
        #    self.ui.outputPowerLabel.setStyleSheet("QLabel {color: #000}")
    
    def p2OptimizationChanged(self,p2Opt):
        if p2Opt is None:
            self.ui.P2OptimizationLabel.setText("?")
        elif p2Opt:
            self.ui.P2OptimizationLabel.setText("ON")
        elif not p2Opt:
            self.ui.P2OptimizationLabel.setText("OFF")
    
    def historyBufferChanged(self, hist):
        if hist is None:
            self.ui.systemStatusLabel.setText("?")
        else:
            self.ui.systemStatusLabel.setText(str(hist))
    
    def historyBufferPumpLaserChanged(self, histPL):
        if histPL is None:
            self.ui.pumpLaserSystemStatusLabel.setText("?")
        else:
            self.ui.pumpLaserSystemStatusLabel.setText(str(histPL))
    
    def pumpPowerChanged(self,pumpPower):
        if pumpPower is None:
            self.ui.pumpPowerLabel.setText("?")
        else:
            self.ui.pumpPowerLabel.setText(siFormat(pumpPower, suffix='W'))
    
    def relHumidityChanged(self, humidity):
        if humidity is None:
            self.ui.relHumidityLabel.setText("?")
        else:
            self.ui.relHumidityLabel.setText(siFormat(humidity, suffix='%'))
    
    def modeChanged(self, mode):
        if mode is None:
            self.ui.pumpModeLabel.setText("?")
        else:
            self.ui.pumpModeLabel.setText(mode)
    
    def pulsingStateChanged(self, pulsing):
        if pulsing:
            self.ui.PulsingLabel.setText('Pulsing')
            self.ui.PulsingLabel.setStyleSheet("QLabel {color: #EA0}")
        else:
            self.ui.PulsingLabel.setText('Not Pulsing')
            self.ui.PulsingLabel.setStyleSheet("QLabel {color: None}")
            
    def activateSocket(self):
        #
        if self.socketListenThread.is_alive():
            self.listenSocketButtonChanged.emit('inactive')
            self.listenToSocket=False
            self.socketListenThread = Thread(target=self.socketListening)
            print 'socket inactive'
        else:
            self.listenSocketButtonChanged.emit('active')
            self.socketListenThread.start()
            print 'socket active'

    def socketListening(self):
        self.listenToSocket = True
        print 'before connect'
        self.dev.socket_connect()
        print 'active with '+self.dev.remoteAddr[0]
        try:
            self.ui.socketConnectionLabel.setText('active with '+str(self.dev.remoteAddr[0]))
        except:
            pass
        while self.listenToSocket:
            do_read = False
            try:
                #print 'waiting for for connection to be established'
                #self.c,addr = self.s.accept() #Establish a connection with the client
                #print 'select select'
                do_read = self.dev.socket_monitor_activity()
            except:
                pass
            if do_read:
                try:
                    #print 'before recv'
                    data = self.dev.socket_read_data()
                    if data == 'disconnect':
                        self.dev.socket_send_data('OK..'+data)
                        print 'socket connection was closed by remote host'
                        self.activateSocket() # fist close connection
                        self.activateSocket() # then re-initiate listening
                        break
                    if not 'getPos' in data:
                        print "Got data: ", data
                    res = self.performRemoteInstructions(data)
                    self.dev.socket_send_data(str(res)+'...'+data)
                except :
                    print 'socket connection closed due to error'
                    self.activateSocket()
                    break
        try:
            self.ui.socketConnectionLabel.setText('inactive')
        except:
            pass
        print 'after thread'
        self.dev.socket_close_connection()  
   
    def listenSocketButtonState(self, newState):
        if newState == 'inactive':
            self.ui.listenToSocketBtn.setChecked(False)
            self.ui.listenToSocketBtn.setText('Listen to Socket')
            self.ui.listenToSocketBtn.setStyleSheet('background-color:None')
        elif newState == 'active':
            self.ui.listenToSocketBtn.setChecked(True)
            self.ui.listenToSocketBtn.setText('Stop listening to Socket')
            self.ui.listenToSocketBtn.setStyleSheet('background-color:red')
    
    def performRemoteInstructions(self,rawData):
        data = rawData.split(',')
        #
        print data
        if data[0] == 'switchLaserOn':
            self.ui.turnOnOffBtn.setChecked(True)
            return (1,self.dev.isLaserOn())
        elif data[0] == 'switchLaserOff':
            self.ui.turnOnOffBtn.setChecked(False)
            return (1,self.dev.isLaserOn())
        elif data[0] == 'isLaserOn':
            return (1,self.dev.isLaserOn())
        elif data[0] == 'getRelativeHumidity':
            return (1,self.dev.humidity())
        elif data[0] == 'getPower':
            return (1,self.dev.outputPower())
        elif data[0] == 'getWavelength':
            return (1,self.dev.getWavelength())
        elif data[0] == 'setWavelength':
            self.ui.wavelengthSpin_2.setValue(float(data[1]))
            return (1,self.dev.getWavelength())
        elif data[0] == 'getWavelengthRange':
            return (1,self.dev.getWavelengthRange())
        elif data[0] == 'getPumpPower':
            return (1,self.dev.getPumpPower())
        elif data[0] == 'getShutter':
            #print self.dev.getInternalShutter(), dtype(self.dev.getInternalShutter())
            return (1,self.dev.getInternalShutter())
        elif data[0] == 'setShutter':
            if data[1] == 'True' or data[1] == ' True':
                self.ui.InternalShutterBtn.setChecked(True)
            elif data[1] == 'False' or data[1] == ' False':
                self.ui.InternalShutterBtn.setChecked(False)
        elif data[0] == 'checkPulsing':
            return (1,self.dev.pulsing())
        elif data[0] == 'getStatus':
            return (1,self.dev.maiTaiHistory)
        elif data[0] == 'getStatusPumpLaser':
            return (1,self.dev.maiTaiPumpLaserHistory)
        else:
            return 0
        
    def closeEvent(self, event):
        print 'stopping threads'
        self.listenToSocket = False
        time.sleep(.2)
        self.dev.closeConnections()
        
        
        
       
        
