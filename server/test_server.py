import asyncio


async def parse_message(reader, writer):
        msg = await reader.read()
        #parse the message (json) and call the corresponding method to deal with it.
        print(msg.decode())

async def main():
    a_server = await asyncio.start_server(parse_message, port=9998)

    async with a_server:
        await a_server.serve_forever()

asyncio.run(main())
