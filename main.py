import os
import uuid
import argparse
import paramiko
import requests
import pwd
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
    ssh_host_target = os.getenv('DOCKER_HOST')
    if ssh_host_target is None:
        print("The required DOCKER_HOST environment variable is not present")
        return 1

    session = requests.session()
    try:
        session.get(args.hub_url)
    except (requests.ConnectionError, requests.exceptions.InvalidSchema):
        print("{} can't be reached".format(args.hub_url))
        return 1

    target_user = 'mountuser'
    home = "/home/{}".format(target_user)
    ssh_dir = "{}/.ssh".format(home)

    os.makedirs(ssh_dir)
    f_path = "{}/id_rsa".format(ssh_dir)

    rsa_key = paramiko.RSAKey.generate(2048)
    rsa_key.write_private_key_file(f_path)
    public_key = ("%s ssh-rsa %s %s" % (
        '', rsa_key.get_base64(), '')).strip()

    with open(f_path, 'r') as file:
        private_key = "".join(file.readlines())

    auth_keys = "{}/authorized_keys".format(ssh_dir)
    with open(auth_keys, 'w') as auth_file:
        auth_file.write(public_key)
    os.chmod(auth_keys, 0o600)

    # Ensure .ssh dir and it's content is owned by the target_user
    uid, gid = pwd.getpwnam(target_user).pw_uid, pwd.getpwnam(
        target_user).pw_uid

    os.chown(ssh_dir, uid, gid)
    for root, dirs, files in os.walk(ssh_dir):
        for ssh_dir in dirs:
            os.chown(os.path.join(root, ssh_dir), uid, gid)
        for ssh_file in files:
            os.chown(os.path.join(root, ssh_file), uid, gid)

    user_cert = '/C=DK/ST=NA/L=NA/O=NBI/OU=NA/CN=Rasmus ' \
                'Munk/emailAddress=rasmus.munk@nbi.ku.dk'

    # SessionID is used as the user parameter, therefore for testing
    # purposes we use root
    mig_dict = {'SESSIONID': target_user,
                'USER_CERT': user_cert,
                'TARGET_MOUNT_ADDR': "@" + ssh_host_target + ":",
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
    call(['/usr/sbin/sshd', '-D', '-E', '/var/log/ssh'])


if __name__ == '__main__':
    main(parser.parse_args())
