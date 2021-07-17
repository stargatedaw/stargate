import socketserver

class MyUDPHandler(socketserver.DatagramRequestHandler):
    def handle(self):
        data = self.rfile.read().strip()
        print(f"The Message is {data}")
        # Send a message from a client
        self.wfile.write(
			"Hello UDP Client! I received a message from you!".encode()
		)

if __name__ == "__main__":
    HOST, PORT = "localhost", 9999
    # Create the server, binding to localhost on port 9999
    with socketserver.UDPServer((HOST, PORT), MyUDPHandler) as server:
        server.serve_forever()

