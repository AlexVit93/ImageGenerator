import os
import logging
from datetime import datetime
from flask import Flask, request, Response
from flask_sqlalchemy import SQLAlchemy
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages import TextMessage, PictureMessage
from viberbot.api.viber_requests import ViberConversationStartedRequest, ViberMessageRequest
import requests
from config import VIBER_TOKEN, OPEN_AI_KEY



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///viber_requests.db'
db = SQLAlchemy(app)

class UserRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, unique=True, nullable=False)
    last_request = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

viber = Api(BotConfiguration(
    name='ImgGen Dalle',
    avatar='https://dl-media.viber.com/1/share/2/long/vibes/icon/image/0x0/e180/79610f57e59ea4bffdf21d261950cfca8d0ea042f0cfd4b7e8606f6d88c3e180.jpg',
    auth_token=VIBER_TOKEN  
))

openai_api_key = OPEN_AI_KEY

@app.route('/start-viber', methods=['POST'])
def incoming():
    logger.debug(f"Received request. Post data: {request.get_data()}")

    if not viber.verify_signature(request.get_data(), request.headers.get('X-Viber-Content-Signature')):
        logger.warning("Invalid signature.")
        return Response(status=403)

    viber_request = viber.parse_request(request.get_data())
    logger.info(f"Received Viber request type: {type(viber_request).__name__}")

    if isinstance(viber_request, ViberConversationStartedRequest):
        viber.send_messages(viber_request.user.id, [
            TextMessage(text="Привет! Какое изображение ты хочешь получить?")
        ])
    elif isinstance(viber_request, ViberMessageRequest):
        message_text = viber_request.message.text
        user_id = viber_request.sender.id

        # Проверка на дубликаты
        last_request = UserRequest.query.filter_by(user_id=user_id).first()
        if last_request and last_request.last_request == message_text:
            logger.info("Duplicate request detected. Ignoring.")
            return Response(status=200)

        if last_request:
            last_request.last_request = message_text
            last_request.timestamp = datetime.utcnow()
        else:
            new_request = UserRequest(user_id=user_id, last_request=message_text)
            db.session.add(new_request)

        db.session.commit()

        logger.info(f"Received message text: {message_text}")
        response = generate_image(message_text)
        if response.startswith("http"):
            viber.send_messages(viber_request.sender.id, [PictureMessage(media=response)])
        else:
            viber.send_messages(viber_request.sender.id, [
                TextMessage(text=response)
            ])

    return Response(status=200)

def generate_image(prompt):
    headers = {
        'Authorization': f'Bearer {openai_api_key}',
        'Content-Type': 'application/json'
    }

    data = {
        'prompt': prompt,
        'size': '256x256',
        'n': 1
    }

    try:
        logger.info(f"Sending image generation request to OpenAI: {data}")
        response = requests.post('https://api.openai.com/v1/images/generations', headers=headers, json=data)
        response.raise_for_status()
        image_url = response.json().get('data', [{}])[0].get('url', "URL изображения не найден")
        logger.info(f"Received response from OpenAI: {response.text}")
        return image_url
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}, Response: {response.text}")
        return "Извините, произошла ошибка при генерации изображения."
    except Exception as e:
        logger.error(f"Error parsing response: {e}")
        return "Ошибка при разборе ответа от API."

viber.set_webhook("https://worker-production-f358.up.railway.app/start-viber")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 7570)), debug=True)
