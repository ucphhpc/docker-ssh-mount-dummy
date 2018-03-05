import os
import uuid
import argparse
import paramiko
import requests
import socket
from subprocess import call

parser = argparse.ArgumentParser()
parser.add_argument('--hub-url', dest='hub_url',
                    default='http://127.0.0.1:8888')
parser.add_argument('--mount-url', dest='mount_url',
                    default='/hub/mount')
parser.add_argument('--auth-url', dest='auth_url',
                    default='/hub/login')


def main(args):
    session = requests.session()
    try:
        session.get(args.hub_url)
    except (requests.ConnectionError, requests.exceptions.InvalidSchema):
        print("{} can't be reached".format(args.hub_url))
        return 1

    os.makedirs('/root/.ssh/')
    f_path = '/root/.ssh/id_rsa'

    rsa_key = paramiko.RSAKey.generate(2048)
    rsa_key.write_private_key_file(f_path)
    public_key = ("%s ssh-rsa %s %s" % (
        '', rsa_key.get_base64(), '')).strip()

    with open(f_path, 'r') as file:
        private_key = "".join(file.readlines())

    with open('/root/.ssh/authorized_keys', 'w') as auth_file:
        auth_file.write(public_key)

    ip = socket.gethostbyname(socket.gethostname())
    user_cert = '/C=DK/ST=NA/L=NA/O=NBI/OU=NA/CN=Rasmus ' \
                'Munk/emailAddress=rasmus.munk@nbi.ku.dk'

    # SessionID is used as the user parameter, therefore for testing
    # purposes we use root
    mig_dict = {'SESSIONID': 'root',
                'USER_CERT': user_cert,
                'TARGET_MOUNT_ADDR': "@" + ip + ":",
                'MOUNTSSHPRIVATEKEY': private_key,
                'MOUNTSSHPUBLICKEY': public_key}

    auth_header = {'Remote-User': user_cert}

    mount_header = {'Remote-User': user_cert,
                    'Mig-Mount': str(mig_dict)}
    # Auth
    session.get(args.hub_url + args.auth_url, headers=auth_header)
    # Mount
    session.get(args.hub_url + args.mount_url, headers=mount_header)

    # Run ssh service
    call(['/usr/sbin/sshd', '-D'])


if __name__ == '__main__':
    main(parser.parse_args())
