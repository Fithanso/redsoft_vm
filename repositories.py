from typing import List
from datetime import datetime

import asyncpg
import abc
from pydantic import BaseModel

from models import VirtualMachine, HardDrive, Connection
from encryption import Crypt

# TODO: мб для каждой машины надо строчкой считать объём дисков функцией аггрегации
# обновляет данные в авторизованной вм - команда обновления, но с проверкой аута


class AbstractRepository(abc.ABC):

    @abc.abstractmethod
    def create(self, obj: VirtualMachine, db_connection: asyncpg.connection.Connection):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, obj_id: int, db_connection: asyncpg.connection.Connection) -> BaseModel:
        raise NotImplementedError

    @abc.abstractmethod
    def update(self, obj_id: int, params: dict, db_connection: asyncpg.connection.Connection):
        raise NotImplementedError


class VirtualMachineRepository(AbstractRepository):
    table_name = 'virtual_machines'
    dto_model = VirtualMachine

    @classmethod
    async def create(cls, obj: VirtualMachine, db_connection: asyncpg.connection.Connection):
        await db_connection.execute(
            f'''INSERT INTO {cls.table_name}
        (ram_amount, dedicated_cpu, host, port, login, password) 
        VALUES ($1, $2, $3, $4, $5, $6)''', obj.ram_amount, obj.dedicated_cpu, obj.host, obj.port, obj.login,
            obj.password)

    @classmethod
    async def get(cls, obj_id: int, db_connection: asyncpg.connection.Connection):
        row = await db_connection.fetchrow(f'SELECT * FROM {cls.table_name} WHERE id = $1', obj_id)
        return cls.dto_model(**dict(row))

    @classmethod
    async def get_by_host_port(cls, vm_host: str, vm_port: int, db_connection: asyncpg.connection.Connection):
        row = await db_connection.fetchrow(f'SELECT * FROM {cls.table_name} WHERE host = $1 AND port = $2 LIMIT 1',
                                           vm_host, vm_port)
        return cls.dto_model(**dict(row))

    @classmethod
    async def update(cls, obj_id: int, params: dict, db_connection: asyncpg.connection.Connection):

        params_str = ''
        params_copy = params.copy()

        for item in enumerate(params.keys(), 2):
            num, key = item[0], item[1]
            params_str += str(key) + '='
            if params.get(key) == 'NULL' or params.get(key) == 'null':
                params_str += 'NULL, '
                del params_copy[key]
            else:
                params_str += '$' + str(num) + ', '

        params_str = params_str[:-2]

        await db_connection.execute(
            f'UPDATE {cls.table_name} SET {params_str} WHERE id=$1',
            obj_id, *list(params_copy.values()))

    @classmethod
    async def get_connected(cls, db_connection: asyncpg.connection.Connection):
        rows = await db_connection.fetch('''
        SELECT v.* FROM connections c JOIN virtual_machines v ON c.virtual_machine_id = v.id WHERE c.end_dttm is NULL
        ORDER BY v.id
        ''')
        return [cls.dto_model(**dict(row)) for row in rows]

    @classmethod
    async def get_ever_connected(cls, db_connection: asyncpg.connection.Connection):
        rows = await db_connection.fetch('''
        SELECT DISTINCT ON (v.id) v.* FROM connections c JOIN virtual_machines v ON c.virtual_machine_id = v.id
        ORDER BY v.id
        ''')
        return [cls.dto_model(**dict(row)) for row in rows]

    @classmethod
    async def get_authorized(cls, db_connection: asyncpg.connection.Connection):
        rows = await db_connection.fetch(f'''
        SELECT * FROM {cls.table_name} WHERE authorized_host IS NOT NULL ORDER BY id
        ''')
        return [cls.dto_model(**dict(row)) for row in rows]

    @classmethod
    async def is_authorized(cls, host, vm) -> bool:
        return vm.authorized_host == host

    @classmethod
    async def authenticate(cls, login, password, vm) -> bool:
        return login == vm.login and password == Crypt().decrypt(str(vm.password))

    @classmethod
    async def authorize(cls, host, vm, db_connection):
        async with db_connection.transaction():
            await VirtualMachineRepository.update(vm.id, {'authorized_host': host}, db_connection)


class ConnectionRepository(AbstractRepository):
    table_name = 'connections'
    dto_model = Connection

    @classmethod
    async def create(cls, obj: Connection, db_connection: asyncpg.connection.Connection):
        await db_connection.execute(
            f'''INSERT INTO {cls.table_name}
        (virtual_machine_id, connection_host, connection_port, start_dttm, end_dttm) 
        VALUES ($1, $2, $3, $4, $5)''', obj.virtual_machine_id, obj.connection_host, obj.connection_port,
            obj.start_dttm, obj.end_dttm)

    @classmethod
    async def get(cls, obj_id: int, db_connection: asyncpg.connection.Connection):
        row = await db_connection.fetchrow(f'SELECT * FROM {cls.table_name} WHERE id = $1', obj_id)
        return cls.dto_model(**dict(row))

    @classmethod
    async def update(cls, obj_id: int, params: dict, db_connection: asyncpg.connection.Connection):

        params_str = ''
        for item in enumerate(params.keys(), 2):
            params_str += str(item[1]) + '=$' + str(item[0]) + ', '
        params_str = params_str[:-2]

        await db_connection.execute(
            f'UPDATE {cls.table_name} SET {params_str} WHERE id=$1',
            obj_id, *list(params.values()))

    @classmethod
    async def filter_and(cls, params: dict, db_connection: asyncpg.connection.Connection) -> List[BaseModel]:
        params_str = ''
        offset = 1

        for item in enumerate(params.keys(), offset):
            num = item[0]
            key = item[1]

            params_str += str(key) + '=$' + str(num)
            if num != len(params.keys()) + offset - 1:
                params_str += ' AND '

        rows = await db_connection.fetch(f'SELECT * FROM {cls.table_name} WHERE {params_str}', *list(params.values()))
        return [cls.dto_model(**dict(row)) for row in rows]

    @classmethod
    async def opened_vm_connections(cls, vm_id: int, db_connection: asyncpg.connection.Connection) -> List[BaseModel]:

        rows = await db_connection.fetch(
            f'SELECT * FROM {cls.table_name} WHERE virtual_machine_id=$1 AND end_dttm is NULL', vm_id)

        return [cls.dto_model(**dict(row)) for row in rows]

    @classmethod
    async def close_vm_connections(cls, vm_id: int, db_connection: asyncpg.connection.Connection) -> None:
        vm_opened_conns = await ConnectionRepository.opened_vm_connections(vm_id, db_connection)
        for conn in vm_opened_conns:
            await ConnectionRepository.update(conn.id, {'end_dttm': datetime.now()}, db_connection)

    @classmethod
    async def open_connection(cls, host, port, vm, db_connection):
        new_connection = Connection(id=None, end_dttm=None, virtual_machine_id=vm.id, connection_host=host,
                                    connection_port=port, start_dttm=datetime.now())
        await ConnectionRepository.close_vm_connections(vm.id, db_connection)
        await ConnectionRepository.create(new_connection, db_connection)
