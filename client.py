import asyncio
import time
from typing import Union, Tuple

import settings as project_settings


class DecodedData:
    _secret_delimiter = '|||'
    __secret_data: str | None
    public_data: str | None

    def __init__(self, data):
        self.__secret_data = None
        self.public_data = None
        self.decode_message(data)

    def decode_message(self, data) -> None:
        decoded = data.decode()

        if self._secret_delimiter in decoded:
            splitted = decoded.split(self._secret_delimiter)
            self.__secret_data, self.public_data = splitted[0], splitted[1]
        else:
            self.public_data = decoded

        print(self.__secret_data, self.public_data)

    def __str__(self):
        return self.public_data

    def __repr__(self):
        return self.public_data


async def run_client() -> None:
    reader, writer = await asyncio.open_connection(project_settings.HOST, project_settings.PORT)
    print("Launched")

    while True:
        data = await reader.read(1024)
        if not data:
            print("Socket closed")
            return
        decoded_data = DecodedData(data)
        print(f"Message: {decoded_data!r}")
        writer.write(b'client received')
        await writer.drain()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_client())
