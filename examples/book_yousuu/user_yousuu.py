# fmt: off
import sys
sys.path.insert(0,r'./')
from tqdm.auto import tqdm

from translator import DataParser
from tqdm.auto import tqdm
import sqlite3
from configs import UserConfig
import os

class TranslateUser(DataParser):
    def __init__(self, file_path: str, output_directory: str, table_name: str):
        super().__init__(file_path, output_directory,
                         parser_name="BookTranslator",
                         do_translate=True,
                         target_config=UserConfig,
                         source_lang="zh-CN",  # Source language
                         target_lang="en",  # Target language
                         target_fields=["userName"],  # Field to be translated
                         max_example_length=50000,  # Maximum length of the input text
                         large_chunks_threshold=40000,
                         verbose=True)
        self.table_name = table_name
        self.data_read = []
        self.converted_data = []
        self.output_directory = output_directory
        self.input_db_path = input_db_path

    def read(self) -> None:
        """Read data from the SQLite database."""
        super(TranslateUser, self).read()
        connection = sqlite3.connect(self.file_path)
        cursor = connection.cursor()

        cursor.execute(f"SELECT id, userName FROM {self.table_name} ORDER BY id DESC limit 50000 offset 40000")

        rows = cursor.fetchall()
        self.data_read = [{"id": row[0], "userName": row[1]} for row in rows]

        connection.close()

    def convert(self) -> None:
        """Translate the content field."""
        super(TranslateUser, self).convert()

        data_converted = []
        for record in tqdm(self.data_read, desc="Translating books"):
            data_dict = {}
            data_dict['id'] = record["id"]
            data_dict['userName'] = record["userName"]
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
            CREATE TABLE IF NOT EXISTS {self.table_name} (id INTEGER, avatarId TEXT, userName TEXT)
        """)

        # Update the `content` field with translated data
        for record in tqdm(self.converted_data_translated, desc="Updating translated userName"):
            cursor.execute(f"""
                UPDATE {self.table_name}
                SET userName = ?
                WHERE id = ?
            """, (record["userName"], record["id"]))

        connection.commit()
        connection.close()


if __name__ == "__main__":
    # Define the input SQLite database and output path
    input_db_path = r"C:\Users\feisa\OneDrive\Desktop\App\1.serious\Large_dataset_translator\examples\book_yousuu\yousuu.db"
    output_directory = r"C:\Users\feisa\OneDrive\Desktop\App\1.serious\Large_dataset_translator\examples\book_yousuu"

    # Initialize and process the translator
    book_translator = TranslateUser(
        input_db_path, output_directory, table_name="users")
    book_translator.read()
    book_translator.convert()
    # book_translator.test()
    book_translator.save
    book_translator.custom_save()

    print("Translation complete. The output database is saved in the output directory.")
