import dotenv

from .config import Config, get_config, get_meta_config, get_project_home  # NOQA

HOME = get_project_home()
dotenv.load_dotenv(f"{HOME}/config.local.env")
dotenv.load_dotenv(f"{HOME}/config.env")


__version__ = "0.1.12"
