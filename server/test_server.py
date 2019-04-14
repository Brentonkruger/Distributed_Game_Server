import asyncio
from http import server
from http.server import SimpleHTTPRequestHandler




def main():
        handler = SimpleHTTPRequestHandler
        a_server = server.HTTPServer(("192.168.0.10", 9998), handler)
        a_server.serve_forever


main()
