from abc import ABC, abstractmethod
from typing import Union, List

import memoization
memoization.suppress_warnings()
from memoization import cached, CachingAlgorithmFlag
from tenacity import (
    retry,
    stop_after_delay,
    stop_after_attempt,
    wait_random_exponential,
)

try:
    from .utils import hash_input
except ImportError:
    from utils import hash_input


class Provider(ABC):
    """
    Base Provider that must be inherited by all Provider class, implement your own provider by inheriting this class
    """
    @abstractmethod
    def __init__(self):
        self.translator = None

    @abstractmethod
    def _do_translate(self, input_data: Union[str, List[str]], src: str, dest: str, fail_translation_code:str = "P1OP1_F", **kwargs) -> Union[str, List[str]]:
        """
        Perform translation of input data from source language to destination language.

        Args:
            input_data (Union[str, List[str]]): The input data to be translated. It can be a single string or a list of strings.
            src (str): The source language code.
            dest (str): The destination language code.
            fail_translation_code (str, optional): The code to be returned when translation fails. Defaults to "P1OP1_F".
            **kwargs: Additional keyword arguments for translation.

        Returns:
            Union[str, List[str]]: The translated output data. It can be a single string or a list of strings.
        """
        raise NotImplemented(" The function _do_translate has not been implemented.")

    def __get_hashable_key(self, input_data: Union[str, List[str]], src: str, dest: str, fail_translation_code: str="P1OP1_F") -> str:
        """
        Generate a hashable key for the input data, source language, destination language, and fail_translation_code.

        Args:
            input_data (Union[str, List[str]]): The input data to be translated. It can be a single string or a list of strings.
            src (str): The source language code.
            dest (str): The destination language code.
            fail_translation_code (str, optional): The code to be returned when translation fails. Defaults to "P1OP1_F".

        Returns:
            str: The hashable key for the input data, source language, destination language, and fail_translation_code.
        """

        return f"{src}-{dest}-{hash_input(input_data, hash=False)}-{fail_translation_code}"
    
    @cached(max_size=10000, thread_safe=False, custom_key_maker=__get_hashable_key, algorithm=CachingAlgorithmFlag.LRU)
    @retry(stop=(stop_after_attempt(6) | stop_after_delay(120)), wait=wait_random_exponential(multiplier=1, max=30), reraise=True)
    def translate(self, input_data: Union[str, List[str]], src: str, dest: str, fail_translation_code: str="P1OP1_F") -> Union[str, List[str]]:
        """
        Translates the input data from the source language to the destination language using the assigned translator object.
        Args:
            input_data (Union[str, List[str]]): The input data to be translated. It can be either a string or a list of strings.
            src (str): The source language code.
            dest (str): The destination language code.
            fail_translation_code (str, optional): The code to be returned in case of translation failure. Defaults to "P1OP1_F".
        Returns:
            Union[str, List[str]]: The translated output data. It will have the same type as the input data.
        Raises:
            TypeError: If the input_data is not of type str or List[str], or if the elements of input_data list are not of type str.
        Notes:
            - The translator object instance must be assigned to self.translator before calling this method.
            - The translation is performed by calling the _do_translate() method.
        """

        # Type check for input_data
        if not isinstance(input_data, (str, list)):
            raise TypeError(f"input_data must be of type str or List[str], not {type(input_data).__name__}")

        if isinstance(input_data, list) and not all(isinstance(item, str) for item in input_data):
            raise TypeError("All elements of input_data list must be of type str")

        # Ensure the translator is set
        assert self.translator, "Please assign the translator object instance to self.translator"

        # Perform the translation
        translated_instance = self._do_translate(input_data,
                                                 src=src,
                                                 dest=dest,
                                                 fail_translation_code=fail_translation_code)

        assert type(input_data) == type(translated_instance),\
            f" The function self._do_translate() return mismatch datatype from the input_data," \
            f" expected {type(input_data)} from self._do_translate() but got {type(translated_instance)}"

        return translated_instance


