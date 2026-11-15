import os
import secrets
import shlex
from pathlib import Path


def main():
    destination = Path('.env.azure')
    values = {'SQL_ADMIN_USER': 'pantrypaladmin'}
    for name in ('SQL_ADMIN_PASSWORD', 'PANTRY_DB_APP_PASSWORD', 'CATALOG_DB_APP_PASSWORD'):
        values[name] = 'Aa1!' + secrets.token_hex(24)
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w') as output:
        for name, value in values.items():
            output.write(f'export {name}={shlex.quote(value)}\n')
    print(f'Created {destination} with owner-only permissions; no passwords printed.')


if __name__ == '__main__':
    main()
