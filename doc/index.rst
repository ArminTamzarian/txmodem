===========
TXMODEM API
===========

:Release: |version|
:Date: |today|

A Python class implementing the XMODEM and XMODEM-CRC send protocol built on top of `pySerial <http://pyserial.sourceforge.net/>`_.

.. toctree::
   :maxdepth: 2

.. automodule:: txmodem

Classes
-------

.. autoclass:: TXMODEM
    :exclude-members: EVENT_INITIALIZATION, EVENT_BLOCK_SENT, EVENT_TERMIATION
    :members:
    

Constants
---------

.. autoattribute:: TXMODEM.EVENT_INITIALIZATION
.. autoattribute:: TXMODEM.EVENT_BLOCK_SENT
.. autoattribute:: TXMODEM.EVENT_TERMIATION

Exceptions
----------

.. autoexception:: ConfigurationException

.. autoexception:: CommunicationException

Main Class
----------

.. autoclass:: Main
    :members:

=======
License
=======

TXMODEM is free software distributed under the terms of the `MIT license <http://www.opensource.org/licenses/mit-license.html>`_ reproduced below. TXMODEM may be used for any purpose, including commercial purposes, at absolutely no cost.::

	Copyright (c) 2012 Armin Tamzarian
		
	Permission is hereby granted, free of charge, to any person obtaining a copy
	of this software and associated documentation files (the "Software"), to deal
	in the Software without restriction, including without limitation the rights
	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
	copies of the Software, and to permit persons to whom the Software is
	furnished to do so, subject to the following conditions:
	   
	The above copyright notice and this permission notice shall be included in
	all copies or substantial portions of the Software.
		
	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
	THE SOFTWARE.
