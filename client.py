import asyncio
import time
from typing import Union, Tuple

import asyncpg

import settings as project_settings
from decoders import DecodedData
from client_actions import ClientActionFactory


async def connect_to_db():
    try:
        conn = await asyncpg.connect('postgresql://{}:{}@localhost/{}'.format(
            project_settings.DB_USER, project_settings.DB_PASSWORD, project_settings.DB_NAME))
        return conn
    except Exception as e:
        print('Unable to connect to DB')


async def run_client() -> None:
    reader, writer = await asyncio.open_connection(project_settings.SERVER_HOST, project_settings.SERVER_PORT)
    print("Client launched")
    db_connection = await connect_to_db()
    print("Connected to DB")

    while True:
        data = await reader.read(1024)
        if not data:
            print("Socket closed")
            return
        decoded_data = DecodedData(data)
        print(f"Message: {decoded_data!r}")
        if decoded_data.action:
            act_cls = ClientActionFactory.get_act(decoded_data.action)
            if act_cls:
                try:
                    result = await act_cls(reader, writer, db_connection).run(decoded_data.tokens)

                    writer.write(result.encode())
                except Exception as e:
                    print(f'Error occurred. Details:{e!r}')

        await writer.drain()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_client())
