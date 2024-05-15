from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import*
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, LocationMessage
import requests
import random

#======這裡是呼叫的檔案內容=====
from message import *
from new import *
from Function import *
#======這裡是呼叫的檔案內容=====

#======python的函數庫==========
import tempfile, os
import datetime
import time
#======python的函數庫==========

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi('ZXxMakoI5GNuejiC7Igzm1wvqw3vDxHGRlicvQPM1qizx9eqUJSouLzo1rbTZxo24IWBi0E3AP8lBSOj7SRVt0GkK5Duowbfjn/Zgn8YPHKYfxJC90NHFr8ihfry5YKOjFiNPkHv+XGPydkBv5F0UAdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('4226f38b9cd8bce4d0417d29d575f750')
GOOGLE_MAPS_API_KEY = 'AIzaSyD5sX433QilH8IVyjPiIpqqzJAy_dZrLvE'

@app.route("/callback", methods=["POST"])
def callback():
    if request.method == "POST":
        payload = request.get_json()
        for event in payload["events"]:
            if event["type"] == "message" and event["message"]["type"] == "location":
                handle_location_message(event)
        return "", 200
    else:
        abort(400)

def handle_location_message(event):
    lat = event["message"]["latitude"]
    lng = event["message"]["longitude"]
    nearby_restaurants = get_nearby_restaurants(lat, lng)
    reply_carousel_message(event["replyToken"], nearby_restaurants)

def get_nearby_restaurants(lat, lng):
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
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {'ZXxMakoI5GNuejiC7Igzm1wvqw3vDxHGRlicvQPM1qizx9eqUJSouLzo1rbTZxo24IWBi0E3AP8lBSOj7SRVt0GkK5Duowbfjn/Zgn8YPHKYfxJC90NHFr8ihfry5YKOjFiNPkHv+XGPydkBv5F0UAdB04t89/1O/w1cDnyilFU='}"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "template",
                "altText": "Nearby Restaurants",
                "template": {
                    "type": "carousel",
                    "columns": [
                        {
                            "thumbnailImageUrl": "https://example.com/image1.jpg",
                            "title": restaurant["name"],
                            "text": restaurant["address"],
                            "actions": [
                                {
                                    "type": "uri",
                                    "label": "View on Google Maps",
                                    "uri": "https://www.google.com/maps/search/?api=1&query=" + restaurant["name"]
                                }
                            ]
                        } for restaurant in restaurants
                    ]
                }
            }
        ]
    }
    url = "https://api.line.me/v2/bot/message/reply"
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        print("Failed to send carousel message:", response.text)

if __name__ == "__main__":
    app.run(debug=True)
import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
