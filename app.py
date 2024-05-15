from flask import Flask, request, abort
import requests

app = Flask(__name__)

# 設置 LINE Bot 的存取權杖和 Google Maps API 的金鑰
LINE_CHANNEL_ACCESS_TOKEN ='ZXxMakoI5GNuejiC7Igzm1wvqw3vDxHGRlicvQPM1qizx9eqUJSouLzo1rbTZxo24IWBi0E3AP8lBSOj7SRVt0GkK5Duowbfjn/Zgn8YPHKYfxJC90NHFr8ihfry5YKOjFiNPkHv+XGPydkBv5F0UAdB04t89/1O/w1cDnyilFU='
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
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"  # 使用 LINE Bot 的存取權杖作為授權 token
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

