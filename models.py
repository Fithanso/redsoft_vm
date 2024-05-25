from pydantic import BaseModel

from datetime import datetime


class VirtualMachine(BaseModel):
    id: int | None
    ram_amount: float
    dedicated_cpu: int
    host: str
    port: int
    login: str
    password: str
    authorized_host: str | None
    # авторизации нам не нужно хранить, поэтому можно не делать под это модель


class HardDrive(BaseModel):
    id: int | None
    size: float
    virtual_machine_id: int


# тут хранятся подключения к машинам. если end_dttm не указан, значит подключение активно
class Connection(BaseModel):
    id: int | None
    virtual_machine_id: int
    connection_host: str | None
    connection_port: int | None
    start_dttm: datetime
    end_dttm: datetime | None
