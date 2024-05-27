import os

from dotenv import load_dotenv

load_dotenv()

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 8005

CLIENT_HOST = '127.0.0.7'
CLIENT_PORT = 8005

DB_USER = 'postgres'
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = 'redsoft_test'

ENCRYPTION_SALT = os.environ.get('ENCRYPTION_SALT')
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')

# test strings
# add_vm ram_amount:16 dedicated_cpu:4 host:127.0.3.9 port:8000 login:fithanso password:passwrd
# connect_to_vm 127.0.3.9 8000
# logout 127.0.0.7 8005
# disconnect 127.0.0.7 8005
# update_vm 127.0.0.7 8005 ram_amount:3 dedicated_cpu:5
# show_hard_drives
