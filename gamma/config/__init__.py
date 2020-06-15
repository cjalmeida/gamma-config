import dotenv

from .config import Config, get_config, get_meta_config, get_project_home  # NOQA

dotenv.load_dotenv("config.local.env")
dotenv.load_dotenv("config.env")


__version__ = "0.1.12"
