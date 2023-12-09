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
    name='NewImageGeneratorZVD22',
    avatar='https://dl-media.viber.com/1/share/2/long/vibes/icon/image/0x0/c437/7099cf7713bfd81662c5e4da0b01ce80c2daafb4a2d1326f7fd0541d4e0ac437.jpg',
    auth_token="52139de14827dd23-aa10a3f48f7b8005-1c2df36521587b45"  
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

try:
    viber.set_webhook('https://worker-production-5dfa.up.railway.app/viber-webhook')
except Exception as e:
    logger.error(f"Error setting webhook: {e}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
