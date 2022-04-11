import os
import paramiko
import pwd
from subprocess import call


def get_username(default_fallback=False):
    if "USERNAME" not in os.environ:
        if default_fallback:
            return "mountuser"
        else:
            return None
    return os.environ["USERNAME"]


def main():
    username = get_username(default_fallback=True)
    if not username:
        print("Missing USERNAME environment variable was not set.")
        exit(-1)

    home = "/home/{}".format(username)
    ssh_dir = "{}/.ssh".format(home)

    os.makedirs(ssh_dir)
    f_path = "{}/id_rsa".format(ssh_dir)

    rsa_key = paramiko.RSAKey.generate(2048)
    rsa_key.write_private_key_file(f_path)
    public_key = ("%s ssh-rsa %s %s" % (
        '', rsa_key.get_base64(), '')).strip()

    auth_keys = "{}/authorized_keys".format(ssh_dir)
    with open(auth_keys, 'w') as auth_file:
        auth_file.write(public_key)
    os.chmod(auth_keys, 0o600)

    # Ensure .ssh dir and it's content is owned by the username
    uid, gid = pwd.getpwnam(username).pw_uid, \
        pwd.getpwnam(username).pw_uid

    os.chown(ssh_dir, uid, gid)
    for root, dirs, files in os.walk(ssh_dir):
        for ssh_dir in dirs:
            os.chown(os.path.join(root, ssh_dir), uid, gid)
        for ssh_file in files:
            os.chown(os.path.join(root, ssh_file), uid, gid)
    # Run ssh service
    call(['/usr/sbin/sshd', '-D', '-E', '/var/log/ssh'])


if __name__ == '__main__':
    main()
