# Сервис сбора изображений ключевых узлов и установок с объекта заказчика
import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
import base64


load_dotenv()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = \
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@" \
    f"{os.getenv('DB_HOST')}:5432/{os.getenv('DB_NAME')}"
db = SQLAlchemy(app)


class Images(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_name = db.Column(db.String(60))
    image = db.Column(db.LargeBinary)

    def __init__(self, image_name, image):
        self.image_name = image_name
        self.image = image


with app.app_context():
    db.create_all()


@app.route('/api/images', methods=['POST'])
def add_image():
    data = request.get_json()
    image_name = data['image_name']
    image = data['image']
    decoded_image = base64.b64decode(image)

    image = Images(image_name, decoded_image)

    try:
        db.session.add(image)
        db.session.commit()
    except SQLAlchemyError as error:
        print("Ошибка записи данных в базу данных: ", error)
        return jsonify({'error': 'Ошибка при записи данных'}), 500
    finally:
        db.session.close()

    return jsonify({'success': 'Изображение успешно сохранено'}), 201


@app.route('/api/images', methods=['GET'])
def get_images():
    data = request.get_json()
    id = data['image_id']
    images_json = []

    try:
        if id:
            image = Images.query.get(id)
            if image is None:
                return jsonify({'error': f'Изображение с id {id} не найдено'}), 404
            images_json.append(
                {'image_key': image.image_name, 'image_data': base64.b64encode(image.image).decode('utf-8')})
        else:
            images = Images.query.all()
            for image in images:
                images_json.append(
                    {'image_key': image.image_name, 'image_data': base64.b64encode(image.image).decode('utf-8')})
    except SQLAlchemyError as error:
        print("Ошибка получения данных из базы данных: ", error)
        return jsonify({'error': 'Ошибка при получении данных'}), 500
    finally:
        db.session.close()

    return jsonify(images_json), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
