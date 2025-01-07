from tqdm.auto import tqdm
from translator import DataParser
from configs import ChapterConfig
from ..utils.db import create_connection


class TranslateController(DataParser):
    def __init__(self, file_path: str, output_directory: str, book_id: int, source_lang: str, target_lang: str):
        super().__init__(
            file_path=file_path,
            output_dir=output_directory,
            source_lang=source_lang,
            target_lang=target_lang,
            parser_name="ChapterTranslator",
            do_translate=True,
            target_config=ChapterConfig,
            target_fields=['chapterTitle', 'content'],
            max_example_length=1000,
            max_example_per_thread=50,
            large_chunks_threshold=20000,
            verbose=True,
        )
        self.book_id = book_id
        self.data_read = []
        self.converted_data = []

    def read(self):
        """Read data from the PostgreSQL database."""
        super(TranslateController, self).read()
        connection = create_connection()
        cursor = connection.cursor()

        print(self.book_id)

        cursor.execute(
            'SELECT id, "bookId", "chapterNumber", "chapterTitle", content FROM "Chapter" WHERE "bookId" = %s ORDER BY id',
            (self.book_id,)
        )

        rows = cursor.fetchall()
        self.data_read = [
            {"id": row[0], "bookId": row[1], "chapterNumber": row[2],
                "chapterTitle": row[3], "content": row[4]}
            for row in rows
        ]

        connection.close()

    def convert(self):
        """Translate the content field."""
        super(TranslateController, self).convert()

        data_converted = []
        for record in tqdm(self.data_read, desc="Translating chapters"):
            data_converted.append({
                "qas_id": self.id_generator(),
                "id": record["id"],
                "bookId": record["bookId"],
                "chapterNumber": record["chapterNumber"],
                "chapterTitle": record["chapterTitle"],
                "content": record["content"],
            })
        self.converted_data = data_converted

    def custom_save(self):
        """Save the translated content into a new SQLite database."""
        connection = create_connection()
        cursor = connection.cursor()

        for record in tqdm(self.converted_data_translated, desc="Updating translated content"):
            cursor.execute(f"""
            UPDATE "Chapter"
            SET "chapterTitle" = %s, "content" = %s
            WHERE "id" = %s
        """, (record['chapterTitle'], record["content"], record["id"]))

        connection.commit()
        connection.close()
