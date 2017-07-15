#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import sys
import time
import usb.core
import usb.util
import StringIO
import Image
import struct

def write_jpg2frame(dev, pic):
	"""Attach header to picture, pad with zeros if necessary, and send to frame"""
	# create header and stack before picture
	# middle 4 bytes have size of picture
	rawdata = b"\xa5\x5a\x18\x04" + struct.pack('<I', len(pic)) + b"\x48\x00\x00\x00" + pic
	# total transfers must be complete chunks of 16384  = 2 ^14. Complete by padding with zeros
	pad = 16384 - (len(rawdata) % 16384) +1         
	tdata = rawdata + pad * b'\x00'
	ltdata = len(tdata)
	# Syntax: write(self, endpoint, data, interface = None, timeout = None):
	endpoint = 0x02               
	dev.write(endpoint, tdata )
       

def get_known_devices():
	"""Return a dict of photo frames"""
	dList = []
	# listed as: Name, idVendor, idProduct, [width , height - in pixel if applicable]
	#
	#0,1 Samsung SPF-75H/76H (23)
	dList.append({'name':"SPF75H/76H Mini Monitor", 'idVendor':0x04e8, 'idProduct':0x200f, 'width':800, 'height':480 })
	dList.append({'name':"SPF75H/76H Mass Storage", 'idVendor':0x04e8, 'idProduct':0x200e})

	#2,3 Samsung SPF-87H (24)
	dList.append({'name':"SPF87H Mini Monitor", 'idVendor':0x04e8, 'idProduct':0x2034, 'width':800, 'height':480 })
	dList.append({'name':"SPF87H Mass Storage", 'idVendor':0x04e8, 'idProduct':0x2033})

	#4,5 Samsung SPF-87Hold (25)
	dList.append({'name':"SPF87Hold Mini Monitor", 'idVendor':0x04e8, 'idProduct':0x2026, 'width':800, 'height':480 })
	dList.append({'name':"SPF87Hold Mass Storage", 'idVendor':0x04e8, 'idProduct':0x2025})

	#6,7 Samsung SPF-83H (26)
	dList.append({'name':"SPF83H Mini Monitor", 'idVendor':0x04e8, 'idProduct':0x200d, 'width':800, 'height':600 })
	dList.append({'name':"SPF83H Mass Storage", 'idVendor':0x04e8, 'idProduct':0x200c})

	#8,9 Samsung SPF-107H (27)
	dList.append({'name':"SPF107H Mini Monitor", 'idVendor':0x04e8, 'idProduct':0x2036, 'width':1024, 'height':600 })
	dList.append({'name':"SPF107H Mass Storage", 'idVendor':0x04e8, 'idProduct':0x2035})      

	#10,11 Samsung SPF-105P (28)
	dList.append({'name':"SPF105P Mini Monitor", 'idVendor':0x04e8, 'idProduct':0x201b, 'width':1024, 'height':600 })
	dList.append({'name':"SPF105P Mass Storage", 'idVendor':0x04e8, 'idProduct':0x201c})      

	#12,13 Samsung SPF-85H/86H (29)
	dList.append({'name':"SPF85H/86H Mini Monitor", 'idVendor':0x04e8, 'idProduct':0x2013, 'width':800, 'height':600 })
	dList.append({'name':"SPF85H/86H Mass Storage", 'idVendor':0x04e8, 'idProduct':0x2012})

	#14,15 Samsung SPF-72H (210)
	dList.append({'name':"SPF72H Mini Monitor", 'idVendor':0x04e8, 'idProduct':0x200b, 'width':800, 'height':480 })
	dList.append({'name':"SPF72H Mass Storage", 'idVendor':0x04e8, 'idProduct':0x200a})

	#16,17 Samsung SPF-700T (211)
	dList.append({'name':"SPF700T Mini Monitor", 'idVendor':0x04e8, 'idProduct':0x2050, 'width':800, 'height':600 })
	dList.append({'name':"SPF700T Mass Storage", 'idVendor':0x04e8, 'idProduct':0x204f })
 
	#18,19 Samsung SPF-85P/86P (212)
	dList.append({'name':"SPF85P/86P Mini Monitor", 'idVendor':0x04e8, 'idProduct':0x2017, 'width':800, 'height':600 })
	dList.append({'name':"SPF85P/86P Mass Storage", 'idVendor':0x04e8, 'idProduct':0x2016})

	#20,21 Samsung SPF-107Hold (213)
	dList.append({'name':"SPF107Hold Mini Monitor", 'idVendor':0x04e8, 'idProduct':0x2028, 'width':1024, 'height':600 })
	dList.append({'name':"SPF107Hold Mass Storage", 'idVendor':0x04e8, 'idProduct':0x2027})      

	# Pearl DPF for Testing
	dList.append({'name':"Pearl DPF", 'idVendor':0x1908, 'idProduct':0x0102, 'width':320, 'height':240 })
	dList.append({'name':"Pearl DPF", 'idVendor':0x1908, 'idProduct':0x0102, 'width':320, 'height':240 })
       
	return dList
     

