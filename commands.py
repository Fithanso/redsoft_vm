import abc
from typing import Union

from models import VirtualMachine
from repositories import VirtualMachineRepository
from encryption import Crypt


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
                                port=data_tokens[3], login=data_tokens[4], password=Crypt().encrypt(data_tokens[5]),
                                authorized_host=None)
        await VirtualMachineRepository.create_vm(new_vm, self.db_connection)
        return 'New VM was successfully created!'


class ConnectToVMCommand(Command):
    async def run(self, data_tokens):
        # искать по host, port -> pydantic. если ее логин и пароль не совп, то ошибка. а иначе создаем объект connection
        # при отключении клиента и сервера authorized_host у вм не сбрасывается. сбрасывается по команде выхода
        row = await VirtualMachineRepository.get_vm_by_host_port(data_tokens[0], int(data_tokens[1]),
                                                                 self.db_connection)
        vm = VirtualMachine(**dict(row))

        return f'Established connection with machine #{vm.id}.'


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
