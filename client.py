import asyncio
import time
import settings as project_settings

async def run_client() -> None:
    reader, writer = await asyncio.open_connection(project_settings.HOST, project_settings.PORT)
    print("Launched")

    while True:
        data = await reader.read(1024)
        if not data:
            print("Socket closed")
            return

        print(f"Received: {data.decode()!r}")



if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_client())
