TXMODEM
=======

A Python class implementing the XMODEM and XMODEM-CRC send protocol built on top of [pySerial](http://pyserial.sourceforge.net/)

Installation
------------
Simply ensure the txmodem.py file is in your PATH or install the module by executing:
```
python setup.py install
```

Class Object Usage
------------------
Usage which automatically creates and closes the serial port with each call to TXMODEM.send():
```python
from txmodem import *

try:
    configuration = {
        "port" : "/dev/tty.PL2303-000013FA",
        "baudrate" : 115200,
        "bytesize" : EIGHTBITS,
        "parity" : PARITY_NONE,
        "stopbits" : STOPBITS_ONE,
        "timeout" : 10
    }
    
	TXMODEM.from_configuration(**configuration).send(filename)
except(ConfigurationException, CommunicationException) as ex:
    print "[ERROR] %s" % (ex) 
```

Usage which uses a preconfigured pySerial Serial object which defers management and further usage of said object:
```python
from txmodem import *
from serial import *

try:
    configuration = {
        "port" : "/dev/tty.PL2303-000013FA",
        "baudrate" : 115200,
        "bytesize" : EIGHTBITS,
        "parity" : PARITY_NONE,
        "stopbits" : STOPBITS_ONE,
        "timeout" : 10
    }
    
	serial_object = Serial(**configuration)
	TXMODEM.from_serial(serial_object).send(filename)
	serial_object.write("FOO")
	serial_object.close()
except(ConfigurationException, CommunicationException) as ex:
    print "[ERROR] %s" % (ex) 
```
Command Line Usage
------------------
Ensure the txmodem.py file is executable and enter:
```
python txmodem.py [OPTION]...
```
Alternately if the module has been installed you can execute the main functionality by entering:
```
python -m txmodem.txmodem [OPTION]...
```
Command Line Options
--------------------
```
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