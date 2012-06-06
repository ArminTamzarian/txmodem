#!/usr/bin/env python
#
# A Python class implementing the XMODEM and XMODEM-CRC send protocol.
#
# (C) 2012 Armin Tamzarian
# This software is distributed under a free software license, see LICENSE

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
    A Python class implementing the XMODEM and XMODEM-CRC send protocol built on top of `pySerial <http://pyserial.sourceforge.net/>`_.
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
    
    def __init__(self, **configuration):
        """
        TXMODEM constructor.
        
        :param configuration: Configuration dictionary for the serial port as defined in the `pySerial API <http://pyserial.sourceforge.net/pyserial_api.html>`_.
        """
        if configuration is not None:
            self.set_configuration(**configuration)
        
    def set_configuration(self, **configuration):
        """
        Set the configuration for the serial device.
        
        :param configuration: Configuration dictionary for the serial port as defined in the `pySerial API <http://pyserial.sourceforge.net/pyserial_api.html>`_.
        """
        for k, v in configuration.items():
            self._configuration[k] = v
        
    def send(self, filename):
        """
        Execute the transmission of the file.
        
        :param filename: Filename of the file to transfer.
        
        :raises ConfigurationException: Will be raised in the event of an invalid file or port configuration parameter.
        :raises CommunicationException: Will be raised in the event of an unrecoverable serial communication error.
        """
        
        # Ensure proper preflight configuration
        if filename is None:
            raise ConfigurationException("No filename specified.")
        
        if self._configuration is None or self._configuration["port"] is None:
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
        Sets the _checksum calculation to _crc_8 for compatibility with _wait_for_signal.
        
        :param buffer: Exists for compatibility. Ignored.
        """
        self._checksum = self._crc_8
    
    def _set_crc_16(self, buffer):
        """
        Sets the _checksum calculation to _crc_16 for compatibility with _wait_for_signal.
        
        :param buffer: Exists for compatibility. Ignored.
        """
        self._checksum = self._crc_16
        
    def _crc_8(self, block):
        """
        Calculates the 8-bit CRC checksum as defined by the original XMODEM specification.
        
        :param block: The block for which the checksum will be calculated.
        """
        return chr(sum(map(ord, block)) & 0xFF)
    
    def _crc_16(self, block):
        """
        Calculates the 8-bit CRC checksum as defined by the original XMODEM-CRC specification.
        
        :param block: The block for which the checksum will be calculated.
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
        Waits for a signal to be received and executes a specified callback function.
        
        :param signals: A dictionary with expected signals for keys and callback functions for values of the signature *function(buffer)*. 
        """
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
        Abstract function to execute communication methods within the XMODEM error correction framework.
        
        :param communication_function: Communication function to execute within the error correction framework.
        :param failure_message: Failure message to raise along with the exception if applicable.
        :param args: Arguments to pass to the supplied communication_function.
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
        Initiates the transmission while automatically selecting between XMODEM and XMODEM-CRC modes.
        """
        try:
            self._wait_for_signal({
                 self._SIGNAL_NAK : self._crc_8,
                 self._SIGNAL_CRC16 : self._crc_16
            })
        except UnexpectedSignalException as ex:
            raise CommunicationException("Unknown initiation signal received.")    
    
    def _transmit_block(self, block_index, block):
        """
        Transmits the specified block of data.
        
        :param block_index: Index of the block to be transmitted.
        :param block: Buffered block of data to be transmitted.
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
        Terminates the XMODEM transmission.
        """
        self._port.write(self._SIGNAL_EOT)
        self._port.flush()
        
        self._wait_for_signal({self._SIGNAL_ACK: None})
        self._port.flush()
        
class Main:
    """
    A Python Main-style class for command line execution of the TXMODEM functionality.
    
    :Example:
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
        Lists the accessible serial devices and their associated system names.
        """
        print "Currently available ports:"
        print "--------------------------"
        for port in list_ports.comports():
            print "  %s" % (port[0])    
    
    def _usage(self):
        """
        Prints the usage information for command line execution.
        """
        print '''\
    XMODEM transfer utility
    
    Usage: python txmodem.py [OPTION]...'''
    
    def _help(self): 
        """
        Prints the usage and help information for command line execution.
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
        Main function to initiate execution of the class.
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