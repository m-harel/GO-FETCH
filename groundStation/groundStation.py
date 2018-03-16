#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ConfigParser, fcntl, io, json, os, socket, struct
try:
	import netaddr, netifaces
except ImportError, e:
	print "Failed to load packages, Please run:"
	print "sudo pip install netaddr netifaces"

CONFIG = None
MESSAGES_IN  = {"a0": {"desc":"Status - Ready to fly"},
		"a1": {"desc":"Status - Ready to start tracking ball"},
		"a2": {"desc":"Status - Ball detected, ready to grab"},
		"a3": {"desc":"Status - Ball grabbed, going home"},
		"a4": {"desc":"Status - End of mission"},
		"b0": {"desc":"Drone data - Gps location"},
		"b1": {"desc":"Drone data - Number of Satellites found"},
		"b2": {"desc":"Drone data - Height"}, 
		"b3": {"desc":"Drone data - Drone state"},
		"b4": {"desc":"Drone data - Battery state"},
		"b5": {"desc":"Drone data - Ball detection data, includes pixel and size"},
		"c0": {"desc":"Ball - First detected"},
		"c1": {"desc":"Ball - Lost"},
		"c2": {"desc":"Ball - Redetected"},
		"c3": {"desc":"Ball - Search timeout"},
		"d0": {"desc":"Error"}}
MESSAGES_OUT = {"z0": {"desc":"Do - Start mission"},
		"z1": {"desc":"Do - Take off"},
		"z2": {"desc":"Do - Start looking for the ball"},
		"z3": {"desc":"Do - Start grabbing"}, 
		"z4": {"desc":"Do - Release ball"},
		"z5": {"desc":"Do - End mission"},
		"z6": {"desc":"Do - Terminate mission"},
		"z7": {"desc":"Do - Stop mission"},
		"z8": {"desc":"Do - Send Drone data"},
		"y0": {"desc":"Settings - Set camera input"},
		"y1": {"desc":"Settings - Save camera pictures"}}

class config(object):
	cache = None
	config = None
	def __init__(self):
		self.cache = {}
		self.config = ConfigParser.RawConfigParser(allow_no_value=True)
		self.load()
	def load(self):
		with open("groundStation.ini", "rb") as infile:
			our_config = infile.read()
		self.config.readfp(io.BytesIO(our_config))
	def save(self):
		with open("groundStation.ini", "wb") as outfile:
			self.config.write(outfile)
	def get(self, section, option):
		if section in self.cache:
			if option not in self.cache[section]:
				self.cache[section][option] = self.config.get(section, option)
		else:
			self.cache[section] = {option:self.config.get(section, option)}
		return self.cache[section][option]
	def set(self, section, option, value):
		self.config.set(section, option, value)
		self.save()

def port_check(check_ip):
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.settimeout(0.5)
	return sock.connect_ex((check_ip,int(CONFIG.get("connection", "tcp_port"))))

def scan_for_drone(last_ip):
	if ((last_ip)and(last_ip != "0.0.0.0")):
		print "Checking last drone ip: {}".format(last_ip)
		if port_check(str(last_ip)) == 0:
			print "Port is open"
			return str(last_ip)
	myiface = ""
	ifaces = netifaces.interfaces()
	for tmp_interface in json.loads(CONFIG.get("connection", "interface_by_order")):
		if tmp_interface in ifaces:
			myiface = tmp_interface
			break
	if myiface != "":
		addrs = netifaces.ifaddresses(myiface)
		ipinfo = addrs[socket.AF_INET][0]
		address = ipinfo["addr"]
		netmask = ipinfo["netmask"]
		cidr = netaddr.IPNetwork("%s/%s" % (address, netmask))
		network = cidr.network
		print "Automatically selected {} interface:".format(myiface)
		print "address: {}".format(address)
		print "netmask: {}".format(netmask)
		print "   cidr: {}".format(cidr)
		print "network: {}".format(network)
	else:
		print "[ERROR] No suitable network interface found"
		return None
	for loop_ip in netaddr.IPNetwork(cidr):
		if port_check(str(loop_ip)) == 0:
			print "Port is open"
			return str(loop_ip)
		else:
			print "No answer from {}:{}".format(loop_ip,int(CONFIG.get("connection", "tcp_port")))
	return None

def main():
	global CONFIG
	CONFIG = config()
	scan_ip = None
	try:
		scan_ip = CONFIG.get("connection", "drone_last_ip")
	except:
		pass
	finally:
		scan_ip = scan_for_drone(scan_ip)
	if scan_ip:
		CONFIG.set("connection", "drone_last_ip", scan_ip)
		print scan_ip
		MESSAGE = "Hello, World!"
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((scan_ip, int(CONFIG.get("connection", "tcp_port"))))
		s.send(MESSAGE)
		data = s.recv(int(CONFIG.get("connection", "buffer_size")))
		s.close()
		print "received data:", data
	else:
		print "[ERROR] No drone found"

if __name__ == "__main__":
	if os.name == "posix":
		main()
	else:
		print "[ERROR] Invalid OS, Only linux OS is currently supported"

