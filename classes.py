from pydantic import BaseModel

from datetime import datetime

class VirtualMachine(BaseModel):
    id : int
    ram_amount: float
    dedicated_cpu: int
    host: str
    port: int
    login: str
    password: str


class HardDrive(BaseModel):
    id: int
    size: float
    virtual_machine_id: int

# тут хранятся подключения к машинам. если end_dttm не указан, значит подключение активно
class Connection(BaseModel):
    virtual_machine_id: int
    connection_host: str | None
    connection_port: int | None
    start_dttm: datetime
    end_dttm: datetime | None