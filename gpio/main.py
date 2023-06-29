#! /usr/bin/env python
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import QThread, QCoreApplication, QObject, pyqtSignal
from threading import Thread, Lock
from PyQt5 import uic
import time
import redis
import serial
import socket, sys
import json
from loguru import logger
import os

GPIO_HOST = os.getenv("GPIO_HOST", "127.0.0.1")


class Interface_ESP32(QObject):
    
    sendNewCmd = pyqtSignal(['QString'])

    def __init__(self):
        super(Interface_ESP32,self).__init__()        
        self.port = os.getenv("USB_PORT", "/dev/ttyUSB0")
        self.baud = 115200

        # Tạo thread quan lý việc gửi dữ liệu phản hồi từ cảm biến tới mô đun trung tâm
        # Địa chỉ cổng nhận tin của mô đun trung tâm: 127.0.0.1:6666
        self.sendFeedback = SendUDP(f'{GPIO_HOST}:6666',parent=self)
        self.sendFeedback.start()

        # Tạo thread quản lý việc giao tiếp với ESP32 qua cổng COM/USB
        self.Thread_ReadWriteData = ReadWriteESP32(self.port,self.baud,parent=self)
        self.Thread_ReadWriteData.newReading.connect(self.sendFeedback.sendMsg)
        self.Thread_ReadWriteData.start()
        
        # Tạo thread quản lý việc nhận mệnh lệnh (đóng/mở) cửa từ mô đun trung tâm
        # Địa chỉ cổng nhận tin: '127.0.0.1:8888'
        self.getCommand = ReceiveUDP(f'{GPIO_HOST}:8888',GPIO_HOST,self)
        self.getCommand.newCommand.connect(self.Thread_ReadWriteData.sendCmd)
        self.getCommand.start()   
    
class ReadWriteESP32(QThread):
    newReading = pyqtSignal(['QString'])
    def __init__(self,port,baud,parent):
        QThread.__init__(self,parent)
        self.port = port
        self.baud = baud
        self.SerConnection = serial.Serial(self.port,self.baud)
        
    def sendCmd(self,data):
        data_str = data.decode()
        #print("command:", data_str)
        cmd = ''
        # Xử lý các lệnh mở cửa
        if data_str[1]=='O': # open
            cmd = 'O{0}\n'
            if data_str=='@O1':
                cmd_send = cmd.format(1)
            elif data_str=='@O2':
                cmd_send = cmd.format(2)
            elif data_str=='@O3':
                cmd_send = cmd.format(3)
            elif data_str=='@O4':
                cmd_send = cmd.format(4)
        # Xử lý các lệnh đóng cửa
        elif data_str[1]=='C': # close
            cmd = 'C{0}\n'
            if data_str=='@C1':
                cmd_send = cmd.format(1)
            elif data_str=='@C2':
                cmd_send = cmd.format(2)
            elif data_str=='@C3':
                cmd_send = cmd.format(3)
            elif data_str=='@C4':
                cmd_send = cmd.format(4)
        if (cmd != ''):
            # Truyền lệnh đóng/mở cửa xuống VĐK ESP32
            self.SerConnection.write(cmd_send.encode())
            logger.info("sent command '{}' to ESP32".format(cmd_send))
            # Flushing by time delay
            time.sleep(1.5)

    def run(self):
        while True:
            # Nhận toàn bộ dữ liệu phản hồi truyền từ ESP32
            # Frame dữ liệu: '@GN'
            #       - N là số thứ tự của cảm biến, 
            #       - Ví dụ, @G1: cảm biến 1 bị kích hoạt, nghĩa là có người đi qua cửa số 1
            data = str(self.SerConnection.readline(),'utf-8')
            if data.startswith('@'):
                self.SerConnection.reset_input_buffer()
                self.newReading.emit(data)

class SendUDP(QThread):
    def __init__(self, remote_address,parent = None):        
        QThread.__init__(self,parent)
        self.remote_address = remote_address
        self.send_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        address = self.remote_address.split(':')
        self.remote_UDP_address = (address[0],int(address[1]))
        self.parent = parent

    def sendMsg(self,msg):  
        # Truyền toàn bộ phản hồi nhận được từ VĐK ESP32 tới mô đun trung tâm 
        # (bao gồm cả trạng thái cảm biến hoặc trạng thái đã đóng/mở cửa)
        if msg.startswith('@'):
            logger.info("sent feedback: {}".format(msg))
            self.send_socket.sendto(msg.encode(),self.remote_UDP_address)
        

class ReceiveUDP(QThread):
    newCommand = pyqtSignal(bytes)

    def __init__(self, local_address, remote_IP, parent = None):        
        QThread.__init__(self,parent)
        self.local_address = local_address
        self.local_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        address = self.local_address.split(':')
        self.local_socket.bind((address[0],int(address[1])))
        self.remote_IP = remote_IP

    def run(self):
        while True:    
            msg_master, add = self.local_socket.recvfrom(1024)
            if (add[0]==self.remote_IP):
                if msg_master:                    
                    self.newCommand.emit(msg_master)


def send_socket(address, msg):
    if isinstance(msg, str):
        msg = msg.encode()
    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPClientSocket.sendto(msg, address)
    return


def connect_redis():

    redis_conn = redis.Redis(
        host=os.getenv("REDIS_HOST", "127.0.0.1"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=0
    )

    connected = False
    while not connected:
        try:
            redis_conn.ping()
            connected = True
            logger.info("Redis connected!")
        except:
            connected = False
            logger.warning("Redis disconnected!")
            time.sleep(5.0)

    return redis_conn


def release_gpio():
    GATE_TIMEOUT = float(os.getenv("GATE_TIMEOUT", "5.0"))
    redis_conn = connect_redis()

    while True:
        for gate_key in ['G1', 'G2', 'G3', 'G4']:
            gate_value = redis_conn.get(gate_key)
            logger.info("Gate: {}, Status: {}".format(gate_key, gate_value))

            if gate_value is None:  # init
                continue

            gate_value = json.loads(gate_value.decode())
            if not gate_value['status']:  # status 0 is close
                continue

            # gate is open
            current_time = int(time.time())
            if current_time - gate_value['time'] >= GATE_TIMEOUT:  # close gate if timeout
                gate_data = {
                    'time': current_time,
                    'status': 0
                }
                send_socket((GPIO_HOST, 8888), f"@C{gate_key[1]}")  # send close signal
                redis_conn.set(gate_key, json.dumps(gate_data))

        time.sleep(1.0)


if __name__ == "__main__":
    Thread(target=release_gpio).start()
    app = QCoreApplication(sys.argv)
    new_thread_app = Interface_ESP32()
    sys.exit(app.exec_())
