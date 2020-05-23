import dotenv

dotenv.load_dotenv("config.env")
dotenv.load_dotenv("config.local.env")

from .config import get_config, get_meta_config, get_project_home  # NOQA

__version__ = "0.1.8"
