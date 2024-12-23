# fmt: off
import sys
sys.path.insert(0,r'./')
from tqdm.auto import tqdm
from translator import DataParser
from tqdm.auto import tqdm
import psycopg2
from configs import ChapterConfig

class TranslateChapter(DataParser):
    def __init__(self, file_path: str, output_directory: str,bookId: int, source_lang: str, target_lang: str,) -> None:
        super().__init__(file_path, output_directory, source_lang, target_lang,
                         parser_name="ChapterTranslator",
                         do_translate=True,
                         target_config=ChapterConfig,
                        #  source_lang="zh-CN",
                        #  target_lang="en",
                         target_fields=['chapterTitle', 'content'],                                
                        #  target_fields=['content'],
                         max_example_length=1000,
                         max_example_per_thread=50,
                         large_chunks_threshold=20000,
                        #  average_string_length_in_list=5000,
                         verbose=True,
                        )
        self.bookId = bookId
        self.output_directory = output_directory
        self.input_db_path = input_db_path
        self.data_read = []
        self.converted_data = []

    def read(self) -> None:
        """Read data from the SQLite database."""
        super(TranslateChapter, self).read()
        connection = psycopg2.connect(database="novel-postgres", user="postgres", password="admin", host="localhost", port="5432")
        cursor = connection.cursor()

        # cursor.execute(f"SELECT id, chapterTitle, content FROM Chapter where bookId = {self.bookId} ORDER BY id LIMIT 10")
        cursor.execute(
        'SELECT id, "bookId", "chapterNumber", "chapterTitle", content FROM "Chapter" WHERE "bookId" = %s ORDER BY id',
        (self.bookId,)
        )
        rows = cursor.fetchall()
        self.data_read = [{"id": row[0], "bookId": row[1], "chapterNumber": row[2], "chapterTitle": row[3], "content": row[4]} for row in rows]

        connection.close()

    def convert(self) -> None:
        """Translate the content field."""
        super(TranslateChapter, self).convert()

        data_converted = []
        for record in tqdm(self.data_read, desc="Translating chapters"):
            data_dict = {}
            data_dict['qas_id'] = self.id_generator()
            data_dict['id'] = record["id"]
            data_dict['bookId'] = record["bookId"]
            data_dict['chapterNumber'] = record["chapterNumber"]
            data_dict['chapterTitle'] = record["chapterTitle"]
            data_dict['content'] = record["content"]
            data_converted.append(data_dict)

        self.converted_data = data_converted

    # def test(self):
    #     for i in range(3):
    #         print(self.converted_data[i])

    def custom_save(self):
        """Save the translated content into a new SQLite database."""
        connection = psycopg2.connect(database="novel-postgres", user="postgres", password="admin", host="localhost", port="5432")
        cursor = connection.cursor()


        for record in tqdm(self.converted_data_translated, desc="Updating translated content"):
            cursor.execute(f"""
            UPDATE "Chapter"
            SET "chapterTitle" = %s, "content" = %s
            WHERE "id" = %s
        """, (record['chapterTitle'], record["content"], record["id"]))


        connection.commit()
        connection.close()


if __name__ == "__main__":

    input_db_path = r"C:\Users\feisa\OneDrive\Desktop\App\1.serious\Large_dataset_translator\examples\yousuu\1000row-yousuu.db"
    output_directory = r"C:\Users\feisa\OneDrive\Desktop\App\1.serious\Large_dataset_translator\examples\yousuu"
    # Initialize and process the translator
    chapter_translator = TranslateChapter( input_db_path, output_directory, bookId=5, source_lang="zh-CN", target_lang="en")
    chapter_translator.read()
    chapter_translator.convert()
    chapter_translator.save
    # chapter_translator.test()
    chapter_translator.custom_save()

    print("Translation complete. The output database is saved in the output directory.")
