#! /usr/bin/python

# Copyright (c) 2012 Armin Tamzarian
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

#
# XMODEM file transfer utility
#
# Revision History:
# -----------------
# 1.0 - Initial release

__version__ = "1.0"
__license__ = "MIT"

import getopt
import math
import os
import re
import sys

from serial import *
from serial.tools import list_ports

class ExceptionTXMODEM(Exception):
    """ Base exception class for the TXMODEM class. """
    pass

class ConfigurationException(ExceptionTXMODEM):
    """ TXMODEM configuration exception. """
    pass

class CommunicationException(ExceptionTXMODEM):
    """ Unrecoverable TXMODEM communication exception. """
    pass

class TimeoutException(ExceptionTXMODEM):
    """ Possibly recoverable TXMODEM timeout exception. """
    pass

class UnexpectedSignalException(ExceptionTXMODEM):
    """ Unexpected communication response exception. """
    _signal = None;
    
    def __init__(self, message, signal):
        Exception.__init__(self, message)
        self._signal = signal
    
    def get_signal(self):
        return self._signal

class TXMODEM:
    """
    A Python class implementing the XMODEM and XMODEM-CRC send protocol built on top of PySerial.
    """
    
    _SIGNAL_SOH = chr(1)
    _SIGNAL_EOT = chr(4)
    _SIGNAL_ACK = chr(6)
    _SIGNAL_NAK = chr(21)
    _SIGNAL_CAN = chr(24)
    _SIGNAL_CRC16 = chr(67)
    
    _BLOCK_SIZE = 128
    _RETRY_COUNT = 10
    
    # default port configurations
    _configuration = {
                     "port" : None,
                     "baudrate" : 115200,
                     "bytesize" : EIGHTBITS,
                     "parity" : PARITY_NONE,
                     "stopbits" : STOPBITS_ONE,
                     "timeout" : 10
                     }

    _port = None
    _checksum = None
    
    _callback_update = None
    
    def __init__(self, **configuration):
        """
        """
        self.set_configuration(**configuration)
        
    def set_configuration(self, **configuration):
        """
        """
        for k, v in configuration.items():
            self._configuration[k] = v
        
    def send(self, filename):
        """
        """
        
        # Ensure proper preflight configuration
        if filename is None:
            raise ConfigurationException("No filename specified.")
        
        if self._configuration["port"] is None:
            raise ConfigurationException("No serial port device specified.")
        
        # Open access to the input file
        input_file = None
        try:
            input_file = open(filename, "rb") 
        except IOError:
            raise ConfigurationException("Unable to access input filename '%s'." % (filename))
        
        # Open access to the serial device
        try:
            self._port = Serial(**self._configuration)
        except ValueError:
            raise ConfigurationException("Invalid value for configuration parameters.")
        except SerialException:
            raise ConfigurationException("Unable to open serial device '%s' with specified parameters." % (configuration["port"]))

        try:            
            self._port.flush()
            self._execute_communication(self._initiate_transmission, "Unable to receive initial NAK.")            

            for i in range(1,  int(math.ceil(os.path.getsize(filename) / self._BLOCK_SIZE)) + 1):
                block = input_file.read(self._BLOCK_SIZE)
                if block:
                    if len(block) < self._BLOCK_SIZE:
                        block += chr(0) * (self._BLOCK_SIZE - len(block))
                    self._execute_communication(self._transmit_block, "Maximum number of transmission retries exceeded.", **{"block_index": i, "block": block})            
                    
            self._execute_communication(self._terminate_transmission, "Maximum number of termination retries exceeded.")
        except IOError:
            raise CommunicationException("Unexpected IO error.")
        finally:
            # Always remember to clean up after yourself
            input_file.close()
            
            if self._port is not None and self._port.isOpen():
                self._port.close()
                  
    def _set_crc_8(self, buffer):
        """
        """
        self._checksum = self._crc_8
    
    def _set_crc_16(self, buffer):
        """
        """
        self._checksum = self._crc_16
        
    def _crc_8(self, block):
        """
        """
        return chr(sum(map(ord, block)) & 0xFF)
    
    def _crc_16(self, block):
        """
        """
        crc = 0
        for b in block:
            crc = crc ^ (ord(b) << 8)
            for i in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = crc << 1
        return "%c%c" % ((crc >> 8) & 0xFF, crc & 0xFF)
             
    def _wait_for_signal(self, signals):
        """
        """
        while True:
            buffer = self._port.read()
            while self._port.inWaiting():
                buffer += self._port.read()
            self._port.flush()
            
            if len(buffer) == 0:
                raise TimeoutException("Communication timeout expired.")
            elif buffer[0] in signals and signals[buffer[0]] is not None:
                signals[buffer[0]](buffer)
            else:
                raise UnexpectedSignalException("Unexpected communication signal received.", buffer)

    def _execute_communication(self, communication_function, failure_message, **args):
        """
        """
        for retry in range(self._RETRY_COUNT):
            try:
                communication_function(**args)
                return
            except UnexpectedSignalException as ex:
                if self._SIGNAL_CAN in ex.get_signal():
                    raise CommunicationException("CAN signal received. Transmission forcefully terminated by receiver.")
            except (TimeoutException, SerialException):
                pass
            
        raise CommunicationException(failure_message)
            
    def _initiate_transmission(self):
        """
        """
        try:
            self._wait_for_signal({
                 self._SIGNAL_NAK : self._crc_8,
                 self._SIGNAL_CRC16 : self._crc_16
            })
            self._checksum = self._crc_8
        except UnexpectedSignalException as ex:
            if self._SIGNAL_CRC16 in ex.get_signal():
                self._checksum = self._crc_16
            else:
                raise CommunicationException("Unknown initiation signal received.")    
    
    def _transmit_block(self, block_index, block):
        """
        """
        try:
            self._port.write("%c%c%c%s%s" % (self._SIGNAL_SOH, chr(block_index & 0xFF), chr(~block_index & 0xFF), block, self._checksum(block)))
            self._port.flush()
            self._wait_for_signal({self._SIGNAL_ACK: None})
            return
        except UnexpectedSignalException as ex:
            if self._SIGNAL_CAN in ex.get_signal():
                raise CommunicationException("CAN signal received. Transmission forcefully terminated by receiver.")
        except (TimeoutException, SerialException):
            pass
            
    def _terminate_transmission(self):
        """
        """
        self._port.write(self._SIGNAL_EOT)
        self._port.flush()
        
        self._wait_for_signal({self._SIGNAL_ACK: None})
        self._port.flush()
        
