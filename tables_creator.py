import asyncio
import asyncpg
import datetime


async def main():
    # Establish a connection to an existing database named "test"
    # as a "postgres" user.
    conn = await asyncpg.connect('postgresql://postgres:scubastar123@localhost/redsoft_test')
    # Execute a statement to create a new table.
    await conn.execute('''
        CREATE TABLE virtual_machines(
            id serial PRIMARY KEY,
            ram_amount double precision,
            dedicated_cpu smallint,
            host varchar(128),
            port integer,
            login varchar(128),
            password varchar(128),
            authorized_host varchar(128)
        )
    ''')

    await conn.execute('''
        CREATE TABLE hard_drives(
            id serial PRIMARY KEY,
            size double precision,
            virtual_machine_id integer REFERENCES virtual_machines(id)
        )
    ''')

    await conn.execute('''
        CREATE TABLE connections(
            id serial PRIMARY KEY,
            virtual_machine_id integer REFERENCES virtual_machines(id),
            connection_host varchar(128),
            connection_port integer,
            start_dttm timestamp with time zone,
            end_dttm timestamp with time zone
        )
    ''')

    # Close the connection.
    await conn.close()


asyncio.get_event_loop().run_until_complete(main())
