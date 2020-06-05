import dotenv

dotenv.load_dotenv("config.local.env")
dotenv.load_dotenv("config.env")

from .config import get_config, get_meta_config, get_project_home, Config  # NOQA

__version__ = "0.1.9"
