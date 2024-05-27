class DecodedData:
    public_data: str | None
    action: str | None
    tokens: list
    _secret_delimiter = '|||'
    _client_action_delimiter = '%%'
    __secret_data: str | None

    def __init__(self, data):
        self.__secret_data = None
        self.public_data = None
        self.action = None
        self.tokens = []
        self.decode_message(data)

        if self.__secret_data:
            self._decode_secret_data()

    def decode_message(self, data) -> None:
        decoded = data.decode()

        if self._secret_delimiter in decoded:
            splitted = decoded.split(self._secret_delimiter)
            self.__secret_data, self.public_data = splitted[0], splitted[1]
        else:
            self.public_data = decoded

    def _decode_secret_data(self):
        if self._client_action_delimiter in self.__secret_data:
            splitted = self.__secret_data.split(self._client_action_delimiter)
            self.action = splitted[0]
            self._decode_tokens(splitted[1])

    def _decode_tokens(self, tokens_str):
        self.tokens = tokens_str.split(':')

    def __str__(self):
        return self.public_data

    def __repr__(self):
        return self.public_data
