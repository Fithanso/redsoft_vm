import asyncio
import abc


from aioconsole import ainput


import settings as project_settings

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


async def main(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:

    while True:
        cmd = await ainput('Insert Command >')
        cmd_cls, token_1, token_2 = CommandFactory.get_cmd(cmd)
        print(cmd_cls)
        if not cmd_cls:
            print('Unknown: {}'.format(cmd))
        else:
            await cmd_cls(reader, writer).run()

        await writer.drain()

    # writer.close()
    # await writer.wait_closed()

async def run_server() -> None:
    server = await asyncio.start_server(main, project_settings.HOST, project_settings.PORT)
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    async with server:
        try:
            await server.serve_forever()
        except KeyboardInterrupt:
            pass



if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_server())


    # loop = asyncio.get_event_loop()
    # # Each client connection will create a new protocol instance
    # coro = loop.create_server(Server, project_settings.HOST, project_settings.PORT)
    # server = loop.run_until_complete(coro)
    # loop.run_until_complete(main(server))
    #
    # # Serve requests until Ctrl+C is pressed
    # print('Serving on {}'.format(server.sockets[0].getsockname()))
    # try:
    #     loop.run_forever()
    # except KeyboardInterrupt:
    #     pass
    #
    # # Close the server
    # server.close()
    # loop.run_until_complete(server.wait_closed())
    # loop.close()