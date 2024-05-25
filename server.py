import asyncio
import abc
import logging

from aioconsole import ainput

import settings as project_settings

class AsyncServer:
    def __init__(self, host = project_settings.HOST, port = project_settings.PORT):
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


    async def accept_connections(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        addr = writer.get_extra_info("peername")
        logging.info(f"Connected by {addr}")
        request_handler = AsyncRequestHandler(reader, writer)
        await request_handler.process_request()


class Command(metaclass=abc.ABCMeta):
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer

    @abc.abstractmethod
    async def run(self, a, b):
        raise NotImplementedError()


class XCommand(Command):
    async def run(self, param1=None, param2=None):
        self.writer.write(b'Command X')


class YCommand(Command):
    async def run(self, param1=None, param2=None):
        self.writer.write(b'Command Y')


class QuitCommand(Command):
    async def run(self, param1=None, param2=None):
        self.writer.write(b'Disconnected...')


class CommandFactory:
    _cmds = {'X': XCommand,
         'Y': YCommand,
         'DISCONNECT': QuitCommand}

    @classmethod
    def get_cmd(cls, cmd):
        tokens = cmd.split(':')
        cmd = tokens[0]
        if len(tokens) == 1:
            nome, numero = None, None
        else:
            nome, numero = (tokens[1], tokens[2]) if len(tokens) == 3 else (tokens[1], None)
        cmd_cls = cls._cmds.get(cmd)
        return cmd_cls, nome, numero


class AsyncRequestHandler:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer

    async def process_request(self) -> None:
        try:

            while True:
                cmd = await ainput('Insert Command >')
                cmd_cls, token_1, token_2 = CommandFactory.get_cmd(cmd)
                print(cmd_cls)
                if not cmd_cls:
                    print('Unknown: {}'.format(cmd))
                else:
                    await cmd_cls(self.reader, self.writer).run()

                await self.writer.drain()
        except KeyboardInterrupt:
            self.writer.close()


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    server = AsyncServer()
    await server.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Server shut down. Good bye!')
