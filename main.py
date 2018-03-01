import os
import paramiko


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
