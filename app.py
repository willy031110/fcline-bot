from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *
import requests

app = Flask(__name__)

# 設置 LINE Bot 的存取權杖和 Google Maps API 的金鑰
LINE_CHANNEL_ACCESS_TOKEN ='ZXxMakoI5GNuejiC7Igzm1wvqw3vDxHGRlicvQPM1qizx9eqUJSouLzo1rbTZxo24IWBi0E3AP8lBSOj7SRVt0GkK5Duowbfjn/Zgn8YPHKYfxJC90NHFr8ihfry5YKOjFiNPkHv+XGPydkBv5F0UAdB04t89/1O/w1cDnyilFU='
GOOGLE_MAPS_API_KEY = 'AIzaSyD5sX433QilH8IVyjPiIpqqzJAy_dZrLvE'

# 初始化 LINE Bot API 和 Webhook Handler
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler('4226f38b9cd8bce4d0417d29d575f750')

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return "OK"

@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    lat = event.message.latitude
    lng = event.message.longitude
    nearby_restaurants = get_nearby_restaurants(lat, lng)
    reply_carousel_message(event.reply_token, nearby_restaurants)

def get_nearby_restaurants(lat, lng):
    # 使用 Google Maps API 查詢附近餐廳
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=1500&type=restaurant&key={GOOGLE_MAPS_API_KEY}"
    response = requests.get(url)
    data = response.json()
    restaurants = []
    for place in data["results"]:
        restaurants.append({
            "name": place["name"],
            "address": place.get("vicinity", "Address not available")
        })
    return restaurants

def reply_carousel_message(reply_token, restaurants):
    columns = []
    for restaurant in restaurants:
        column = CarouselColumn(
            thumbnail_image_url="https://example.com/image1.jpg",
            title=restaurant["name"],
            text=restaurant["address"],
            actions=[
                URIAction(
                    label="View on Google Maps",
                    uri="https://www.google.com/maps/search/?api=1&query=" + restaurant["name"]
                )
            ]
        )
        columns.append(column)

    carousel_template = CarouselTemplate(columns=columns)
    template_message = TemplateSendMessage(alt_text="Nearby Restaurants", template=carousel_template)
    
    line_bot_api.reply_message(reply_token, template_message)

if __name__ == "__main__":
    app.run(debug=True)

