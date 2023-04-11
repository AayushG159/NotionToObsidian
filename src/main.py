import logging_config
from migrate import Migrate
from config import Config

if __name__ == '__main__':
    config = Config()
    location, attach_folder = config.get_config()
    migrate = Migrate(location, attach_folder)
    migrate.start_migration()
