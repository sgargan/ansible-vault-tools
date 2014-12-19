Vaults make it simple and easy to store sensitive text information like away from prying eyes while at rest in source control. While they were primarily intended to store text info, with a little careful bas64 manipulation they can easily store sensitive binary information as well.

This script takes the pain out of adding base64 encoded binary info into your ansible vaults. Once in the vault, the template and playbook include provided can be used to recreate the binary on your target hosts.

Adding
------

You pass key=value pairs to the script and if the values are paths on the filesystem their contents will be read, base64 encoded and added to the vault. If not files the values are written as supplied. you can supply the password as a param or if missing, the script will prompt for it.

```bash
./create_vault.py -v prod_keystore_vault -i prod_keystore=path/to/keystore keystore_password=some_password
```

This will create a new vault with two entries

```yaml
prod_keystore: LS0tLS1CRUdJTiBDRVJU...........

keystore_pass: some_password
```

If the vault already exists, existing keys will be overwritten and new keys appended.

Restoring via ansible
---------------------

You can decode any base64 string in a Jinja template very easily e.g. {{prod_keystore | b64decode}}

To restore encoded sensitive binary data on your target hosts you can use reusable pattern playbook and template included.

```yaml
- hosts: webservers

  vars_files:
    - vaults/prod_keystore_vault

  tasks:
    - {include: includes/base64_to_file.yml, base64_data: {{prod_keystore}}, dest: /opt/my_app/keystore }
```

Restoring via script
--------------------

If you'd like to pull out encoded data with the script, you can supply the original create line with the -e switch. It will read the vault find the requested keys, decode their contents and write them to the supplied path.

```bash
./create_vault.py -v prod_keystore_vault -e -i prod_keystore=path/to/keystore_copy
```
