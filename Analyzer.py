import serial.tools.list_ports
import datetime

user = "aron"

def init():
    timestamp = "timestamp = " + str(datetime.datetime.now())
    f = open('data.ini', 'w')
    f.write("[init]\n" + timestamp + "\n")

def selectPort():
    ports = serial.tools.list_ports.comports()
    serialInst = serial.Serial()

    portList = []

    for port in ports:
        portList.append(str(port))
        print(str(port))

    val = input("Select Port: COM")

    for x in range(0, len(portList)):
        if portList[x].startswith("COM" + str(val)):
            portVar = "COM" + str(val)
            print(portList[x])

    serialInst.baudrate = 115200
    serialInst.port = portVar
    serialInst.open()
    serialInst.write("rq".encode('utf-8'))
    f = open('data.ini', 'a')
    f.write("[user." + user + ".data]\n")
    while True:
        if serialInst.in_waiting:
            packet = serialInst.readline()
            f.write(packet.decode('utf-8'))
            if packet.decode('utf-8').split(";")[0] == "lvl":
                if packet.decode('utf-8').split(";")[1] == "14\n":
                    print("Level 14 reached!")
                    f.write("[user." + user + ".finished]\n")
                    break
            print(packet.decode('utf-8'))


init()
selectPort()