class Main:
    """
    A Python Main-style class for command line execution of the TXMODEM functionality.
    
    :Example
    ``python txmodem.py --file [filename] --port [port]``
    """

    _EXIT_OK = 0
    _EXIT_ERROR = 1
    
    # default port configurations
    _configuration = {
                     "port" : None,
                     "baudrate" : 115200,
                     "bytesize" : EIGHTBITS,
                     "parity" : PARITY_NONE,
                     "stopbits" : STOPBITS_ONE,
                     "timeout" : 10
                     }
    
    _tx_filename = None
        
    def _list_ports(self):
        """
        """
        print "Currently available ports:"
        print "--------------------------"
        for port in list_ports.comports():
            print "  %s" % (port[0])    
    
    def _usage(self):
        """
        """
        print '''\
    XMODEM transfer utility
    
    Usage: txmodem.py [OPTION]...'''
    
    def _help(self): 
        """
        """
        self._usage()
        
        print '''
    Startup:
      -?, --help    print this help
      -l, --list    list the available serial port devices
    
    Configuration:
      -p, --port    specify the serial port device to use
      -b, --baud    specify the baud rate for the serial port device
      -t, --timeout specify the communication timeout in s

    Transfer:
      -f, --file    specify the file that will be transfered
     '''
                    
    def run(self):
        """
        """
        # scan arguments for options    
        try:
            opts, args = getopt.getopt(sys.argv[1:], "?lp:b:t:f:", ["help", "list", "port=", "baud=", "timeout=", "file="])
        except getopt.GetoptError, err:
            print str(err)
            return self._EXIT_ERROR
        
        # initial argument scan for execution terminators
        for o, a in opts:
            if o in ("-?", "--help"):
                self._help()
                return self._EXIT_OK
            elif o in ("-l", "--list"):
                self._list_ports()
                return self._EXIT_OK
            
        # argument scan to extract configuration items
        for o, a in opts:
            if o in ("-p", "--port"):
                self._configuration["port"] = a;
            elif o in ("-b", "--baud"):
                try:
                    self._configuration["baudrate"] = int(a)
                except ValueError:
                    print "[ERROR] Invalid baud rate '%s' specified." % (a)
                    return self._EXIT_ERROR 
            elif o in ("-t", "--timeout"):
                try:
                    self._configuration["timeout"] = int(a)
                except ValueError:
                    print "[ERROR] Invalid timeout '%s' specified." % (a)
                    return self._EXIT_ERROR 
            elif o in ("-f", "--file"):
                self._tx_filename = a
                
        try:
            TXMODEM(**self._configuration).send(self._tx_filename)
        except(ConfigurationException, CommunicationException) as ex:
            print "[ERROR] %s" %(ex)        
        except(KeyboardInterrupt, SystemExit):
            print "[INFO] Exit command detected."
        
        return self._EXIT_OK

if __name__ == "__main__":
    sys.exit(Main().run())