def find_device(Anzahl,device,device2):
	"""Try to find device on USB bus."""
	try:
		print "[LCD4linux] looking for frame",Anzahl, device['name'], device['idVendor'], device['idProduct'], device2['idProduct']
		if Anzahl == 2:
			d = list(usb.core.find(idVendor=device['idVendor'], idProduct=device['idProduct'], find_all=True))+list(usb.core.find(idVendor=device2['idVendor'], idProduct=device2['idProduct'], find_all=True))
			if isinstance(d,list):
				if len(d) >= 2:
					d = d[1]
				else:
					d = None
			else:
				d = None
		else:
			d = list(list(usb.core.find(idVendor=device['idVendor'], idProduct=device['idProduct'], find_all=True))+list(usb.core.find(idVendor=device2['idVendor'], idProduct=device2['idProduct'], find_all=True)))[0]
	except:
		from traceback import format_exc
		print "[LCD4linux] find exception"
		print "Error:",format_exc()
		d = None
	return d  

def init_device(Anzahl,device0, device1):
	"""First try Mini Monitor mode, then Mass storage mode"""
	dev = find_device(Anzahl,device0,device1)

	if dev is not None:
		## found it, trying to init it
		print "[LCD4linux] Find frame device",dev
		if dev.idProduct == device0["idProduct"]:
			print "[LCD4linux] init Device"
			frame_init(dev)
		else:
			print "[LCD4linux] Find frame device in Mass Storage Mode"
			frame_switch(dev)
			ts = time.time()
			while True:
				# may need to burn some time
				dev = find_device(Anzahl,device0,device1)
				if dev is not None and dev.idProduct == device0["idProduct"]:
					#switching successful
					break
				elif time.time() - ts > 3:
					print "[LCD4linux] switching failed. Ending program"
					return None
			frame_init(dev)
			print "[LCD4linux] frame device switched to Mini Monitor"
	else:
		print "[LCD4linux] Could not find frame in either mode"
		return None
	return dev

def frame_init(dev):
	"""Init device so it stays in Mini Monitor mode"""
	# this is the minimum required to keep the frame in Mini Monitor mode!!!
#	dev.ctrl_transfer(0xc0, 4 )
#	dev.ctrl_transfer(0xc0, 0x01, 0x00, 0x00, 0x09, 0x04 )
	dev.ctrl_transfer(0xc0, 0x01, 0x00, 0x00, 0x02 )

def frame_switch(dev):
	"""Switch device from Mass Storage to Mini Monitor""" 
	CTRL_TYPE_VENDOR = (2 << 5)
	CTRL_IN = 0x80
	CTRL_RECIPIENT_DEVICE = 0
	try:
		time.sleep(0.5)
		s="\x00"*251
		dev.ctrl_transfer(0x00|0x80,  0x06, 0xfe, 0xfe, 0xfe)
#		dev.ctrl_transfer(0x00|0x80,  0x06, 0xfe, 0xfe, s, 0xfe )
#		dev.ctrl_transfer(CTRL_TYPE_VENDOR | CTRL_IN | CTRL_RECIPIENT_DEVICE, 0x04, 0x00, 0x00, 1)
#		result = dev.ctrl_transfer(CTRL_TYPE_VENDOR | CTRL_IN | CTRL_RECIPIENT_DEVICE, 0x04, 0x00, 0x00, 1)
#		expect(result, [ 0x03 ])
#		result = dev.ctrl_transfer(CTRL_TYPE_VENDOR | CTRL_IN | CTRL_RECIPIENT_DEVICE, 0x01, 0x00, 0x00, 2)
#		expect(result, [ 0x09, 0x04 ])
#		result = dev.ctrl_transfer(CTRL_TYPE_VENDOR | CTRL_IN | CTRL_RECIPIENT_DEVICE, 0x02, 0x00, 0x00, 1)
#		expect(result, [ 0x46 ])
	# settling of the bus and frame takes about 0.42 sec
	# give it some extra time, but then still make sure it has settled
	except:
		print "[LCD4linux] switching ERROR"
#		from traceback import format_exc
#		print format_exc()
	finally:
		time.sleep(2)

def name(dev):
	try:
		return usb.util.get_string(dev,1) 
	except:
		try:
			return usb.util.get_string(dev,256,2) 
		except:
			return None

def main():
	global dev, known_devices_list
       
	known_devices_list = get_known_devices()

	# define which frame to use, here use Samsung SPF-87H
	device0 = known_devices_list[0] # Mini Monitor mode
	device1 = known_devices_list[1] # Mass Storage mode

	dev = init_device(device0, device1)   
	print "Frame is in Mini Monitor mode and initialized. Sending pictures now"

	image = Image.open("mypicture.jpg")
	#manipulations to consider:
	#  convert
	#  thumbnail
	#  rotate
	#  crop
	image = image.resize((800,480))
	output = StringIO.StringIO()
	image.save(output, "JPEG", quality=94)
	pic  = output.getvalue()
	output.close()
	write_jpg2frame(dev, pic)       
