from typing import List
from datetime import datetime

import asyncpg
import abc
from pydantic import BaseModel

from models import (VirtualMachineInput, VirtualMachineOutput, VirtualMachine, HardDrive, Connection,
                    HardDriveWithVirtualMachine)
from encryption import Crypt
from query_builders import WhereBuilder, SetBuilder


class AbstractRepository(abc.ABC):

    @abc.abstractmethod
    def get(self, params: dict, db_connection: asyncpg.connection.Connection) -> BaseModel:
        raise NotImplementedError


class VirtualMachineRepository(AbstractRepository):
    table_name = 'virtual_machines'
    dto_model = VirtualMachineOutput

    @classmethod
    async def create(cls, obj: VirtualMachineInput, db_connection: asyncpg.connection.Connection):

        await db_connection.execute(
            f'''INSERT INTO {cls.table_name}
        (ram_amount, dedicated_cpu, host, port, login, password) 
        VALUES ($1, $2, $3, $4, $5, $6)''', obj.ram_amount, obj.dedicated_cpu, obj.host, obj.port, obj.login,
            obj.password)

    @classmethod
    async def get(cls, params: dict, db_connection: asyncpg.connection.Connection, mode='AND'):

        offset = 1
        params_str = WhereBuilder.build(params, offset, mode)

        rows = await db_connection.fetch(f'''
        SELECT 
        DISTINCT ON (v.id) v.*, COALESCE(SUM(hd.size), 0) as hard_drive_space, json_agg(hd.id) as hard_drives_ids 
        FROM {cls.table_name} v
            LEFT JOIN hard_drives hd ON hd.virtual_machine_id = v.id
            WHERE {params_str}
        
        GROUP BY v.id
        ''', *list(params.values()))
        return [VirtualMachine(**dict(row)) for row in rows]

    @classmethod
    async def update(cls, obj_id: int, params: dict, db_connection: asyncpg.connection.Connection):

        for field_to_remove in VirtualMachine.READONLY_FIELDS:
            params.pop(field_to_remove, None)

        offset = 2
        params_str, params_copy = SetBuilder.build(params, params.copy(), offset)

        await db_connection.execute(
            f'UPDATE {cls.table_name} SET {params_str} WHERE id=$1',
            obj_id, *list(params_copy.values()))

    @classmethod
    async def nullify_authorized_host(cls, obj_id: int, db_connection: asyncpg.connection.Connection):
        await db_connection.execute(f'UPDATE {cls.table_name} SET authorized_host = NULL WHERE id=$1', obj_id)

    @classmethod
    async def get_connected(cls, db_connection: asyncpg.connection.Connection):
        rows = await db_connection.fetch(f'''
        SELECT 
        DISTINCT ON (v.id) v.*, COALESCE(SUM(hd.size), 0) as hard_drive_space, json_arrayagg(hd.id) as hard_drives_ids  
        FROM {cls.table_name} v
        
        LEFT JOIN hard_drives hd ON hd.virtual_machine_id = v.id
        WHERE v.id IN (SELECT v.id FROM connections c WHERE c.virtual_machine_id = v.id AND c.end_dttm is NULL)
        
        GROUP BY v.id ORDER BY v.id
        ''')
        return [cls.dto_model(**dict(row)) for row in rows]

    @classmethod
    async def get_ever_connected(cls, db_connection: asyncpg.connection.Connection):
        rows = await db_connection.fetch(f'''
        SELECT 
        DISTINCT ON (v.id) v.*, COALESCE(SUM(hd.size), 0) as hard_drive_space, json_arrayagg(hd.id) as hard_drives_ids  
        FROM {cls.table_name} v
        
        LEFT JOIN hard_drives hd ON hd.virtual_machine_id = v.id
        WHERE v.id IN (SELECT v.id FROM connections c WHERE c.virtual_machine_id = v.id)
        
        GROUP BY v.id ORDER BY v.id
        ''')
        return [cls.dto_model(**dict(row)) for row in rows]

    @classmethod
    async def get_authorized(cls, db_connection: asyncpg.connection.Connection):
        rows = await db_connection.fetch(f'''
        SELECT 
        DISTINCT ON (v.id) v.*, COALESCE(SUM(hd.size), 0) as hard_drive_space, json_agg(hd.id) as hard_drives_ids 
        FROM {cls.table_name} v
            LEFT JOIN hard_drives hd ON hd.virtual_machine_id = v.id
            WHERE authorized_host IS NOT NULL
        
        GROUP BY v.id
        ORDER BY v.id
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
    async def get(cls, params: dict, db_connection: asyncpg.connection.Connection, mode='AND') -> List[BaseModel]:

        offset = 1
        params_str = WhereBuilder.build(params, offset, mode)

        rows = await db_connection.fetch(f'SELECT * FROM {cls.table_name} WHERE {params_str}', *list(params.values()))
        return [cls.dto_model(**dict(row)) for row in rows]

    @classmethod
    async def update(cls, obj_id: int, params: dict, db_connection: asyncpg.connection.Connection):

        offset = 2
        params_str, params_copy = SetBuilder.build(params, params.copy(), offset)

        await db_connection.execute(
            f'UPDATE {cls.table_name} SET {params_str} WHERE id=$1',
            obj_id, *list(params_copy.values()))

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
        # VM can only have one connection at a time
        new_connection = Connection(id=None, end_dttm=None, virtual_machine_id=vm.id, connection_host=host,
                                    connection_port=port, start_dttm=datetime.now())
        await ConnectionRepository.close_vm_connections(vm.id, db_connection)
        await ConnectionRepository.create(new_connection, db_connection)


class HardDriveRepository(AbstractRepository):
    table_name = 'hard_drives'
    dto_model = HardDrive

    @classmethod
    async def get(cls, params: dict, db_connection: asyncpg.connection.Connection, mode='AND') -> List[BaseModel]:

        offset = 1
        params_str = WhereBuilder.build(params, offset, mode)

        rows = await db_connection.fetch(f'SELECT * FROM {cls.table_name} WHERE {params_str}', *list(params.values()))
        return [cls.dto_model(**dict(row)) for row in rows]

    @classmethod
    async def get_all_with_vm(cls, db_connection: asyncpg.connection.Connection) -> List[BaseModel]:
        rows = await db_connection.fetch(f'''
                SELECT hd.id as hard_drive_id, hd.*, v.id as virtual_machine_id, v.*, Aggregated.hard_drive_space
                FROM (
                    SELECT v.id, COALESCE(SUM(hd.size), 0) as hard_drive_space
                    FROM virtual_machines v
                    LEFT JOIN hard_drives hd ON hd.virtual_machine_id = v.id
                    GROUP BY v.id
                ) AS Aggregated
                INNER JOIN virtual_machines v ON Aggregated.id = v.id
                RIGHT JOIN hard_drives hd ON hd.virtual_machine_id = v.id
                ORDER BY hd.id
                ''')

        return [HardDriveWithVirtualMachine(**dict(row)) for row in rows]
