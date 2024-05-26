from datetime import datetime
from typing import ClassVar, List

from pydantic import BaseModel, Field


class VirtualMachine(BaseModel):
    SAFE_FIELDS: ClassVar[list] = ['id', 'authorized_host']

    id: int | None
    ram_amount: float
    dedicated_cpu: int
    host: str
    port: int
    login: str
    password: str
    authorized_host: str | None
    hard_drives_ids: str | None
    hard_drive_space: float = 0

    class Config:
        validate_assignment = True


class HardDrive(BaseModel):
    id: int | None
    size: float
    virtual_machine_id: int


class Connection(BaseModel):
    id: int | None
    virtual_machine_id: int
    connection_host: str | None
    connection_port: int | None
    start_dttm: datetime
    end_dttm: datetime | None

    class Config:
        validate_assignment = True
