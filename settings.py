import os

from dotenv import load_dotenv

load_dotenv()

HOST = '127.0.0.1'
PORT = 9999

DB_USER = 'postgres'
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = 'redsoft_test'

ENCRYPTION_SALT = os.environ.get('ENCRYPTION_SALT')
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')

COMMANDS = '''
'''

# test strings
# add_vm 16 4 127.0.0.5 8000 fithanso passwrd
# connect_to_vm 127.0.0.7 8000
# logout 127.0.0.7 8000
# disconnect 127.0.0.7 8000
# update_vm 127.0.0.7 8000 ram_amount:16 dedicated_cpu:10
