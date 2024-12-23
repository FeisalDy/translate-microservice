# fmt: off
import sys
sys.path.insert(0,r'./')
from tqdm.auto import tqdm

from translator import DataParser
from tqdm.auto import tqdm
import sqlite3
from configs import BookConfig
import os

class TranslateBook(DataParser):
    def __init__(self, file_path: str, output_directory: str, table_name: str):
        super().__init__(file_path, output_directory,
                         parser_name="BookTranslator",
                         do_translate=True,
                         target_config=BookConfig,
                         source_lang="zh-CN",  # Source language
                         target_lang="en",  # Target language
                         target_fields=["tags", "title", "author"],  # Field to be translated
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
        super(TranslateBook, self).read()
        connection = sqlite3.connect(self.file_path)
        cursor = connection.cursor()

        cursor.execute(f"SELECT bookId, tags, title, author FROM {self.table_name} ORDER BY bookId DESC")

        rows = cursor.fetchall()
        self.data_read = [{"bookId": row[0], "tags": row[1], 'title': row[2], 'author': row[3]} for row in rows]

        connection.close()

    def convert(self) -> None:
        """Translate the content field."""
        super(TranslateBook, self).convert()

        data_converted = []
        for record in tqdm(self.data_read, desc="Translating books"):
            data_dict = {}
            data_dict['bookId'] = record["bookId"]
            data_dict['tags'] = record["tags"]
            data_dict['title'] = record["title"]
            data_dict['author'] = record["author"]
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
            CREATE TABLE IF NOT EXISTS {self.table_name} (bookId INTEGER PRIMARY KEY UNIQUE, status INTEGER, tags TEXT, score REAL, scorerCount INTEGER, title TEXT, countWord INTEGER, author TEXT, cover TEXT, updateAt TEXT, caseId INTEGER)
        """)

        # Add the `en_title` column if it doesn't already exist
        cursor.execute("PRAGMA table_info(books);")
        columns = [col[1] for col in cursor.fetchall()]
        if "en_title" not in columns:
            cursor.execute("ALTER TABLE books ADD COLUMN en_title TEXT;")


        # Update the `content` field with translated data
        for record in tqdm(self.converted_data_translated, desc="Updating translated content"):
            cursor.execute(f"""
                UPDATE {self.table_name}
                SET tags = ?, author = ?, en_title = ?
                WHERE bookId = ?
            """, (record["tags"], record["author"], record["title"], record["bookId"]))

        connection.commit()
        connection.close()


if __name__ == "__main__":
    # Define the input SQLite database and output path
    input_db_path = r"C:\Users\feisa\OneDrive\Desktop\App\1.serious\Large_dataset_translator\examples\book_yousuu\yousuu.db"
    output_directory = r"C:\Users\feisa\OneDrive\Desktop\App\1.serious\Large_dataset_translator\examples\book_yousuu"

    # Initialize and process the translator
    book_translator = TranslateBook(
        input_db_path, output_directory, table_name="books")
    book_translator.read()
    book_translator.convert()
    # book_translator.test()
    book_translator.save
    book_translator.custom_save()

    print("Translation complete. The output database is saved in the output directory.")
