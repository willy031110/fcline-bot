import logging
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, LocationMessage, CarouselColumn, TemplateSendMessage, CarouselTemplate, MessageAction
import requests
import os

app = Flask(__name__)

# 設置日誌
logging.basicConfig(level=logging.INFO)

# 頻道訪問令牌和密鑰
line_bot_api = LineBotApi('ZXxMakoI5GNuejiC7Igzm1wvqw3vDxHGRlicvQPM1qizx9eqUJSouLzo1rbTZxo24IWBi0E3AP8lBSOj7SRVt0GkK5Duowbfjn/Zgn8YPHKYfxJC90NHFr8ihfry5YKOjFiNPkHv+XGPydkBv5F0UAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('4226f38b9cd8bce4d0417d29d575f750')
GOOGLE_MAPS_API_KEY = 'AIzaSyD5sX433QilH8IVyjPiIpqqzJAy_dZrLvE'

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    logging.info(f"Request body: {body}")
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logging.error("無效的簽名。請檢查你的頻道訪問令牌/頻道密鑰。")
        abort(400)
    except LineBotApiError as e:
        logging.error(f"LineBotApiError: {e.status_code} {e.error.message} {e.error.details}")
        abort(400)
    except Exception as e:
        logging.error(f"異常: {e}")
        abort(400)
    return 'OK'

def get_nearby_restaurants(latitude, longitude):
    url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={latitude},{longitude}&radius=500&type=restaurant&key={GOOGLE_MAPS_API_KEY}'
    response = requests.get(url)
    data = response.json()
    return data.get('results', [])[:10]  # 限制返回的餐廳數量不超過10個

def format_restaurant_info(restaurant):
    photo_reference = restaurant.get('photos', [{}])[0].get('photo_reference', '')
    name = restaurant.get('name', 'N/A')
    address = restaurant.get('vicinity', 'N/A')[:60]  # 限制地址長度
    return {
        'photo_url': f'https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={GOOGLE_MAPS_API_KEY}' if photo_reference else '',
        'name': name,
        'address': address
    }

def create_carousel_template(restaurants):
    columns = []
    for restaurant in restaurants:
        info = format_restaurant_info(restaurant)
        column = CarouselColumn(
            thumbnail_image_url=info['photo_url'],
            title=info['name'],
            text=info['address'],
            actions=[
                MessageAction(label='詳細資訊', text=f'詳細資訊: {info["name"]}')
            ]
        )
        columns.append(column)
    return TemplateSendMessage(
        alt_text='附近餐廳推薦',
        template=CarouselTemplate(columns=columns)
    )

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    message_text = event.message.text
    if message_text in ['推薦附近餐廳', '隨機推薦附近餐廳']:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='請分享您的位置'))

@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    latitude = event.message.latitude
    longitude = event.message.longitude
    nearby_restaurants = get_nearby_restaurants(latitude, longitude)
    carousel_template = create_carousel_template(nearby_restaurants)
    try:
        line_bot_api.reply_message(event.reply_token, carousel_template)
    except LineBotApiError as e:
        logging.error(f"回覆消息時出現錯誤: {e.status_code} {e.error.message} {e.error.details}")

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)


