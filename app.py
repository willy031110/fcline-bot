from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os
import requests

app = Flask(__name__)

# 環境變數存儲敏感信息
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('ZXxMakoI5GNuejiC7Igzm1wvqw3vDxHGRlicvQPM1qizx9eqUJSouLzo1rbTZxo24IWBi0E3AP8lBSOj7SRVt0GkK5Duowbfjn/Zgn8YPHKYfxJC90NHFr8ihfry5YKOjFiNPkHv+XGPydkBv5F0UAdB04t89/1O/w1cDnyilFU=')
LINE_CHANNEL_SECRET = os.getenv('4226f38b9cd8bce4d0417d29d575f750')
GOOGLE_MAPS_API_KEY = os.getenv('AIzaSyD5sX433QilH8IVyjPiIpqqzJAy_dZrLvE')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("簽名驗證失敗。請檢查您的頻道訪問令牌和頻道密鑰。")
        abort(400)
    except Exception as e:
        print(f"例外情況: {e}")
        abort(400)
    return 'OK'

def get_nearby_restaurants(latitude, longitude):
    try:
        url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={latitude},{longitude}&radius=500&type=restaurant&key={GOOGLE_MAPS_API_KEY}'
        response = requests.get(url)
        response.raise_for_status()  # 為不良回應引發HTTPError
        data = response.json()
        return data.get('results', [])[:10]  # 限制返回的餐廳數量不超過10個
    except requests.RequestException as e:
        print(f"請求失敗: {e}")
        return []

def format_restaurant_info(restaurant):
    photo_reference = restaurant.get('photos')[0].get('photo_reference') if restaurant.get('photos') else ''
    name = restaurant.get('name', '')[:40]  # 確保名稱符合限制
    address = restaurant.get('vicinity', '')[:60]  # 限制地址長度
    photo_url = f'https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={GOOGLE_MAPS_API_KEY}' if photo_reference else ''
    return {
        'photo_url': photo_url,
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
    message_text = event.message.text.strip()
    if message_text in ['推薦附近餐廳', '隨機推薦附近餐廳']:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='請分享您的位置'))

@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    latitude = event.message.latitude
    longitude = event.message.longitude
    nearby_restaurants = get_nearby_restaurants(latitude, longitude)
    if not nearby_restaurants:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='找不到附近的餐廳，請稍後再試。'))
        return
    carousel_template = create_carousel_template(nearby_restaurants)
    line_bot_api.reply_message(event.reply_token, carousel_template)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)




