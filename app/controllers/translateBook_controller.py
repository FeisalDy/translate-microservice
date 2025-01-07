from tqdm.auto import tqdm
from translator import DataParser
from configs import BookConfig
# from utils.db import create_connection
from ..utils.db import create_connection


class TranslateBookController(DataParser):
    def __init__(self, file_path: str, output_directory: str, id: int, source_lang: str, target_lang: str):
        super().__init__(
            file_path=file_path,
            output_dir=output_directory,
            source_lang=source_lang,
            target_lang=target_lang,
            parser_name="BookTranslator",
            do_translate=True,
            target_config=BookConfig,
            target_fields=['title',
                           'author', 'tags', 'description'],
            max_example_length=1000,
            max_example_per_thread=50,
            large_chunks_threshold=20000,
            verbose=True,
        )
        self.id = id
        self.data_read = []
        self.converted_data = []

    def read(self):
        """Read data from the PostgreSQL database."""
        super(TranslateBookController, self).read()
        connection = create_connection()
        cursor = connection.cursor()

        cursor.execute(
            'SELECT id, title, cn_title, author, cn_author, "isCompleted", tags, cover, description FROM "Book" WHERE id = %s',
            (self.id,)
        )
        # cursor.execute(
        #     'SELECT id, title, cn_title, author, cn_author, "isCompleted", tags, cover, description FROM "Book"',
        # )
        rows = cursor.fetchall()

        self.data_read = [
            {"id": row[0], "title": row[1], "cn_title": row[2], "author": row[3], "cn_author": row[4],
                "isCompleted": row[5], "tags": row[6], "cover": row[7], "description": row[8]}
            for row in rows
        ]

        connection.close()

    def convert(self):
        """Translate the content field."""
        super(TranslateBookController, self).convert()

        data_converted = []
        for record in tqdm(self.data_read, desc="Translating books"):

            data_converted.append({
                "qas_id": self.id_generator(),
                "id": record["id"],
                "title": record["title"],
                "cn_title": record["title"],
                "author": record["author"],
                "cn_author": record["author"],
                "isCompleted": record["isCompleted"],
                "tags": record["tags"],
                "cover": record["cover"],
                "description": record["description"],
            })

        self.converted_data = data_converted

    def custom_save(self):
        """Save the translated content into a new SQLite database."""
        connection = create_connection()
        cursor = connection.cursor()
        for record in self.converted_data:
            cursor.execute(
                'UPDATE "Book" SET title = %s, cn_title= %s, author = %s, cn_author = %s, tags = %s, description = %s WHERE id = %s',
                (record["title"], record["cn_title"], record["author"], record["cn_author"], record["tags"],
                 record["description"], record["id"])
            )

        connection.commit()
        connection.close()
