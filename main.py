import os
import paramiko
from subprocess import call
from utils.io import (
    makedirs,
    exists,
    write,
    chmod,
    chown,
    lookup_uid,
    lookup_gid,
    load,
    touch,
)


def get_username(default_fallback=False):
    if "USERNAME" not in os.environ:
        if default_fallback:
            return "mountuser"
        else:
            return None
    return os.environ["USERNAME"]


def get_authorized_keys_dir():
    if "AUTHORIZED_KEYS_DIR" not in os.environ:
        return None
    return os.environ["AUTHORIZED_KEYS_DIR"]


def main():
    username = get_username(default_fallback=True)
    if not username:
        print("Missing USERNAME environment variable was not set.")
        exit(-1)

    public_keys = []
    authorized_keys_dir = get_authorized_keys_dir()
    if authorized_keys_dir and exists(authorized_keys_dir):
        for root, dirs, files in os.walk(authorized_keys_dir):
            for _file in files:
                content = load(os.path.join(root, _file))
                if content:
                    public_keys.append(content)

    home = os.path.join(os.sep, "home", username)
    ssh_dir = os.path.join(home, ".ssh")
    if not exists(ssh_dir):
        created, msg = makedirs(ssh_dir)
        if not created:
            print(msg)
            exit(-1)

    ssh_key_path = os.path.join(ssh_dir, "id_rsa")
    rsa_key = paramiko.RSAKey.generate(2048)
    rsa_key.write_private_key_file(ssh_key_path)
    public_key = ("%s ssh-rsa %s %s" % ("", rsa_key.get_base64(), "")).strip()
    public_keys.append(public_key)

    authorized_keys_path = os.path.join(ssh_dir, "authorized_keys")
    if not exists(authorized_keys_path):
        created, msg = touch(authorized_keys_path)
        print(msg)
        if not created:
            exit(-1)

    if not write(authorized_keys_path, public_keys, mode="a"):
        print("Failed to write public keys to authorized_keys file.")
        exit(-1)

    # Ensure private key has correct permissions
    success, msg = chmod(ssh_key_path, 0o600)
    print(msg)
    if not success:
        exit(-1)

    # Ensure .ssh dir and it's content is owned by the username
    uid, gid = lookup_uid(username), lookup_gid(username)
    if not uid or not gid:
        print("Failed to lookup uid and gid for user: {}".format(username))
        exit(-1)

    success, msg = chown(ssh_dir, uid, gid)
    print(msg)
    if not success:
        exit(-1)

    for root, dirs, files in os.walk(ssh_dir):
        for ssh_dir in dirs:
            success, msg = chown(os.path.join(root, ssh_dir), uid, gid)
            print(msg)
        for ssh_file in files:
            success, msg = chown(os.path.join(root, ssh_file), uid, gid)
            print(msg)
    # Run ssh service
    call(["/usr/sbin/sshd", "-D", "-E", "/var/log/ssh"])


if __name__ == "__main__":
    main()
