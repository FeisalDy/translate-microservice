from flask import Blueprint, request, jsonify
from app.controllers.translate_controller import TranslateController
from app.controllers.translateBook_controller import TranslateBookController
translate_bp = Blueprint('translate', __name__)


@translate_bp.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        file_path = r"C:\Users\feisa\OneDrive\Desktop\App\1.serious\Large_dataset_translator\examples\yousuu\dummy.db"
        output_directory = r"C:\Users\feisa\OneDrive\Desktop\App\1.serious\Large_dataset_translator\examples\yousuu"
        book_id = data.get("bookId")
        source_lang = data.get("source_lang")
        target_lang = data.get("target_lang")

        controller = TranslateController(
            file_path, output_directory, book_id, source_lang, target_lang)
        controller.read()
        controller.convert()
        controller.save
        controller.custom_save()

        return jsonify({"status": "success", "data": "Chapters translated"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@translate_bp.route('/translate/book', methods=['POST'])
def translate_book():
    try:
        data = request.json
        file_path = r"C:\Users\feisa\OneDrive\Desktop\App\1.serious\Large_dataset_translator\examples\yousuu\dummy.db"
        output_directory = r"C:\Users\feisa\OneDrive\Desktop\App\1.serious\Large_dataset_translator\examples\yousuu"
        id = data.get("id")
        source_lang = data.get("source_lang")
        target_lang = data.get("target_lang")

        controller = TranslateBookController(
            file_path, output_directory, id, source_lang, target_lang)
        controller.read()
        controller.convert()
        controller.save
        controller.custom_save()

        return jsonify({"status": "success", "data": "Book translated"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@translate_bp.route('/test', methods=['GET'])
def test():
    return jsonify({"message": "Hello, World!"}), 200
