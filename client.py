import asyncio
import time
import settings as project_settings

async def run_client() -> None:
    reader, writer = await asyncio.open_connection(project_settings.HOST, project_settings.PORT)
    print("Launched")
    writer.write(b"Hello world!")
    await writer.drain()

    while True:
        print('entered cycle')
        data = await reader.read()
        print("red")
        if not data:
            raise Exception("socket closed")

        print(f"Received: {data.decode()}")



if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_client())
