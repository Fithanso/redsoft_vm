import abc
from typing import Union

from models import VirtualMachine
from repositories import VirtualMachineRepository
from encryption import Crypt
from aioconsole import ainput


class Action(metaclass=abc.ABCMeta):
    def __init__(self, reader, writer, db_connection):
        self.reader = reader
        self.writer = writer
        self.db_connection = db_connection

    @abc.abstractmethod
    async def run(self, data_tokens) -> Union[str, None]:
        raise NotImplementedError()


class AddVMAction(Action):
    async def run(self, data_tokens):

        new_vm = VirtualMachine(id=None, ram_amount=data_tokens[0], dedicated_cpu=data_tokens[1], host=data_tokens[2],
                                port=data_tokens[3], login=data_tokens[4], password=Crypt().encrypt(data_tokens[5]),
                                authorized_host=None)
        await VirtualMachineRepository.create_vm(new_vm, self.db_connection)
        return 'New VM was successfully created!'


class ConnectToVMAction(Action):
    async def run(self, data_tokens):
        # искать по host, port -> pydantic. если ее логин и пароль не совп, то ошибка. а иначе создаем объект connection
        # при отключении клиента и сервера authorized_host у вм не сбрасывается. сбрасывается по команде выхода
        row = await VirtualMachineRepository.get_vm_by_host_port(data_tokens[0], int(data_tokens[1]),
                                                                 self.db_connection)
        vm = VirtualMachine(**dict(row))
        cmd = await ainput('VM found on requested host and port. Specify login and password >')
        print(cmd)
        return f'Established connection with machine #{vm.id}.'


class QuitAction(Action):
    async def run(self, data_tokens):
        self.writer.write(b'Disconnected...')


class HelpAction(Action):
    async def run(self, data_tokens):
        print('Help')


class ActionFactory:
    _acts = {
        'add_vm': AddVMAction,
        'connect_to_vm': ConnectToVMAction,
        'disconnect': QuitAction,
        'help': HelpAction
    }

    @classmethod
    def get_act(cls, cmd):
        tokens = cmd.split(' ')
        cmd = tokens[0]
        act_cls = cls._acts.get(cmd)
        return act_cls
