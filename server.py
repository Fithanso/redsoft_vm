import asyncio
import abc
import logging

import asyncpg
from aioconsole import ainput

import settings as project_settings
from actions import ActionFactory


class AsyncServer:
    def __init__(self, host=project_settings.HOST, port=project_settings.PORT):
        self.host = host
        self.port = port
        self.writer = None
        self.reader = None

    async def start(self) -> None:
        server = await asyncio.start_server(
            self.accept_connections, self.host, self.port
        )
        print('Serving on {}'.format(server.sockets[0].getsockname()))

        async with server:
            await server.serve_forever()

    async def accept_connections(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        addr = writer.get_extra_info("peername")
        logging.info(f"Connected by {addr}")

        conn = await self._connect_to_db()
        request_handler = AsyncRequestHandler(reader, writer, conn)
        await request_handler.process_input()

    async def _connect_to_db(self):
        try:
            conn = await asyncpg.connect('postgresql://{}:{}@localhost/{}'.format(
                project_settings.DB_USER, project_settings.DB_PASSWORD, project_settings.DB_NAME))
            return conn
        except Exception as e:
            print('Unable to connect to DB')


class AsyncRequestHandler:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, conn: asyncpg.connection.Connection):
        self.reader = reader
        self.writer = writer
        self.db_connection = conn

    async def process_input(self) -> None:
        try:

            while True:
                cmd = await ainput('Insert action >')
                act_cls = ActionFactory.get_act(cmd)
                data_tokens = self._get_data_tokens(cmd)
                if act_cls:
                    # try:
                    result = await act_cls(self.reader, self.writer, self.db_connection).run(data_tokens)
                    if result:
                        print(result)
                    # except Exception as e:
                    #     print(f'Error occurred. Details:{e!r}')
                else:
                    print('Unknown action: {}'.format(cmd))

                await self.writer.drain()
        except KeyboardInterrupt:
            self.writer.close()

    def _get_data_tokens(self, cmd):
        return cmd.split(' ')[1:]


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    server = AsyncServer()
    await server.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Server shut down. Good bye!')
