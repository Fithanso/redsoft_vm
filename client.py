import asyncio
import time
import settings as project_settings

async def run_client() -> None:
    reader, writer = await asyncio.open_connection(project_settings.HOST, project_settings.PORT)

    writer.write(b"Hello world!")
    await writer.drain()

    messages = 10

    while True:
        data = await reader.read(1024)

        if not data:
            raise Exception("socket closed")

        print(f"Received: {data.decode()}")

        if messages > 0:
            await asyncio.sleep(1)
            writer.write(f"{time.time()}".encode())
            await writer.drain()
            messages -= 1
        else:
            writer.write(b"quit")
            await writer.drain()
            break


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(run_client())
