# redsoft_vm

## Deployment

For application to work you need to:
1. Have `.env` file in the project root with following variables:
```
DB_PASSWORD=[db password]
ENCRYPTION_SALT=[salt must be 16 characters long]
ENCRYPTION_KEY=[key must be 16, 24, or 32 characters long]
```


2. Install poetry
3. Run `poetry install` from project root
4. Enter she with `poetry shell`
5. You can now run `server.py` and `client.py`