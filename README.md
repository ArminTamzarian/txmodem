TXMODEM
=======

A Python class implementing the XMODEM and XMODEM-CRC send protocol built on top of [pySerial](http://pyserial.sourceforge.net/)

Class Object Usage
------------------
```python
try:
	TXMODEM(configuration).send(filename)
except(ConfigurationException, CommunicationException) as ex:
    print "[ERROR] %s" % (ex) 
```
Command Line Usage
------------------
```
python txmodem.py [OPTION]...

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