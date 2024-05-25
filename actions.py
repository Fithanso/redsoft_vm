import abc
from typing import Union
from datetime import datetime

from models import VirtualMachine, Connection
from repositories import VirtualMachineRepository, ConnectionRepository
from encryption import Crypt
from aioconsole import ainput
import settings as project_settings
import utils


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
        await VirtualMachineRepository.create(new_vm, self.db_connection)
        return 'New VM was successfully created!'


class ConnectToVMAction(Action):
    async def run(self, data_tokens):
        current_host = project_settings.HOST
        current_port = project_settings.PORT
        # при отключении клиента и сервера authorized_host у вм не сбрасывается. сбрасывается по команде выхода
        vm = await VirtualMachineRepository.get_by_host_port(data_tokens[0], int(data_tokens[1]),
                                                             self.db_connection)
        new_connection = Connection(id=None, end_dttm=None, virtual_machine_id=vm.id, connection_host=current_host,
                                    connection_port=current_port, start_dttm=datetime.now())

        if vm.authorized_host == current_host:
            async with self.db_connection.transaction():
                await self._close_old_connections(vm.id)
                await ConnectionRepository.create(new_connection, self.db_connection)
            return f'Established connection with machine #{vm.id}.'

        login = await ainput(f'Authentication required for machine #{vm.id}. Enter login >')
        password = await ainput('Enter password >')

        if login == vm.login and password == Crypt().decrypt(str(vm.password)):
            async with self.db_connection.transaction():
                await self._close_old_connections(vm.id)
                await VirtualMachineRepository.update(vm.id, {'authorized_host': current_host}, self.db_connection)
                await ConnectionRepository.create(new_connection, self.db_connection)
            return f'Successfully authenticated for VM #{vm.id}.'

        return f'Login or password are invalid.'

    async def _close_old_connections(self, vm_id):
        vm_opened_conns = await ConnectionRepository.opened_vm_connections(vm_id, self.db_connection)
        for conn in vm_opened_conns:
            await ConnectionRepository.update(conn.id, {'end_dttm': datetime.now()}, self.db_connection)


class ShowCurrentlyConnectedAction(Action):
    async def run(self, data_tokens):
        connected_vms = await VirtualMachineRepository.get_connected(self.db_connection)

        return 'Currently connected VMs: \r\n' + utils.models_to_str(connected_vms)


class ShowEverConnectedAction(Action):
    async def run(self, data_tokens):
        ever_connected_vms = await VirtualMachineRepository.get_ever_connected(self.db_connection)
        return 'Ever connected VMs: \r\n' + utils.models_to_str(ever_connected_vms)


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
        'show_connected': ShowCurrentlyConnectedAction,
        'show_ever_connected': ShowEverConnectedAction,
        'disconnect': QuitAction,
        'help': HelpAction
    }

    @classmethod
    def get_act(cls, cmd):
        tokens = cmd.split(' ')
        cmd = tokens[0]
        act_cls = cls._acts.get(cmd)
        return act_cls
