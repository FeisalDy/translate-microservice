import pprint
from typing import Dict, List
from dataclasses import dataclass
from .config import Config
import sys
sys.path.insert(0, r'./')


@dataclass
class UserConfig(Config):
    """
    Custom configuration for translating comment data.
    """
    id: int
    userName: str     # The userName of the comment to be translated

    def __str__(self) -> str:
        return self.__repr__

    @property
    def __repr__(self) -> str:
        """
        Represents the configuration in string form.
        """
        return f"UserConfig(id={self.id}, userName={self.userName})"

    @property
    def get_dict(self) -> Dict:
        """
        Returns the configuration as a dictionary.
        """
        return {
            "id": self.id,
            "userName": self.userName,
        }

    @classmethod
    def get_keys(cls) -> List[str]:
        """
        Returns the list of keys expected in the configuration.
        """
        return ["id", "userName"]

    def get_dict_str(self, indent: int = 4) -> None:
        """
        Pretty prints the configuration as a dictionary.
        """
        pp = pprint.PrettyPrinter(indent=indent)
        pp.pprint(self.get_dict)

    @staticmethod
    def target_fields() -> List[str]:
        return ["userName"]
