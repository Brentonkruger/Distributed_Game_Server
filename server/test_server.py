import asyncio
from http import server
from http.server import SimpleHTTPRequestHandler


# async def parse_message(reader, writer):
#         msg = await reader.read()
#         #parse the message (json) and call the corresponding method to deal with it.
#         print(msg.decode())



def main():
        handler = SimpleHTTPRequestHandler
        a_server = server.HTTPServer(("192.168.0.10", 9998), handler)
        a_server.serve_forever

        
#     a_server = await asyncio.start_server(parse_message, port=9998)

#     async with a_server:
#         await a_server.serve_forever()

# asyncio.run(main())
main()
