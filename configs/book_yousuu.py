import pprint
from typing import Dict, List
from dataclasses import dataclass
from .config import Config
import sys
sys.path.insert(0, r'./')


@dataclass
class BookConfig(Config):
    """
    Custom configuration for translating books data.
    """
    bookId: int
    tags: str     # The content of the comment to be translated
    title: str
    author: str

    def __str__(self) -> str:
        return self.__repr__

    @property
    def __repr__(self) -> str:
        """
        Represents the configuration in string form.
        """
        return f"CustomConfig(bookId={self.bookId}, tags={self.tags}, title={self.title}, author={self.author})"

    @property
    def get_dict(self) -> Dict:
        """
        Returns the configuration as a dictionary.
        """
        return {
            "bookId": self.bookId,
            "tags": self.tags,
            "title": self.title,
            "author": self.author,
        }

    @classmethod
    def get_keys(cls) -> List[str]:
        """
        Returns the list of keys expected in the configuration.
        """
        return ["bookId", "tags", "title", "author"]

    def get_dict_str(self, indent: int = 4) -> None:
        """
        Pretty prints the configuration as a dictionary.
        """
        pp = pprint.PrettyPrinter(indent=indent)
        pp.pprint(self.get_dict)

    @staticmethod
    def target_fields() -> List[str]:
        return ["tags", "title", "author"]
