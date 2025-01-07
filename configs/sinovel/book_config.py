import pprint
from typing import Dict, List
from dataclasses import dataclass
from ..config import Config
import sys
sys.path.insert(0, r'./')


@dataclass
class BookConfig(Config):
    """
    Custom configuration for translating books data.
    """
    id: int
    title: str
    cn_title: str
    author: str
    cn_author: str
    # wordCount: int
    isCompleted: bool
    tags: List[str]
    cover: str
    description: str

    def __str__(self) -> str:
        return self.__repr__

    @property
    def __repr__(self) -> str:
        """
        Represents the configuration in string form.
        """
        # return f"ChapterConfig(id={self.id}, bookId={self.bookId}, chapterNumber={self.chapterNumber}, chapterTitle={self.chapterTitle}, content={self.content})"
        return f"BookConfig(id={self.id}, title={self.title}, cn_title={self.cn_title}, author={self.author}, cn_author={self.cn_author}, isCompleted={self.isCompleted}, tags={self.tags}, cover={self.cover}, description={self.description})"

    @property
    def get_dict(self) -> Dict:
        """
        Returns the configuration as a dictionary.
        """
        return {
            "id": self.id,
            "title": self.title,
            "cn_title": self.cn_title,
            "author": self.author,
            "cn_author": self.cn_author,
            "isCompleted": self.isCompleted,
            "tags": self.tags,
            "cover": self.cover,
            "description": self.description
        }

    @classmethod
    def get_keys(cls) -> List[str]:
        """
        Returns the list of keys expected in the configuration.
        """
        return ["id", "title", "cn_title", "author", "cn_author", "isCompleted", "tags", "cover", "description"]

    def get_dict_str(self, indent: int = 4) -> None:
        """
        Pretty prints the configuration as a dictionary.
        """
        pp = pprint.PrettyPrinter(indent=indent)
        pp.pprint(self.get_dict)

    @staticmethod
    def target_fields() -> List[str]:
        return ["title", "author", "tags", "description"]
