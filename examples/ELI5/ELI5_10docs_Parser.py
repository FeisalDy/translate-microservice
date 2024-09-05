import json
import random
import sys
sys.path.insert(0,r'./')
from tqdm.auto import tqdm

from configs import BaseConfig
from translator import DataParser
from translator import VerboseCallback
from providers import *

PARSER_NAME = "ELI5_val"


class ELI5Val(DataParser):
    def __init__(self, file_path: str, output_path: str, target_lang: str="vi",
                 max_example_per_thread=400, large_chunks_threshold=20000,
                 translator: Provider = GoogleProvider):
        super().__init__(
            file_path,
            output_path,
            parser_name=PARSER_NAME,
            target_config=BaseConfig,  # The data config to be validated to check if self implement "convert" function is correct or not,
            # you must map the data form to the correct fields of the @dataclass in the configs/base_config.py
            target_fields=[
                "question_text",
                "orig_answer_texts",
            ],  # The data fields to be translated (The fields belong to BaseConfig)
            do_translate=True,
            verbose=False, # Set to True to see extra information
            target_lang=target_lang,
            max_example_per_thread=max_example_per_thread,
            large_chunks_threshold=large_chunks_threshold,
            translator=translator,
            parser_callbacks=[VerboseCallback],
        )

        self.max_ctxs = 5

    # Read function must assign data that has been read to self.data_read
    def read(self) -> None:
        # The read function must call the read function in DataParser class
        # I just want to be sure that the file path is correct
        super(ELI5Val, self).read()

        with open(self.file_path, encoding='utf-8') as jfile:
            json_data = [json.loads(example) for example in jfile]

        self.data_read = json_data[0]
        return None

    def convert(self) -> None:
        # The convert function must call the convert function in DataParser class
        # I just want to be sure the read function has actually assigned the self.data_read
        super(ELI5Val, self).convert()

        lfqa_prefixs = [
            "\n\n Here are some relevant documents, which may or may not be applicable to the previous question. If you use this information, please indicate 'Based on the provided documents':\n",
            "\n\n Below are some pertinent documents, which may or may not relate to the previous question. If you utilize this information, kindly mention 'In reference to the provided documents':\n",
            "\n\n The following documents may or may not be relevant to the previous question. If you choose to incorporate this information, please acknowledge with 'Based on the provided documents':\n",
            "\n\n Here are some documents that could be useful for the question at hand. It's up to you whether or not to use them. If you do, please state 'Based on the documents provided':\n",
            "\n\n These documents may or may not have relevance to the previous question. If you decide to use them, kindly acknowledge with 'In reference to the provided documents':\n",
            "\n\n Here are some documents that might be of interest in relation to the previous question. If you opt to use them, please mention 'Based on the provided documents':\n",
            "\n\n The following documents may or may not pertain to the previous question. If you incorporate this information, kindly indicate 'In reference to the provided documents':\n",
            "\n\n Here are some relevant documents, which may or may not have relevance to the previous question. If you use this information, please acknowledge with 'Based on the provided documents':\n",
            "\n\n Below are some pertinent documents that may or may not be applicable to the previous question. If you choose to incorporate this information, please state 'In reference to the provided documents':\n",
            "\n\n The following documents may or may not relate to the previous question. If you decide to use them, kindly mention 'Based on the provided documents':\n",
            "\n\n Here are some documents that could be useful for the question at hand. It's up to you whether or not to use them. If you do, please acknowledge with 'In reference to the provided documents':\n",
            "\n\n These documents may or may not have relevance to the previous question. If you opt to use them, please state 'Based on the documents provided':\n",
            "\n\n Here are some documents that might be of interest in relation to the previous question. If you choose to use them, kindly indicate 'In reference to the provided documents':\n",
            "\n\n The following documents may or may not pertain to the previous question. If you incorporate this information, please acknowledge with 'Based on the provided documents':\n",
            "\n\n Here are some relevant documents, which may or may not have relevance to the previous question. If you use this information, please indicate 'In reference to the provided documents':\n",
            "\n\n Below are some pertinent documents that may or may not be applicable to the previous question. If you opt to use this information, please state 'Based on the provided documents':\n",
            "\n\n The following documents may or may not relate to the previous question. If you decide to use them, kindly mention 'In reference to the provided documents':\n",
            "\n\n Here are some documents that could be useful for the question at hand. It's up to you whether or not to use them. If you do, please acknowledge with 'Based on the documents provided':\n",
            "\n\n These documents may or may not have relevance to the previous question. If you choose to use them, please indicate 'In reference to the provided documents':\n",
            "\n\n Here are some documents that might be of interest in relation to the previous question. If you opt to use them, kindly state 'Based on the provided documents':\n",
        ]
        lfqa_system_prompts = [
            "You are an AI assistant specializing in Question Answering. Please answer the following question based on the provided documents.",
            "Incorporate the information from the documents into your response.",
            "Consider the relevance of the provided documents in your answer.",
            "Your response should take into account the information contained in the documents.",
            "Use the documents as a reference when responding to the question.",
            "Incorporate the relevant information from the provided documents.",
            "Base your response on the information presented in the documents.",
            "Make sure to address the question with the help of the provided documents.",
            "Take the information from the documents into consideration when answering.",
            "Your answer should be influenced by the information in the provided documents.",
            "Ensure that your response is informed by the contents of the documents.",
            "Integrate the information from the documents into your reply.",
            "Refer to the documents when formulating your response.",
            "Keep the information in the documents in mind when answering.",
            "The documents are there to assist you in your response.",
            "Use the information from the documents to support your answer.",
            "Your response should reflect the content of the provided documents.",
            "Take advantage of the information in the documents when answering.",
            "In your response, consider the information from the documents.",
            "The provided documents can be a valuable resource in your answer.",
            "As an AI assistant specialized in Question Answering, analyze the provided documents and answer the question accordingly.",
            "Utilize the knowledge from the documents as a Question Answering AI assistant to address the question.",
            "Based on your specialization in Question Answering, make sure to use the provided documents in your response.",
            "Your expertise as a Question Answering AI assistant should guide you in utilizing the provided documents effectively.",
            "Your role as a specialized Question Answering AI assistant makes it essential to refer to the documents in your response.",
            "",
            "",
            "",
            "",
            "",
            "",
            ""
        ]

        data_converted = []
        for data in tqdm(self.data_read, desc="Converting data"):
            data_dict = {}
            data_dict['system_prompt'] = random.choice(lfqa_system_prompts)

            data_dict['qas_id'] = data['question_id']

            docs = [ctx[0] for ctx in data['ctxs'][:self.max_ctxs]]
            lfqa_prefix = random.choice(lfqa_prefixs)
            data_dict['question_text'] = data['question'] + lfqa_prefix
            for doc in docs:
                data_dict['question_text'] += doc + "\n\n"

            data_dict['orig_answer_texts'] = data['answers'][0] if data['answers'] else None
            data_dict['answer_lengths'] = None
            data_converted.append(data_dict)

        # Be sure to assign the final data list to self.converted_data
        self.converted_data = data_converted

        return None


if __name__ == '__main__':
    eli5_val_parser = ELI5Val(r"examples/ELI5/ELI5_val_10_doc.json",
                              r"examples/ELI5",
                              max_example_per_thread=100,
                              large_chunks_threshold=1000,
                              target_lang="ko")
    eli5_val_parser.read()
    eli5_val_parser.convert()
    eli5_val_parser.save
