# fmt: off
import sys
sys.path.insert(0,r'./')
from tqdm.auto import tqdm

from translator import DataParser
from tqdm.auto import tqdm
import sqlite3
from configs import CustomConfig
import os

class TranslateComments(DataParser):
    def __init__(self, file_path: str, output_directory: str, table_name: str):
        super().__init__(file_path, output_directory,
                         parser_name="NovelTranslator",
                         do_translate=True,
                         target_config=CustomConfig,
                         source_lang="zh-CN",  # Source language
                         target_lang="en",  # Target language
                         target_fields=['chapter_title', 'content'],  # Field to be translated
                         max_example_length=100000,  # Maximum length of the input text
                         large_chunks_threshold=40000,
                         verbose=True)
        self.table_name = table_name
        self.data_read = []
        self.converted_data = []
        self.output_directory = output_directory
        self.input_db_path = input_db_path

    def read(self) -> None:
        """Read data from the SQLite database."""
        super(TranslateComments, self).read()
        connection = sqlite3.connect(self.file_path)
        cursor = connection.cursor()

        # Select all rows from the table
        #110000 to 210000
        # mulai dari 1.000.000 sampai selesai. mulai dari 900.000, 410000 to 610000
        cursor.execute(f"SELECT _id, content FROM {self.table_name} ORDER BY _id DESC LIMIT 10000 OFFSET 400000")
        # cursor.execute(f"SELECT _id, content FROM {self.table_name} ORDER BY _id DESC LIMIT 100 OFFSET 119400")

        rows = cursor.fetchall()
        self.data_read = [{"_id": row[0], "content": row[1]} for row in rows]

        connection.close()

    def convert(self) -> None:
        """Translate the content field."""
        super(TranslateComments, self).convert()

        data_converted = []
        for record in tqdm(self.data_read, desc="Translating comments"):
            data_dict = {}
            data_dict['_id'] = record["_id"]
            data_dict['content'] = record["content"]
            data_converted.append(data_dict)

        self.converted_data = data_converted

    def test(self):
        for i in range(10):
            print(self.converted_data[i])

    def custom_save(self):
        """Save the translated content into a new SQLite database."""
        output_db_path = os.path.join(self.file_path)
        connection = sqlite3.connect(output_db_path)
        cursor = connection.cursor()

        # Create a new table schema (same as the original)
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                _id TEXT UNIQUE PRIMARY KEY,
                bookId INTEGER,
                createrId INTEGER,
                content TEXT,
                createdAt TEXT,
                essence INTEGER,
                inReview INTEGER,
                jurisdiction INTEGER,
                praiseCount INTEGER,
                replyCount INTEGER,
                score INTEGER,
                shielded INTEGER,
                tags TEXT,
                updateAt TEXT,
                voting INTEGER,
                collected INTEGER,
                replyable INTEGER
            )
        """)


        # Update the `content` field with translated data
        for record in tqdm(self.converted_data_translated, desc="Updating translated content"):
            cursor.execute(f"""
                UPDATE {self.table_name}
                SET content = ?
                WHERE _id = ?
            """, (record["content"], record["_id"]))

        connection.commit()
        connection.close()


if __name__ == "__main__":
    # Define the input SQLite database and output path
    input_db_path = r"C:\Users\feisa\OneDrive\Desktop\App\1.serious\Large_dataset_translator\examples\yousuu\yousuu.db"
    output_directory = r"C:\Users\feisa\OneDrive\Desktop\App\1.serious\Large_dataset_translator\examples\yousuu"

    # Initialize and process the translator
    comments_translator = TranslateComments(
        input_db_path, output_directory, table_name="comments")
    comments_translator.read()
    comments_translator.convert()
    comments_translator.save
    comments_translator.custom_save()

    print("Translation complete. The output database is saved in the output directory.")
