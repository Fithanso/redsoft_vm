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

# test strings
# add_vm ram_amount:16 dedicated_cpu:4 host:127.0.1.9 port:8000 login:fithanso password:passwrd
# connect_to_vm 127.0.0.7 8000
# logout 127.0.0.7 8000
# disconnect 127.0.0.7 8000
# update_vm 127.0.0.7 8000 ram_amount:1 dedicated_cpu:2
# show_hard_drives
