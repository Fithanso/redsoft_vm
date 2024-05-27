from datetime import datetime
from typing import ClassVar, List

from pydantic import BaseModel, Field


class VirtualMachineInput(BaseModel):
    ram_amount: float
    dedicated_cpu: int
    host: str
    port: int
    login: str
    password: str

    class Config:
        validate_assignment = True


class VirtualMachineOutput(BaseModel):
    READONLY_FIELDS: ClassVar[List] = ['id', 'hard_drives_ids', 'hard_drive_space']

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


class HardDriveWithVirtualMachine(BaseModel):

    hard_drive_id: int | None
    size: float

    virtual_machine_id: int
    ram_amount: float
    dedicated_cpu: int
    host: str
    port: int
    authorized_host: str | None
    hard_drive_space: float = 0


