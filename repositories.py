import asyncpg

from models import VirtualMachine, HardDrive, Connection

# TODO: написать интерфейс под репозитории с create и get_by_id как обязательными


class VirtualMachineRepository:
    table_name = 'virtual_machines'

    @classmethod
    async def create_vm(cls, vm: VirtualMachine, db_connection: asyncpg.connection.Connection):
        await db_connection.execute(
            f'''INSERT INTO {cls.table_name}
        (ram_amount, dedicated_cpu, host, port, login, password) 
        VALUES ($1, $2, $3, $4, $5, $6)''', vm.ram_amount, vm.dedicated_cpu, vm.host, vm.port, vm.login, vm.password)

    @classmethod
    async def get_vm_by_id(cls, vm_id: int, db_connection: asyncpg.connection.Connection):
        row = await db_connection.fetchrow('SELECT * FROM {cls.table_name} WHERE id = $1', )

