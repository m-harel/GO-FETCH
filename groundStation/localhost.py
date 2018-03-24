import time, struct, socket, hashlib, base64, sys, re, logging, signal
from select import select
from threading import Thread

# Constants
MAGICGUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
TEXT = 0x01
BINARY = 0x02

class WebSocket(object): # WebSocket implementation
	handshake = (
		"HTTP/1.1 101 Web Socket Protocol Handshake\r\n"
		"Upgrade: WebSocket\r\n"
		"Connection: Upgrade\r\n"
		"Sec-WebSocket-Accept: %(acceptstring)s\r\n"
		"Server: TestTest\r\n"
		"Access-Control-Allow-Origin: http://localhost\r\n"
		"Access-Control-Allow-Credentials: true\r\n"
		"\r\n"
	)

	def __init__(self, client, server): # Constructor
		self.client = client
		self.server = server
		self.handshaken = False
		self.header = ""
		self.data = ""

	def feed(self, data): # Serve this client
		if not self.handshaken: # If we haven't handshaken yet
			logging.debug("No handshake yet")
			self.header += data
			if self.header.find('\r\n\r\n') != -1:
				parts = self.header.split('\r\n\r\n', 1)
				self.header = parts[0]
				if self.dohandshake(self.header, parts[1]):
					logging.info("Handshake successful")
					self.handshaken = True
		else: # We have handshaken
			logging.debug("Handshake is complete")
			recv = self.decodeCharArray(data) # Decode the data that we received according to section 5 of RFC6455
			recv = ''.join(recv).strip()
			if len(recv) > 0:
				if recv == "register":
					return 1
				else:
					self.sendMessage(recv); # Send our reply
					return 0

	def sendMessage(self, s): # Encode and send a WebSocket message
		message = "" # Empty message to start with
		b1 = 0x80 # always send an entire message as one frame (fin)
		if type(s) == unicode: # in Python 2, strs are bytes and unicodes are strings
			b1 |= TEXT
			payload = s.encode("UTF8")
		elif type(s) == str:
			b1 |= TEXT
			payload = s
		message += chr(b1) # Append 'FIN' flag to the message
		b2 = 0 # never mask frames from the server to the client
		length = len(payload) # How long is our payload?
		if length < 126:
			b2 |= length
			message += chr(b2)
		elif length < (2 ** 16) - 1:
			b2 |= 126
			message += chr(b2)
			l = struct.pack(">H", length)
			message += l
		else:
			l = struct.pack(">Q", length)
			b2 |= 127
			message += chr(b2)
			message += l
		message += payload # Append payload to message
		self.client.send(str(message)) # Send to the client

	def decodeCharArray(self, stringStreamIn):
		byteArray = [ord(character) for character in stringStreamIn] # Turn string values into opererable numeric byte values
		datalength = byteArray[1] & 127
		indexFirstMask = 2
		if datalength == 126:
			indexFirstMask = 4
		elif datalength == 127:
			indexFirstMask = 10
		masks = [m for m in byteArray[indexFirstMask : indexFirstMask+4]] # Extract masks
		indexFirstDataByte = indexFirstMask + 4
		decodedChars = [] # List of decoded characters
		i = indexFirstDataByte
		j = 0
		while i < len(byteArray): # Loop through each byte that was received
			decodedChars.append( chr(byteArray[i] ^ masks[j % 4]) ) # Unmask this byte and add to the decoded buffer
			i += 1
			j += 1
		return decodedChars # Return the decoded string

	def dohandshake(self, header, key=None): # Handshake with this client
		logging.debug("Begin handshake: %s" % header)
		handshake = self.handshake # Get the handshake template
		for line in header.split('\r\n')[1:]: # Step through each header
			name, value = line.split(': ', 1)
			if name.lower() == "sec-websocket-key": # If this is the key
				combined = value + MAGICGUID # Append the standard GUID and get digest
				response = base64.b64encode(hashlib.sha1(combined).digest())
				handshake = handshake % { 'acceptstring' : response } # Replace the placeholder in the handshake response
		logging.debug("Sending handshake %s" % handshake)
		self.client.send(handshake)
		return True

	def onmessage(self, data):
		logging.info("Got message: %s" % data)
		self.send(data)

	def send(self, data):
		logging.info("Sent message: %s" % data)
		self.client.send("\x00%s\xff" % data)

	def close(self):
		self.client.close()

class WebSocketServer(object): # WebSocket server implementation
	def __init__(self, bind, port, cls): # Constructor
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.socket.bind((bind, port))
		self.bind = bind
		self.port = port
		self.cls = cls
		self.connections = {}
		self.registered = []
		self.listeners = [self.socket]

	def listen(self, backlog=5): # Listen for requests
		self.socket.listen(backlog)
		logging.info("Listening on %s" % self.port)
		self.running = True # Keep serving requests
		while self.running:
			rList, wList, xList = select(self.listeners, [], self.listeners, 1) # Find clients that need servicing
			for ready in rList:
				if ready == self.socket:
					logging.debug("New client connection")
					client, address = self.socket.accept()
					fileno = client.fileno()
					self.listeners.append(fileno)
					self.connections[fileno] = self.cls(client, self)
				else:
					logging.debug("Client ready for reading %s" % ready)
					client = self.connections[ready].client
					try:
						data = client.recv(4096)
					except socket.error, e:
						logging.error("Connection error: %s" % e)
						data = None
					fileno = client.fileno()
					if data:
						if self.connections[fileno].feed(data) == 1:
							self.registered.append(ready)
					else:
						logging.debug("Closing client %s" % ready)
						self.connections[fileno].close()
						del self.connections[fileno]
						if ready in self.registered:
							del self.registered[ready]
						self.listeners.remove(ready)
			for failed in xList: # Step though and delete broken connections
				if failed == self.socket:
					logging.error("Socket broke")
					for fileno, conn in self.connections:
						conn.close()
					self.running = False
			for activeWS in self.registered:
				try:
					self.connections[activeWS].sendMessage("Keep alive")
				except:
					logging.debug("Skip keepalive to %s" % activeWS)

if __name__ == "__main__":
	logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
	server = WebSocketServer("127.1.2.0", 7120, WebSocket)
	server_thread = Thread(target=server.listen, args=[5])
	server_thread.start()
	def signal_handler(signal, frame): # Add SIGINT handler for killing the threads
		logging.info("Caught Ctrl+C, shutting down...")
		server.running = False
		sys.exit()
	signal.signal(signal.SIGINT, signal_handler)
	while True:
		time.sleep(100)
