import asyncio
import abc


from aioconsole import ainput


import settings as project_settings

class Command(metaclass=abc.ABCMeta):
    def __init__(self, server):
        self.server = server

    @abc.abstractmethod
    def run(self, a, b):
        raise NotImplementedError()


class XCommand(Command):
    def run(self, param1=None, param2=None):
        self.server.send_message('Command X')


class YCommand(Command):
    def run(self, db, param1=None, param2=None):
        self.server.send_message('Command Y')


class QuitCommand(Command):
    def run(self, param1=None, param2=None):
        self.server.send_message('Disconnected...')

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

class Server(asyncio.Protocol):

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        print(transport)
        print(type(transport))
        self.transport = transport

    def send_message(self, message):
        self.transport.write(bytes(message, encoding='UTF-8'))

    # def data_received(self, data):
    #     message = data.decode()
    #     print('Data received: {!r}'.format(message))
    #     cmd_cls, param1, param2 = CommandFactory.get_cmd(message)
    #     res = cmd_cls.run(param1, param2)
    #     print('Sending response: {!r}'.format(res))
    #     self.transport.write(bytes(res, encoding='UTF-8'))


async def main(server):
    while True:
        cmd = await ainput('Insert Command >')
        cmd_cls, token_1, token_2 = CommandFactory.get_cmd(cmd)
        print(cmd_cls)
        if not cmd_cls:
            print('Unknown: {}'.format(cmd))
        else:
            cmd_cls(server).run()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    # Each client connection will create a new protocol instance
    coro = loop.create_server(Server, project_settings.HOST, project_settings.PORT)
    server = loop.run_until_complete(coro)
    loop.run_until_complete(main(server))

    # Serve requests until Ctrl+C is pressed
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Close the server
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()