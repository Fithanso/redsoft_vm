import abc
from typing import Union
from datetime import datetime

from models import VirtualMachineInput, Connection
from repositories import VirtualMachineRepository, ConnectionRepository, HardDriveRepository
from encryption import Crypt
from aioconsole import ainput
import settings as project_settings
import utils


class Action(metaclass=abc.ABCMeta):
    def __init__(self, reader, writer, db_connection):
        self.reader = reader
        self.writer = writer
        self.db_connection = db_connection
        self.client_action_delimiter = '%%'

    @abc.abstractmethod
    async def run(self, data_tokens) -> str:
        raise NotImplementedError()


class AuthAction(Action):
    async def run(self, data_tokens) -> str:
        # very simple authentication
        client_host = project_settings.CLIENT_HOST
        client_port = project_settings.CLIENT_PORT
        # it means that the client takes his username and password and checks them.
        # but in this case, we take it from the general DB.
        # although it would be better do create separate DB for a client
        vm = await VirtualMachineRepository.get({'host': client_host, 'port': int(client_port)},
                                                self.db_connection)
        vm = vm[0]
        login = data_tokens[0]
        password = data_tokens[1]
        if await VirtualMachineRepository.authenticate(login, password, vm):
            return 'OK'
        return 'ERROR'


class ClientActionFactory:
    acts = {
        'client_auth': AuthAction,
    }

    @classmethod
    def get_act(cls, cmd):
        act_cls = cls.acts.get(cmd)
        return act_cls
