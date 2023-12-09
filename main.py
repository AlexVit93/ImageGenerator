import logging
from flask import Flask, request, Response
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages import TextMessage
from viberbot.api.viber_requests import ViberConversationStartedRequest, ViberMessageRequest
import requests



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
viber = Api(BotConfiguration(
    name='ViberImgGenZVD22',
    avatar='https://dl-media.viber.com/1/share/2/long/vibes/icon/image/0x0/7a79/ea1b44bd126efb7b41b8287c94919ebec3f329f99eac4c00241274b577fd7a79.jpg',
    auth_token="5213cb7e4567dca0-d4405daf51c55dad-2ac214f785263ae4"  
))

openai_api_key = "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"  

@app.route('/viber-webhook', methods=['POST'])
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
        try:
            image_url = response.json().get('data', [{}])[0].get('url', "URL изображения не найден")
            return image_url
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return "Ошибка при разборе ответа от API."
    else:
        logger.error("Error in image generation")
        return "Извините, произошла ошибка при генерации изображения."



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)

viber.set_webhook('https://worker-production-7610.up.railway.app')
