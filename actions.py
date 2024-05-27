import abc
from typing import Union
from datetime import datetime

from models import VirtualMachineInput, Connection
from repositories import VirtualMachineRepository, ConnectionRepository, HardDriveRepository
from encryption import Crypt
from aioconsole import ainput
import settings as project_settings
import utils


# TODO: перенести аутентификацию на сторону клиента


class Action(metaclass=abc.ABCMeta):
    def __init__(self, reader, writer, db_connection):
        self.reader = reader
        self.writer = writer
        self.db_connection = db_connection

    @abc.abstractmethod
    async def run(self, data_tokens) -> Union[str, None]:
        raise NotImplementedError()


class AddVMAction(Action):
    async def run(self, data_tokens) -> Union[str, None]:

        validated_data = await self._validate_dto(data_tokens)

        await VirtualMachineRepository.create(validated_data, self.db_connection)
        return 'New VM was successfully created!'

    async def _validate_dto(self, update_data) -> VirtualMachineInput:
        data_dict = {}
        update_data = {field_value.split(':')[0]: field_value.split(':')[1] for field_value in update_data}
        for field_name, value in update_data.items():
            if field_name == 'password':
                value = Crypt().encrypt(value)
            data_dict[field_name] = value
        return VirtualMachineInput(**data_dict)


class ConnectToVMAction(Action):
    async def run(self, data_tokens) -> str:
        current_host = project_settings.HOST
        current_port = project_settings.PORT
        # при отключении клиента и сервера authorized_host у вм не сбрасывается. сбрасывается по команде выхода
        vm = await VirtualMachineRepository.get({'host': data_tokens[0], 'port': int(data_tokens[1])},
                                                self.db_connection)
        vm = vm[0]
        await ConnectionRepository.open_connection(current_host, current_port, vm, self.db_connection)

        if await VirtualMachineRepository.is_authorized(current_host, vm):
            return f'Already authenticated. Established connection with machine #{vm.id}.'

        login = await ainput(f'Authentication required for machine #{vm.id}. Enter login >')
        password = await ainput('Enter password >')

        if await VirtualMachineRepository.authenticate(login, password, vm):
            await VirtualMachineRepository.authorize(current_host, vm, self.db_connection)

            self.writer.write(f'secret:mecret|||Host {current_host} has established connection.'.encode())
            await self.writer.drain()
            msg = await self.reader.read(1024)
            return f'Successfully authenticated for VM {vm.host}:{vm.port}. {msg}'

        await ConnectionRepository.close_vm_connections(vm.id, self.db_connection)
        return f'Login or password are invalid. Connection closed.'


class ShowCurrentlyConnectedAction(Action):
    async def run(self, data_tokens) -> Union[str, None]:
        connected_vms = await VirtualMachineRepository.get_connected(self.db_connection)

        return 'Currently connected VMs: \r\n' + utils.models_to_str(connected_vms)


class ShowEverConnectedAction(Action):
    async def run(self, data_tokens) -> Union[str, None]:
        ever_connected_vms = await VirtualMachineRepository.get_ever_connected(self.db_connection)
        return 'Ever connected VMs: \r\n' + utils.models_to_str(ever_connected_vms)


class ShowAuthorizedAction(Action):
    async def run(self, data_tokens) -> Union[str, None]:
        authorized_vms = await VirtualMachineRepository.get_authorized(self.db_connection)
        return 'Authenticated VMs: \r\n' + utils.models_to_str(authorized_vms)


class LogoutAction(Action):
    async def run(self, data_tokens) -> Union[str, None]:
        vm = await VirtualMachineRepository.get({'host': data_tokens[0], 'port': int(data_tokens[1])},
                                                self.db_connection)
        vm = vm[0]
        current_host = project_settings.HOST

        if not await VirtualMachineRepository.is_authorized(current_host, vm):
            return f'Error. You are not authenticated.'

        await VirtualMachineRepository.nullify_authorized_host(vm.id, self.db_connection)
        return f'Logged out from VM {vm.host}:{vm.port}.'


class DisconnectAction(Action):
    async def run(self, data_tokens) -> Union[str, None]:
        vm = await VirtualMachineRepository.get({'host': data_tokens[0], 'port': int(data_tokens[1])},
                                                self.db_connection)
        vm = vm[0]
        await ConnectionRepository.close_vm_connections(vm.id, self.db_connection)
        return f'Disconnected from VM {vm.host}:{vm.port}.'


class UpdateVMAction(Action):

    async def run(self, data_tokens) -> Union[str, None]:
        vm = await VirtualMachineRepository.get({'host': data_tokens[0], 'port': int(data_tokens[1])},
                                                self.db_connection)
        vm = vm[0]
        current_host = project_settings.HOST

        if not await VirtualMachineRepository.is_authorized(current_host, vm):
            return f'Error. You are not authenticated.'

        update_data = data_tokens[2:]
        validated_data = await self._validate_dto(vm, update_data)

        await VirtualMachineRepository.update(vm.id, validated_data, self.db_connection)
        return f'VM {vm.host}:{vm.port} was successfully updated.'

    async def _validate_dto(self, vm, update_data):
        update_data = {field_value.split(':')[0]: field_value.split(':')[1] for field_value in update_data}
        for field_name, value in update_data.items():
            if field_name == 'password':
                value = Crypt().encrypt(value)
            setattr(vm, field_name, value)

        return dict(vm)


class ShowHardDrivesAction(Action):
    async def run(self, data_tokens) -> Union[str, None]:
        hard_drives = await HardDriveRepository.get_all_with_vm(self.db_connection)
        return 'Hard drives:' + utils.models_to_str(hard_drives)


class HelpAction(Action):
    async def run(self, data_tokens):
        return 'Available commands: \r\n' + ', '.join(list(ActionFactory.acts.keys()))


class ActionFactory:
    acts = {
        'add_vm': AddVMAction,
        'connect_to_vm': ConnectToVMAction,
        'show_connected': ShowCurrentlyConnectedAction,
        'show_ever_connected': ShowEverConnectedAction,
        'show_authorized': ShowAuthorizedAction,
        'update_vm': UpdateVMAction,
        'logout': LogoutAction,
        'disconnect': DisconnectAction,
        'show_hard_drives': ShowHardDrivesAction,
        'help': HelpAction
    }

    @classmethod
    def get_act(cls, cmd):
        tokens = cmd.split(' ')
        cmd = tokens[0]
        act_cls = cls.acts.get(cmd)
        return act_cls
