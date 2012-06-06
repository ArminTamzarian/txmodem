TXMODEM
=======

A Python class implementing the XMODEM and XMODEM-CRC send protocol built on top of [pySerial](http://pyserial.sourceforge.net/)

Class Object Usage
------------------

Usage which automatically creates and closes the serial port with each call to TXMODEM.send():
```python
from txmodem import *

try:
	TXMODEM.from_configuration(**configuration).send(filename)
except(ConfigurationException, CommunicationException) as ex:
    print "[ERROR] %s" % (ex) 
```

Usage which uses a preconfigured pySerial Serial object which leaves the object opened after each call to TXMODEM.send():
```python
from txmodem import *
from serial import *

try:
	serial_object = Serial(**configuration)
	TXMODEM.from_serial(serial_object).send(filename)
	serial_object.write("FOO")
	serial_object.close()
except(ConfigurationException, CommunicationException) as ex:
    print "[ERROR] %s" % (ex) 
```
Command Line Usage
------------------
```
python txmodem.py [OPTION]...

or

python -m txmodem.txmodem [OPTION]...

Startup:
 -?, --help    print this help
 -l, --list    list the available serial port devices
    
Configuration:
 -p, --port    specify the serial port device to use
 -b, --baud    specify the baud rate for the serial port device
 -t, --timeout specify the communication timeout in s

Transfer:
 -f, --file    specify the file that will be transfered
```