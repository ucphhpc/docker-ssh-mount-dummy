import os
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


def main(args):
    session = requests.session()
    try:
        session.get(args.hub_url)
    except (requests.ConnectionError, requests.exceptions.InvalidSchema):
        print("{} can't be reached".format(args.hub_url))
        return 1

    os.makedirs('/root/.ssh/')
    rsa_key = paramiko.RSAKey.generate(2048)
    rsa_key.write_private_key_file('/root/.ssh/id_rsa')
    public_key = ("%s ssh-rsa %s %s" % (
        '', rsa_key.get_base64(), '')).strip()

    authorized_keys = open('/root/.ssh/authorized_keys', 'w')
    authorized_keys.write(public_key)

    ip = socket.gethostbyname(socket.gethostname())
    user_cert = '/C=DK/ST=NA/L=NA/O=NBI/OU=NA/CN=Rasmus ' \
                'Munk/emailAddress=rasmus.munk@nbi.ku.dk'

    mig_dict = {'SESSIONID': os.urandom(24),
                'USER_CERT': user_cert,
                'TARGET_MOUNT_ADDR': "@" + ip + ":",
                'MOUNTSSHPRIVATEKEY': rsa_key,
                'MOUNTSSHPUBLICKEY': public_key}

    mount_header = {'Remote-User': user_cert,
                    'Mig-Mount': str(mig_dict)}

    session.get(args.hub_url + args.mount_url, headers=mount_header)

    # Run ssh service
    call(['/usr/sbin/sshd', '-D'])


if __name__ == '__main__':
    main(parser.parse_args())