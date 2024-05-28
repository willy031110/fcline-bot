import random
import requests
from linebot import WebhookHandler, LineBotApi
from linebot.models import *
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, LocationMessage
from linebot.models import TextSendMessage, TemplateSendMessage, CarouselTemplate, CarouselColumn, MessageAction
from flask import Flask, request, abort
import tempfile, os
import datetime
import time

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = 'ZXxMakoI5GNuejiC7Igzm1wvqw3vDxHGRlicvQPM1qizx9eqUJSouLzo1rbTZxo24IWBi0E3AP8lBSOj7SRVt0GkK5Duowbfjn/Zgn8YPHKYfxJC90NHFr8ihfry5YKOjFiNPkHv+XGPydkBv5F0UAdB04t89/1O/w1cDnyilFU='
GOOGLE_MAPS_API_KEY = 'AIzaSyD5sX433QilH8IVyjPiIpqqzJAy_dZrLvE'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler('4226f38b9cd8bce4d0417d29d575f750')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    except Exception as e:
        print(f"Exception: {e}")
        abort(400)
    return 'OK'

def get_nearby_restaurants(latitude, longitude):
    url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={latitude},{longitude}&radius=500&type=restaurant&key={GOOGLE_MAPS_API_KEY}'
    response = requests.get(url)
    data = response.json()
    return data.get('results', [])[:10]  # 只返回前10個餐廳

def format_restaurant_info(restaurant):
    photo_url = restaurant.get('photos')[0]['photo_reference'] if restaurant.get('photos') else ''
    name = restaurant.get('name', '')
    address = restaurant.get('vicinity', '')[:60]  # 確保地址不超過60個字符
    phone_number = restaurant.get('formatted_phone_number', '')
    return {
        'photo_url': f'https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_url}&key={GOOGLE_MAPS_API_KEY}',
        'name': name,
        'address': address,
        'phone_number': phone_number
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
                MessageAction(label='詳細資訊', text=f'詳細資訊: {info["name"]}'),
            ]
        )
        columns.append(column)
    return TemplateSendMessage(
        alt_text='附近餐廳推薦',
        template=CarouselTemplate(columns=columns)
    )

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_id = event.source.user_id
    message_text = event.message.text
    if message_text == '推薦附近餐廳':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='請分享您的位置'))
    elif message_text == '隨機推薦附近餐廳':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='請分享您的位置'))

@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    user_id = event.source.user_id
    latitude = event.message.latitude
    longitude = event.message.longitude
    nearby_restaurants = get_nearby_restaurants(latitude, longitude)

    if '隨機' in event.message.text:
        if nearby_restaurants:
            random_restaurant = random.choice(nearby_restaurants)
            carousel_template = create_carousel_template([random_restaurant])
            line_bot_api.reply_message(event.reply_token, carousel_template)
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text='附近沒有找到餐廳'))
    else:
        carousel_template = create_carousel_template(nearby_restaurants)
        line_bot_api.reply_message(event.reply_token, carousel_template)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
