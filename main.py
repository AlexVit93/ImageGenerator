import os
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
    name='GeneratorImageZVD22',
    avatar='https://dl-media.viber.com/1/share/2/long/vibes/icon/image/0x0/f56e/239aafb14ef8d8170306d44e50ccda5c65b56882d61b98bb8463ddc6c25af56e.jpg',
    auth_token="52140c8a4c27e541-3cb4c10a0a4f4a22-899a23cf49f3cc8f"  
))

openai_api_key = "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"  

@app.route('/start-viber', methods=['POST'])
def incoming():
    logging.debug("received request. post data: {0}".format(request.get_data()))
    
    if not viber.verify_signature(request.get_data(), request.headers.get('X-Viber-Content-Signature')):
        return Response(status=403)

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
            # Добавьте больше логирования
            logger.error(f"Full error: {e}, Response: {response.text}")
            return "Ошибка при разборе ответа от API."
    else:
        logger.error("Error in image generation")
        return "Извините, произошла ошибка при генерации изображения."

viber.set_webhook("https://worker-production-0a9f.up.railway.app/start-viber")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 7570)), debug=True)
    
