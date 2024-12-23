from .filters import have_code, have_re_code
from .utils import (
    force_super_call,
    ForceBaseCallMeta,
    no_args_method,
    timeit,
    have_internet,
    safe_tqdm_write
)
from .callbacks import *
from configs import *
from providers import *
from concurrent.futures import ThreadPoolExecutor
from tqdm.auto import tqdm
from abc import abstractmethod
from typing import List, Dict, Union
from httpcore._exceptions import ConnectTimeout
import traceback
import warnings
import threading
from copy import deepcopy
import math
import re
import json
import os
import random
import string
import sys
sys.path.insert(0, r'./')

try:
    from google.colab import files
    IN_COLAB = True
except ImportError:
    IN_COLAB = False


if not have_internet(timeout=5):
    raise ConnectTimeout(
        "Please provide internet connection as this script require external api calls")


class DataParser(metaclass=ForceBaseCallMeta):
    def __init__(self, file_path: str,
                 output_dir: str,
                 parser_name: str,
                 target_config: Config,
                 verbose: bool = False,
                 target_fields: List[str] = None,
                 do_translate: bool = False,
                 # Enable splitting a large list into sublist if a list of one example is too large to process
                 enable_sub_task_thread: bool = True,
                 # This argument go with max_list_length_per_thread
                 no_translated_code: bool = False,
                 max_example_per_thread: int = 400,  # How many examples, each thread can contain
                 # Maximum number of examples that will be distributed evenly across threads, any examples exceed this threshold will be process in queue
                 large_chunks_threshold: int = 20000,
                 # Maximum number of strings contain in a list in a single thread.
                 max_list_length_per_thread: int = 3,
                 # if larger, split the list into sub-list and process in parallel
                 # Maximum string length in a single example, if exceed, truncate the string
                 max_example_length: int = 15000,
                 # Average string length in a list, if exceed, split the list into sub-list and process in parallel
                 average_string_length_in_list: int = 1600,
                 translator: Provider = GoogleProvider,
                 source_lang: str = "en",
                 target_lang: str = "vi",
                 # Fail code for *expected* fail translation and can be removed
                 fail_translation_code: str = "P1OP1_F",
                 # post-translation,
                 # Callback function to be called after each step of the parser
                 parser_callbacks: List[ParserCallback] = None
                 ) -> None:
        """
        Initializes the DataParser object.
        Args:
            file_path (str): The path to the file.
            output_dir (str): The output directory.
            parser_name (str): The name of the parser.
            target_config (Config): The target configuration.
            verbose (bool, optional): Whether to enable verbose mode. Defaults to False.
            target_fields (List[str], optional): The target fields to be translated. Defaults to None.
            do_translate (bool, optional): Whether to perform translation. Defaults to False.
            enable_sub_task_thread (bool, optional): Whether to enable sub-task threading. Defaults to True.
            no_translated_code (bool, optional): Whether to exclude translated code. Defaults to False.
            max_example_per_thread (int, optional): The maximum number of examples per thread. Defaults to 400.
            large_chunks_threshold (int, optional): The maximum number of examples for large chunks. Defaults to 20000.
            max_list_length_per_thread (int, optional): The maximum number of strings in a list per thread. Defaults to 3.
            max_example_length (int, optional): The maximum string length in a single example. Defaults to 15000.
            average_string_length_in_list (int, optional): The average string length in a list. Defaults to 1600.
            translator (Provider, optional): The translation provider. Defaults to GoogleProvider.
            source_lang (str, optional): The source language. Defaults to "en".
            target_lang (str, optional): The target language. Defaults to "vi".
            fail_translation_code (str, optional): The fail code for expected fail translation. Defaults to "P1OP1_F".
            parser_callbacks (List[ParserCallback], optional): The callback function to be called after each step of the parser. Defaults to None.
        """
        self.parser_name = parser_name
        self.parser_callbacks = parser_callbacks
        if self.parser_callbacks:
            if not isinstance(self.parser_callbacks, list):
                self.parser_callbacks = [self.parser_callbacks]
            print(
                f"Parser {self.parser_name} has {len(self.parser_callbacks)} callbacks")
            self.parser_callbacks = [callback()
                                     for callback in self.parser_callbacks]
            for callback in self.parser_callbacks:
                assert isinstance(
                    callback, ParserCallback), "Please provide a valid callback function!"
                callback.on_start_init(self)

        self.data_read = None
        self.converted_data = None
        self.file_path = file_path
        self.output_dir = output_dir
        assert os.path.isdir(
            self.output_dir), "Please provide the correct output directory"

        assert target_config, "Please specified the target config (Choose from the configs dir)"
        self.target_config = target_config
        self.do_translate = do_translate

        self.verbose = verbose

        if self.do_translate:
            self.fail_translation_code = fail_translation_code
            self.enable_sub_task_thread = enable_sub_task_thread
            self.max_example_length = max_example_length
            self.source_lang = source_lang
            self.target_lang = target_lang
            assert target_fields, f"Please specified target fields to be translate from the {self.target_config} config"
            self.target_fields = target_fields
            assert set(self.target_fields).issubset(set(self.target_config.get_keys())), \
                f"The target fields {self.target_fields} do not exist in the target config {self.target_config.get_keys()}"

            # target_fields value can only be string or list of string
            target_type_hints = self.target_config.__annotations__
            for key in self.target_fields:
                assert target_type_hints[key] in [str, List[str], list], \
                    f"Invalid target field type to be translated, the field {key} must be either string or list of string, but got {target_type_hints[key].__name__}"

            self.no_translated_code = no_translated_code
            assert max_example_per_thread < large_chunks_threshold, \
                " Large chunks threshold can't be smaller than max_example per thread!"
            self.max_example_per_thread = max_example_per_thread
            self.large_chunks_threshold = large_chunks_threshold
            if self.enable_sub_task_thread:
                self.max_list_length_per_thread = max_list_length_per_thread
                self.average_string_length_in_list = average_string_length_in_list

            self.converted_data_translated = None

            self.translator = translator

        if self.parser_callbacks:
            for callback in self.parser_callbacks:
                callback.on_finish_init(self)

    @property
    def get_translator(self) -> Provider:
        """
        Returns a deep copy of the translator object.

        Returns:
            Provider: A deep copy of the translator object.
        """
        return deepcopy(self.translator)()

    @staticmethod
    def id_generator(size: int = 6, chars: str = string.ascii_uppercase + string.digits) -> str:
        """
        Generate a random string of specified size using the given characters.

        Parameters:
        - size (int): The length of the generated string. Default is 6.
        - chars (str): The characters to be used for generating the string. Default is a combination of uppercase letters and digits.

        Returns:
        - str: The randomly generated string.
        """
        return ''.join(random.choice(chars) for _ in range(size))

    @staticmethod
    def split_list(input_list: List[str], max_sub_length: int) -> List[list]:
        """
        Splits a list into sublists of a maximum specified length.

        Args:
            input_list (List[str]): The input list to be split.
            max_sub_length (int): The maximum length of each sublist.

        Returns:
            List[list]: A list of sublists, where each sublist has a maximum length of max_sub_length.
        """
        return [input_list[x:x + max_sub_length] for x in range(0, len(input_list), max_sub_length)]

    @staticmethod
    def flatten_list(nested_list: List) -> List:
        """
        Turn a list from [[], [], []] -> []
        """

        flattened_list = []
        for item in nested_list:
            if isinstance(item, list):
                flattened_list.extend(DataParser.flatten_list(item))
            else:
                flattened_list.append(item)
        return flattened_list

    def validate(self, keys: List[str]) -> bool:
        dict_fields = self.target_config.get_keys()
        for key in dict_fields:
            assert key in keys, f"\n Invalid parser, the key '{key}' is missing from {dict_fields}\n" \
                                f"you can adjust the fields {self.target_config.__name__} in the 'configs/*.py'" \
                                f"  or fill in the missing field."
        return True

    @timeit
    def pre_translate_validate(self) -> None:
        validated_translate_data = []
        # Note: This validates will override the original self.converted_data
        for idx, example in enumerate(tqdm(self.converted_data, desc="Validating data for translation:")):
            for key in self.target_fields:
                if self.no_translated_code:
                    example_filters = 0
                    contain_code, score, found_elements = have_code(
                        example[key])
                    if contain_code:
                        example_filters += 1
                        if len(self.converted_data) - 2 == idx:
                            safe_tqdm_write(
                                f"Number of example with code: {example_filters}")
                        break
                    elif key == self.target_fields[-1]:
                        validated_translate_data.append(example)
                else:
                    if key == self.target_fields[-1]:
                        validated_translate_data.append(example)

        safe_tqdm_write(
            f"\nTotal data left after filtering for translation: {len(validated_translate_data)}\n")
        self.converted_data = validated_translate_data

    @timeit
    def post_translate_validate(self) -> None:
        post_validated_translate_data = []
        # Note: This validates will override the original self.converted_data_translated
        for idx, example in enumerate(tqdm(self.converted_data_translated, desc="Validating data after translation:")):
            for key in self.target_fields:
                example_filters = 0
                if have_re_code(example[key], code=self.fail_translation_code):
                    example_filters += 1
                    if len(self.converted_data_translated) - 2 == idx:
                        safe_tqdm_write(
                            f"Number of example with fail code: {example_filters}")
                    break
                elif key == self.target_fields[-1]:
                    post_validated_translate_data.append(example)

        safe_tqdm_write(
            f"\nTotal data left after filtering fail translation: {len(post_validated_translate_data)}\n")
        self.converted_data_translated = post_validated_translate_data

    # def __translate_per_key(self, example: Dict, translator: Provider = None, progress_idx: int = 0) -> Dict:
    #     """
    #     This function loop through each key of one example and send to __translate_texts if the value of the key is
    #     under a certain threshold. If exceeded, then send to __sublist_multithread_translate
    #     """

    #     assert self.do_translate, "Please enable translate via self.do_translate"
    #     keys = self.target_config.get_keys()
    #     for key in keys:
    #         if key in self.target_fields:
    #             type = "str" if isinstance(example[key], str) else "list"
    #             if example[key] == "" or example[key] is None:
    #                 continue
    #             if type == "list":
    #                 for data in example[key]:
    #                     if len(data) > self.max_example_length:
    #                         warnings.warn(
    #                             f"Example" + example["qas_id"] + " have field len larger than {self.max_example_length}, truncating...")
    #                         example[key].append(data[:self.max_example_length])
    #             else:
    #                 if len(example[key]) > self.max_example_length:
    #                     warnings.warn(
    #                         f"Example" + example["qas_id"] + " have field len larger than {self.max_example_length}, truncating...")
    #                     example[key] = example[key][:self.max_example_length]

    #             if self.enable_sub_task_thread:
    #                 average_length_sub_task_criteria = False
    #                 if type == "list":
    #                     average_length = sum(
    #                         len(lst) for lst in example[key]) / len(example[key])
    #                     if average_length > self.average_string_length_in_list:
    #                         average_length_sub_task_criteria = True
    #                 if type == "list" and average_length_sub_task_criteria and len(example[key]) >= self.max_list_length_per_thread:
    #                     if self.verbose:
    #                         safe_tqdm_write(
    #                             f"\nSplitting {key} field which contain {len(example[key])} items on chunk {progress_idx}\n")
    #                     example[key] = self.__sublist_multithread_translate(example[key],
    #                                                                         progress_idx,
    #                                                                         key)
    #                 else:
    #                     if self.verbose:
    #                         safe_tqdm_write(
    #                             f"\nTranslating {key} field which contain string of length {len(example[key])} on chunk {progress_idx}\n")
    #                     example[key] = self.__translate_texts(
    #                         src_texts=example[key], translator=translator)
    #             else:
    #                 example[key] = self.__translate_texts(
    #                     src_texts=example[key], translator=translator)

    #     return example

    def __translate_per_key(self, example: Dict, translator: Provider = None, progress_idx: int = 0) -> Dict:
        """
        This function loops through each key of one example and sends to __translate_texts if the value of the key is
        under a certain threshold. If exceeded, then send to __sublist_multithread_translate.
        """
        assert self.do_translate, "Please enable translate via self.do_translate"
        keys = self.target_config.get_keys()

        for key in keys:
            if key in self.target_fields:
                type = "str" if isinstance(example[key], str) else "list"
                if example[key] == "" or example[key] is None:
                    continue

                # Handle string type
                if type == "str":
                    if len(example[key]) > self.max_example_length:
                        warnings.warn(
                            f"Example {example['qas_id']} has field length larger than {self.max_example_length}, truncating...")

                        # Split the string into chunks
                        chunks = [example[key][i:i + self.max_example_length]
                                  for i in range(0, len(example[key]), self.max_example_length)]

                        # Translate each chunk
                        translated_chunks = [self.__translate_texts(
                            chunk, translator) for chunk in chunks]

                        # Combine the translated chunks
                        example[key] = ''.join(translated_chunks)
                    else:
                        # If the string is within the limit, translate normally
                        example[key] = self.__translate_texts(
                            example[key], translator)

                # Handle list type
                elif type == "list":
                    for idx, data in enumerate(example[key]):
                        if len(data) > self.max_example_length:
                            warnings.warn(
                                f"Example {example['qas_id']} has field length larger than {self.max_example_length}, truncating...")

                            # Split the string into chunks
                            chunks = [data[i:i + self.max_example_length]
                                      for i in range(0, len(data), self.max_example_length)]

                            # Translate each chunk
                            translated_chunks = [self.__translate_texts(
                                chunk, translator) for chunk in chunks]

                            # Combine the translated chunks
                            example[key][idx] = ''.join(translated_chunks)
                        else:
                            # If the string is within the limit, translate normally
                            example[key][idx] = self.__translate_texts(
                                data, translator)

        return example

    def __sublist_multithread_translate(self,
                                        list_str: List[str],
                                        progress_idx: int = 0,
                                        # The field name (key name) of one example that exceed a certain threshold and needed to be split and translate in parallel
                                        field_name: str = None
                                        ) -> List[str]:
        """
        This function split a large list into sub-list and translate it in parallel, orders are maintained when merge all
        sub-lists, this is useful when order are necessary (e.g Dialogs example)
        """

        translated_list_data = []
        num_threads = len(list_str) / self.max_list_length_per_thread
        sub_str_lists = self.split_list(
            list_str, max_sub_length=self.max_list_length_per_thread)
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            finished_task = 0
            lock = threading.RLock()

            def callback_sub_list_done(future):
                nonlocal translated_list_data
                nonlocal finished_task
                nonlocal lock
                if not future.exception():
                    with lock:
                        # This need to be .append to keep the list structure
                        # Since this deal with sub-list and needed to be merged later
                        translated_list_data.append(future.result())
                        finished_task += 1
                else:
                    safe_tqdm_write(f"Sub task of chunk {progress_idx} with field {field_name} failed with the following error: {future.exception()}."
                                    f"Restarting thread when others finished...")
                    if self.verbose:
                        safe_tqdm_write(
                            f"Error traceback: {traceback.format_exc()}")
                    if self.parser_callbacks:
                        for callback in self.parser_callbacks:
                            callback.on_error_translate(
                                self, future.exception())
                pass

            for idx, list_chunk in enumerate(sub_str_lists):
                # Assign each thread with a new Translator instance
                future_chunk = executor.submit(self.__translate_texts,
                                               src_texts=list_chunk,
                                               translator=self.get_translator,
                                               sub_list_idx=idx)
                future_chunk.add_done_callback(callback_sub_list_done)
                future_dict = {
                    "future": future_chunk,
                    "idx": idx
                }
                futures.append(future_dict)

            # Wait for all threads to complete
            while finished_task < len(futures):
                for future_dict in futures:
                    # If exception occurs in one of the thread, restart the thread with its specific chunk
                    if future_dict['future'].exception():
                        safe_tqdm_write(
                            f"Thread {future_dict['idx']} failed, restarting thread with chunk {future_dict['idx']}")
                        backup_future_chunk = executor.submit(self.__translate_texts,
                                                              src_texts=sub_str_lists[future_dict['idx']],
                                                              translator=self.get_translator,
                                                              sub_list_idx=future_dict['idx'])
                        backup_future_chunk.add_done_callback(
                            callback_sub_list_done)
                        backup_future_dict = {"future": backup_future_chunk,
                                              "idx": future_dict['idx']}
                        futures[future_dict['idx']] = backup_future_dict
                        continue

            # Sorting the list of dictionaries based on the 'key' value
            translated_list_data = sorted(
                translated_list_data, key=lambda x: x['key'])
            # Extracting values after sorting
            translated_list_data = [item['text_list']
                                    for item in translated_list_data]
            translated_list_data = self.flatten_list(translated_list_data)

            return translated_list_data

    def __translate_texts(self,
                          src_texts: Union[List[str], str],
                          translator: Provider = None,
                          # sub_list_idx is for pass through of index information and can be merge later by __sublist_multithread_translate
                          sub_list_idx: int = None,
                          ) -> Union[List[str], str, Dict[List[str], int]]:
        """
        Actual place where translation take place
        """

        list_bypass = False
        if type(src_texts) == list:
            if len(src_texts) == 1:
                src_texts = src_texts[0]
                list_bypass = True
                if self.verbose:
                    safe_tqdm_write(
                        f"List contain only one element, extract the element and translate...")
            if len(src_texts) == 0:
                if self.verbose:
                    safe_tqdm_write(f"Empty list, skipping...")
                return src_texts
        else:
            if len(src_texts) == 0:
                if self.verbose:
                    safe_tqdm_write(f"Empty string, skipping...")
                return src_texts

        assert self.do_translate, "Please enable translate via self.do_translate"
        # This if is for multithread Translator instance
        translator_instance = deepcopy(
            self.translator)() if translator is None else translator

        target_texts = translator_instance.translate(src_texts,
                                                     src=self.source_lang,
                                                     dest=self.target_lang,
                                                     fail_translation_code=self.fail_translation_code)
        if list_bypass:
            target_texts = [target_texts]

        return {'text_list': target_texts, 'key': sub_list_idx} if sub_list_idx is not None else target_texts

    def translate_converted(self,
                            en_data: List[str] = None,
                            desc: str = None,
                            translator: Provider = None,
                            large_chunk: List[str] = None) -> Union[None, List[str]]:
        """
        This function support translation in multithread for large dataset
        (Does not maintain order for the final dataset)
        """

        assert self.converted_data is not None or en_data is not None or large_chunk is not None, \
            "Please implement the convert function for DataParser " \
            "and assign converted_data to self.converted_data"

        if not en_data and not large_chunk:
            converted_data = self.converted_data
        elif not en_data:
            converted_data = large_chunk
        else:
            converted_data = en_data

        translated_data = []

        # Split large data into large chunks, recursive feed to the same function
        if len(converted_data) > self.large_chunks_threshold and large_chunk is None:
            num_large_chunks = len(converted_data) / \
                self.large_chunks_threshold
            large_chunks = self.split_list(
                converted_data, max_sub_length=self.large_chunks_threshold)
            safe_tqdm_write(
                f"Data is way too large, spliting data into {num_large_chunks} large chunk for sequential translation")

            # Main thread progress bar
            for idx, large_chunk in enumerate(tqdm(large_chunks, desc=f"Translating large chunk ", colour="red")):
                safe_tqdm_write(f"Processing large chunk No: {idx}")
                self.translate_converted(large_chunk=large_chunk)
            return None

        # Split large chunk into large example, recursive feed to the same function via multithread
        if len(converted_data) > self.max_example_per_thread and en_data is None:
            num_threads = len(converted_data) / self.max_example_per_thread
            chunks = self.split_list(
                converted_data, max_sub_length=self.max_example_per_thread)
            safe_tqdm_write(f"Data too large, splitting data into {num_threads} chunk, each chunk is {len(chunks[0])}"
                            f" Processing with multithread...")

            # Progress bar
            desc = "Translating total converted large chunk data" if large_chunk else "Translating total converted data"
            progress_bar = tqdm(total=math.ceil(
                num_threads), desc=desc, position=math.ceil(num_threads)+1, leave=False)

            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = []
                finished_task = 0
                # https://stackoverflow.com/questions/22885775/what-is-the-difference-between-lock-and-rlock#22885810
                lock = threading.RLock()

                def callback_done(future):
                    nonlocal translated_data
                    nonlocal finished_task
                    nonlocal progress_bar
                    nonlocal lock
                    if not future.exception():
                        with lock:
                            # This need to be += or .extend to shallow flatten the list structure
                            translated_data += future.result()
                            finished_task += 1
                            progress_bar.update(1)
                    else:
                        safe_tqdm_write(f"Task failed with the following error: {future.exception()}."
                                        f" Restarting thread when others finished")
                        if self.verbose:
                            safe_tqdm_write(
                                f"Error traceback: {traceback.format_exc()}")
                        if self.parser_callbacks:
                            for callback in self.parser_callbacks:
                                callback.on_error_translate(
                                    self, future.exception())

                        pass

                for idx, chunk in enumerate(chunks):
                    # Assign each thread with a new Translator instance
                    future_chunk = executor.submit(self.translate_converted,
                                                   en_data=chunk,
                                                   desc=f"chunk {idx}",
                                                   translator=self.get_translator)
                    future_chunk.add_done_callback(callback_done)
                    future_dict = {"future": future_chunk,
                                   "idx": idx}
                    futures.append(future_dict)

                # Wait for all threads to complete
                while finished_task < len(futures):
                    for future_dict in futures:
                        # If exception occurs in one of the thread, restart the thread with its specific chunk
                        if future_dict['future'].exception():
                            safe_tqdm_write(
                                f"Thread {future_dict['idx']} failed, restarting thread with chunk {future_dict['idx']}")
                            backup_future_chunk = executor.submit(self.translate_converted,
                                                                  en_data=chunks[future_dict['idx']],
                                                                  desc=f"Backup chunk {future_dict['idx']}",
                                                                  translator=self.get_translator)
                            backup_future_chunk.add_done_callback(
                                callback_done)
                            backup_future_dict = {"future": backup_future_chunk,
                                                  "idx": future_dict['idx']}
                            futures[future_dict['idx']] = backup_future_dict
                            continue

            if large_chunk:
                if not self.converted_data_translated:
                    self.converted_data_translated = translated_data
                else:
                    self.converted_data_translated += translated_data
                return None

            self.converted_data_translated = translated_data
            return None

        progress_bar_desc = "Translating converted data" if not desc else f"Translating converted data {desc}"
        for example in tqdm(converted_data, desc=progress_bar_desc, colour="#add8e6", leave=False):
            translated_data_example = self.__translate_per_key(example,
                                                               translator,
                                                               progress_idx=int(re.findall(r'\d+', desc)[0]) if desc and re.findall(r'\d+', desc) else 0)
            translated_data.append(translated_data_example)
        if en_data:
            return translated_data
        if large_chunk:
            # Assuming that the previous large chunk process already create self.converted_data_translated
            # This cover the case where last large chunk only contain a single thread
            self.converted_data_translated += translated_data
        else:
            self.converted_data_translated = translated_data

    @abstractmethod
    @force_super_call
    def convert(self) -> Union[List[Dict], None]:
        assert self.data_read is not None, "Please implement the read function for DataParser" \
                                           " and assign data to self.data_read"
        if self.parser_callbacks:
            for callback in self.parser_callbacks:
                callback.on_start_convert(self)
        pass

    @abstractmethod
    @force_super_call
    def read(self) -> Union[List, Dict, None]:
        assert os.path.isfile(
            self.file_path), f"Invalid path file for {self.file_path}"

        if self.parser_callbacks:
            for callback in self.parser_callbacks:
                callback.on_start_read(self)
        pass

    @no_args_method
    @timeit
    def save(self) -> None:
        """
        Save the correct format that pyarrow supported, which is "line-delimited JSON" and can be load by
        huggingface-datasets load_datasets function
        """

        if self.parser_callbacks:
            for callback in self.parser_callbacks:
                callback.on_finish_convert(self)

            for callback in self.parser_callbacks:
                callback.on_start_save_converted(self)

        output_path = os.path.join(self.output_dir, f"{self.parser_name}.json")
        with open(output_path, 'w', encoding='utf-8') as jfile:
            print(f"\n Saving {self.parser_name} to {output_path}... ")
            for idx, data in enumerate(tqdm(self.converted_data, desc="Writing data to file")):
                if self.validate(self.converted_data[idx].keys()):
                    jfile.write(json.dumps(data, ensure_ascii=False) + "\n")
            print(f"\n Total line printed: {idx + 1}")

        if self.parser_callbacks:
            for callback in self.parser_callbacks:
                callback.on_finish_save_converted(self)

        if IN_COLAB:
            print(f"\n Downloading converted data to local machine...")
            files.download(output_path)

        if self.do_translate:
            if self.parser_callbacks:
                for callback in self.parser_callbacks:
                    callback.on_start_translate(self)

            self.pre_translate_validate()
            self.translate_converted()
            self.post_translate_validate()
            assert self.converted_data_translated is not None, "Converted data haven't been translated yet!"

            if self.parser_callbacks:
                for callback in self.parser_callbacks:
                    callback.on_finish_translate(self)

                for callback in self.parser_callbacks:
                    callback.on_start_save_translated(self)

            # for idx, data in enumerate(tqdm(self.converted_data_translated, desc="Writing translated data to file")):
            #     print(data)
            # output_translated_path = os.path.join(self.output_dir,
            #                                       f"{self.parser_name}_translated_{self.target_lang}.json")
            # with open(output_translated_path, 'w', encoding='utf-8') as jfile:
            #     print(f"\n Saving {self.parser_name} translated to {output_translated_path}... ")
            #     for idx, data in enumerate(
            #             tqdm(self.converted_data_translated, desc="Writing translated data to file")):
            #         jfile.write(json.dumps(data, ensure_ascii=False) + "\n")
            #     print(f"\n Total line printed: {idx + 1}")

            # if self.parser_callbacks:
            #     for callback in self.parser_callbacks:
            #         callback.on_finish_save_translated(self)

            # if IN_COLAB:
            #     print(f"\n Downloading converted translated data to local machine...")
            #     files.download(output_translated_path)
