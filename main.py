import logging_config
from migrate import Migrate

if __name__ == '__main__':
    location = r'D:\Notion Exports\Export-36cee0fc-4028-4851-9087-8402cb3bd1d5'
    migrate = Migrate(location)
    migrate.start_migration()
