import logging
from flask import Flask, request, Response
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages import TextMessage
from viberbot.api.viber_requests import ViberConversationStartedRequest, ViberMessageRequest
import requests
import json
from config import VIBER_AUTH_TOKEN, OPENAI_API_KEY


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
viber = Api(BotConfiguration(
    name='ImageGenerator',
    avatar='',
    auth_token=VIBER_AUTH_TOKEN  
))

openai_api_key = OPENAI_API_KEY  

@app.route('/', methods=['POST'])
def incoming():
    logger.info("Received a request")
    viber_request = viber.parse_request(request.get_data())

    if isinstance(viber_request, ViberConversationStartedRequest):
        viber.send_messages(viber_request.user.id, [
            TextMessage(text="Привет! Скажи, какое изображение ты хочешь получить сейчас?")
        ])
    elif isinstance(viber_request, ViberMessageRequest):
        message_text = viber_request.message.text
        response = generate_image(message_text)
        viber.send_messages(viber_request.sender.id, [
            TextMessage(text="Твое изображение будет готово примерно через 2-3 минуты"),
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
        'size': '300x300',
        'n': 1
    }

    response = requests.post('https://api.openai.com/v1/images/generations', headers=headers, json=data)
    if response.status_code == 200:
        image_url = json.loads(response.text)['data'][0]['url']
        return image_url
    else:
        logger.error("Error in image generation")
        return "Извините, произошла ошибка при генерации изображения."

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
