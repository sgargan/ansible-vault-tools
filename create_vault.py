#!/usr/bin/python

# create an encrypted vars ansible vault containing the specified key value
# pairs. If any of the values is a file on the filesystem then its content
# will be read and base64 encoded.
#
# This is primarily useful for storing sensitive binary information such as
# cryptographic keys, certs and passwords securely.
#
from ansible.utils.vault import VaultEditor
from argparse import ArgumentParser
import base64, getpass, os, sys, signal, yaml

def parse_vault_args(item_args):
    items = {}

    for item in item_args:
        k, v = item.split('=')
        if os.path.isfile(v):
            try:
                with open(v, "rb") as vault_data:
                    items[k] = base64.b64encode(vault_data.read())
            except Exception, e:
                console("Could not read file '%s', '%s'" % v, e)
        else:
            items[k] = v

    console('parsed %d entries' % len(items))
    return items

def get_password(password):
    if not password:
        password = getpass.getpass('Enter vault password:')
    return password

def console(msg):
    if not quiet:
        print msg

def add_to_vault(args):
    vault_file = args.v
    password = get_password(args.p)
    editor = VaultEditor(args.c, password, vault_file)

    console("Adding entries to %s" % vault_file)
    if args.t and os.path.isfile(vault_file):
        os.remove(vault_file)

    vault_data = {}
    if os.path.isfile(vault_file):
        if is_encrypted(vault_file):
            editor.decrypt_file()
        with open(vault_file, 'r') as v:
            vault_data = yaml.load(v)

    vault_args = parse_vault_args(args.i)
    vault_data = dict(vault_data.items() + vault_args.items())

    with open(vault_file, 'w') as v:
        v.write( yaml.dump(vault_data, default_flow_style=False) )

    editor.encrypt_file()

def extract_from_vault(args):

    vault_file = args.v
    password = get_password(args.p)
    editor = VaultEditor(args.c, password, vault_file)

    vault_data = {}
    if os.path.isfile(vault_file):

        encrypted = is_encrypted(vault_file)
        if encrypted:
            editor.decrypt_file()

        try:
            with open(vault_file, 'r') as v:
                vault_data = yaml.load(v)

            for item in args.i:
                key, file = item.split('=')
                try:
                    if vault_data[key]:
                        with open(file, 'wb') as unpack:
                            unpack.write(base64.b64decode(vault_data[key]))
                        console('Extracted %s to %s' % (key, file))
                except Exception, e:
                    console('Could not extract %s to %s, %s' % (key, file, e))
        except:
            if encrypted:
                editor.encrypt_file()

def is_encrypted(vault_file):
    with open(vault_file, 'r') as v:
        return '$ANSIBLE_VAULT' in v.readline()
        
def parse_args():
    usage = '''
    Create an encrypted vars ansible vault containing the specified key value
    pairs. If any of the values is a file on the filesystem then its content
    will be read and base64 encoded.

    This is primarily useful for storing sensitive binary information such as
    cryptographic keys, certs and passwords securely.

    > create_vault -v prod_certs_vault -i prod_cert=./prod.crt -i prod_key=./prod.key -i prod_password=some_secret

    To convert the base64 data back to a file on a target host you can use the following in a template

    {{prod_cert | b64decode}}

    if you'd like to unpack them from the vault file directly specify the -e flag and this will reverse the process

    > create_vault -v prod_certs_vault -e -i prod_cert=/tmp/prod.crt

    will open the vault, read the kv pair keyed with prod_cert, decode and dump it to the given path

    '''
    parser = ArgumentParser(prog='create_vault')
    parser.add_argument('-v', help='the name of the vault file to create or update')
    parser.add_argument('-i', help='item to add, items are key=value pairs. if the value is a file then the contents are parsed and base64 encoded', nargs='+')
    parser.add_argument('-p', help='password for the vault.', default=None)
    parser.add_argument('-c', help='the name of the cypher to use', default='AES256')
    parser.add_argument('-q', help='quiet', default=False, action="store_true")
    parser.add_argument('-e', help='extract', default=False, action="store_true")
    parser.add_argument('-t', help='truncate existing, default is to overwrite and append', default=False, action="store_true")

    return parser.parse_args()

global quiet

if __name__ == '__main__':

    try:
      args = parse_args()
    except Exception, e:
      print e

    quiet = args.q
    if args.e:
        extract_from_vault(args)
    else:
        add_to_vault(args)
