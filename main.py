import os
import requests
import paramiko
from io import StringIO

#
# def generate_ssh_rsa_key_pair(size=2048, public_key_prefix='',
#                               public_key_postfix=''):
#     rsa_key = paramiko.RSAKey.generate(size)
#
#     string_io_obj = StringIO()
#     rsa_key.write_private_key(string_io_obj)
#
#     private_key = string_io_obj.getvalue()
#     public_key = ("%s ssh-rsa %s %s" % (
#         public_key_prefix, rsa_key.get_base64(), public_key_postfix)).strip()
#
#     return (private_key, public_key)


def main():
    os.makedirs('/root/.ssh/')
    rsa_key = paramiko.RSAKey.generate(2048)
    rsa_key.write_private_key_file('/root/.ssh/id_rsa')

    public_key = ("%s ssh-rsa %s %s" % (
        '', rsa_key.get_base64(), '')).strip()
    id_rsa_pub = open('/root/.ssh/id_rsa.pub', 'w')
    id_rsa_pub.write(public_key)


if __name__ == '__main__':
    main()
