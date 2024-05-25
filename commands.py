import abc
from typing import Union

from models import VirtualMachine
from repositories import VirtualMachineRepository


class Command(metaclass=abc.ABCMeta):
    def __init__(self, reader, writer, db_connection):
        self.reader = reader
        self.writer = writer
        self.db_connection = db_connection

    @abc.abstractmethod
    async def run(self, data_tokens) -> Union[str, None]:
        raise NotImplementedError()


class AddVMCommand(Command):
    async def run(self, data_tokens):
        new_vm = VirtualMachine(id=None, ram_amount=data_tokens[0], dedicated_cpu=data_tokens[1], host=data_tokens[2],
                                port=data_tokens[3], login=data_tokens[4], password=data_tokens[5])
        await VirtualMachineRepository.create_vm(new_vm, self.db_connection)
        return 'New VM was successfully created!'


class ConnectToVMCommand(Command):
    async def run(self, data_tokens):
        # искать по id -> pydantic. если ее логи и пароль не совп, то ошибка. а иначе создаем объект connection

        return 'Established connection with machine #{}.'


class QuitCommand(Command):
    async def run(self, data_tokens):
        self.writer.write(b'Disconnected...')


class HelpCommand(Command):
    async def run(self, data_tokens):
        print('Help')


class CommandFactory:
    _cmds = {
        'add_vm': AddVMCommand,
        'connect_to_vm': ConnectToVMCommand,
        'disconnect': QuitCommand,
        'help': HelpCommand
    }

    @classmethod
    def get_cmd(cls, cmd):
        tokens = cmd.split(' ')
        cmd = tokens[0]
        cmd_cls = cls._cmds.get(cmd)
        return cmd_cls
