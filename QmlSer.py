#! D:\Python36\python.exe
import os
import sys
import configparser

from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, pyqtProperty

from serial import Serial
from serial.tools import list_ports


class QmlSer(QObject):
    def __init__(self, context, parent=None):
        super().__init__(parent)
        
        self.win = parent
        self.ctx = context

        self.cmbPort = self.win.findChild(QObject, 'cmbPort')
        self.cmbBaud = self.win.findChild(QObject, 'cmbBaud')
        self.cmbData = self.win.findChild(QObject, 'cmbData')
        self.cmbParity = self.win.findChild(QObject, 'cmbParity')
        self.cmbStop = self.win.findChild(QObject, 'cmbStop')

        self.txtMain = self.win.findChild(QObject, 'txtMain')
        self.txtSend = self.win.findChild(QObject, 'txtSend')

        self.chkRHex = self.win.findChild(QObject, 'chkRHex')
        self.chkWave = self.win.findChild(QObject, 'chkWave')
        self.chkTHex = self.win.findChild(QObject, 'chkTHex')
        self.chkLine = self.win.findChild(QObject, 'chkLine')
        self.chkTime = self.win.findChild(QObject, 'chkTime')

        self.btnOpen = self.win.findChild(QObject, 'btnOpen')

        self.ctx.setContextProperty('ports', ['%s (%s)' %(port, desc[:desc.index('(')]) for port, desc, hwid in list_ports.comports()])

        self.ser = Serial()

        self.initSetting()

        self.buffer = ''    #串口接收缓存

        self.tmrSer = QtCore.QTimer()
        self.tmrSer.setInterval(20)
        self.tmrSer.timeout.connect(self.on_tmrSer_timeout)
        self.tmrSer.start()

    def initSetting(self):
        if not os.path.exists('setting.ini'):
            open('setting.ini', 'w')
        
        self.conf = configparser.ConfigParser()
        self.conf.read('setting.ini')
        
        if not self.conf.has_section('serial'):
            self.conf.add_section('serial')
            self.conf.set('serial', 'port',     'COM0')
            self.conf.set('serial', 'baudrate', '9600')

        self.cmbPort.setProperty('currentIndex', self.cmbPort.find(self.conf.get('serial', 'port')))
        self.cmbBaud.setProperty('currentIndex', self.cmbBaud.find(self.conf.get('serial', 'baudrate')))

    @pyqtSlot()
    def on_btnOpen_clicked(self):
        if not self.ser.is_open:
            try:
                self.ser.timeout = 1
                self.ser.xonxoff = 0
                self.ser.port = self.cmbPort.property('currentText')[:self.cmbPort.property('currentText').index(' ')]
                self.ser.parity = self.cmbParity.property('currentText')[0]
                self.ser.baudrate = int(self.cmbBaud.property('currentText'))
                self.ser.bytesize = int(self.cmbData.property('currentText'))
                self.ser.stopbits = int(self.cmbStop.property('currentText'))
                self.ser.open()
            except Exception as e:
                print(e)
            else:
                self.btnOpen.setProperty('text', '关闭串口')
        else:
            self.ser.close()

            self.btnOpen.setProperty('text', '打开串口')

    @pyqtSlot()
    def on_btnSend_clicked(self):
        if self.ser.is_open:
            text = self.txtSend.property('text')
            if self.chkTHex.property('checkedState'):
                bytes = ' '.join([chr(int(c, 16)) for c in text.split()]).encode('latin')
            else:
                bytes = text.encode('latin') + (b'\r\n' if self.chkLine.property('checkedState') else b'')
            
            self.ser.write(bytes)

    def on_tmrSer_timeout(self):
        if self.ser.is_open:
            if self.ser.in_waiting > 0:
                bytes = self.ser.read(self.ser.in_waiting)
                
                self.txtMain.setProperty('text', self.txtMain.property('text') + bytes.decode('latin'))

    @pyqtSlot()
    def on_btnClear_clicked(self):
        self.txtMain.setProperty('text', '')

    @pyqtSlot()
    def on_closed(self):
        self.ser.close()

        self.conf.set('serial', 'port',     self.cmbPort.property('currentText'))
        self.conf.set('serial', 'baudrate', self.cmbBaud.property('currentText'))

        self.conf.write(open('setting.ini', 'w'))


if __name__ == '__main__':
    app = QGuiApplication(sys.argv)

    qml = QQmlApplicationEngine('QmlSer.qml')

    qml.rootContext().setContextProperty('Ser', QmlSer(qml.rootContext() ,qml.rootObjects()[0]))

    sys.exit(app.exec())
