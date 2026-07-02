from flask import Flask, render_template, request, redirect
from openai import api_key
import requests
import sqlite3
from google import genai

client = genai.Client(api_key="#KEY")


app = Flask(__name__)

# Replace with your OpenWeather API Key
WEATHER_API_KEY = "YOUR_OPENWEATHER_API_KEY"



# ================= DATABASE =================

def init_db():
    conn = sqlite3.connect("travel.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trips(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        place TEXT,
        days INTEGER,
        budget INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT,
        password TEXT
    )
    """)
    cursor.execute("""
CREATE TABLE IF NOT EXISTS saved_trips(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    place TEXT,
    days INTEGER,
    budget INTEGER
)
""")
    cursor.execute("""
CREATE TABLE IF NOT EXISTS reviews(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    place TEXT,
    username TEXT,
    rating INTEGER,
    review TEXT
)
""")

    conn.commit()
    conn.close()

init_db()


# ================= WIKIPEDIA =================

def get_place_info(place):
    try:
        place = place.replace(" ", "_")

        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{place}"

        headers = {
            "User-Agent": "SmartTravelPlanner"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()

            return {
                "title": data.get("title", place),
                "description": data.get("extract", "No information available"),
                "image": data.get("thumbnail", {}).get("source", "")
            }

    except:
        pass

    return {
        "title": place,
        "description": "No information available",
        "image": ""
    }

def get_attractions(place):

    attractions = {

        "mysuru": [
            "🏰 Mysore Palace",
            "⛰ Chamundi Hills",
            "🌸 Brindavan Gardens",
            "🦁 Mysore Zoo",
            "⛪ St. Philomena's Church",
            "🛍 Devaraja Market",
            "🏛 Jaganmohan Palace",
            "🕉 Srirangapatna"
        ],

        "goa": [
            "🏖 Baga Beach",
            "🌊 Calangute Beach",
            "🏰 Fort Aguada",
            "⛪ Basilica of Bom Jesus",
            "🚤 Dudhsagar Falls",
            "🌅 Vagator Beach"
        ],

        "bengaluru": [
            "🌳 Cubbon Park",
            "🌺 Lalbagh Botanical Garden",
            "🏛 Bangalore Palace",
            "🏢 Vidhana Soudha",
            "🛍 Commercial Street",
            "🐅 Bannerghatta National Park"
        ],

        "ooty": [
            "🚂 Nilgiri Mountain Railway",
            "🌺 Botanical Garden",
            "🏞 Ooty Lake",
            "⛰ Doddabetta Peak",
            "🍃 Tea Museum",
            "🌲 Pine Forest"
        ],

        "hampi": [
            "🛕 Virupaksha Temple",
            "🛞 Stone Chariot",
            "🏯 Lotus Mahal",
            "🌄 Matanga Hill",
            "🏛 Elephant Stables",
            "🌅 Hemakuta Hill"
        ],

        "coorg": [
            "🌊 Abbey Falls",
            "🏞 Raja's Seat",
            "☕ Coffee Plantations",
            "🐘 Dubare Elephant Camp",
            "🛕 Namdroling Monastery",
            "🌳 Talacauvery"
        ],

        "delhi": [
            "🕌 Red Fort",
            "🗼 Qutub Minar",
            "🇮🇳 India Gate",
            "🛕 Lotus Temple",
            "🏛 Humayun's Tomb",
            "🛍 Chandni Chowk"
        ],

        "agra": [
            "🕌 Taj Mahal",
            "🏰 Agra Fort",
            "🌅 Mehtab Bagh",
            "🏛 Fatehpur Sikri",
            "🛍 Kinari Bazaar"
        ],

        "jaipur": [
            "🏰 Amber Fort",
            "🌬 Hawa Mahal",
            "🏯 City Palace",
            "🔭 Jantar Mantar",
            "💧 Jal Mahal"
        ],

        "mumbai": [
            "🌊 Marine Drive",
            "🚪 Gateway of India",
            "🏝 Elephanta Caves",
            "🎬 Film City",
            "🛍 Colaba Causeway"
        ]
    }

    key = place.strip().lower()

    if key in attractions:
        return attractions[key]

    return [
        f"📍 Main Tourist Attraction of {place}",
        f"🏛 Historical Place in {place}",
        f"🌳 Popular Park in {place}",
        f"🛍 Local Market in {place}",
        f"🍽 Famous Food Street in {place}",
        f"🌅 Scenic Viewpoint in {place}"
    ]
# ================= WEATHER =================

def get_weather(place):

    url = (
        f"https://api.openweathermap.org/data/2.5/weather?"
        f"q={place}&appid={WEATHER_API_KEY}&units=metric"
    )

    try:

        response = requests.get(url, timeout=10)

        data = response.json()

        if data.get("cod") != 200:
            return None

        return {
            "temp": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "wind": data["wind"]["speed"],
            "condition": data["weather"][0]["main"],
            "description": data["weather"][0]["description"],
            "icon": data["weather"][0]["icon"]
        }

    except Exception as e:
        print("Weather Error:", e)
        return None


# ================= COORDINATES =================

def get_coordinates(place):
    try:
        url = f"https://nominatim.openstreetmap.org/search"
        params = {
            "q": place,
            "format": "json",
            "limit": 1
        }

        res = requests.get(url, params=params,
                           headers={"User-Agent": "SmartTravelPlanner"})

        data = res.json()

        if data:
            return {
                "lat": float(data[0]["lat"]),
                "lon": float(data[0]["lon"])
            }

    except:
        pass

    return {"lat": 12.97, "lon": 77.59}

# ================= HOTELS =================

import requests

API_KEY = "YOUR_GEOAPIFY_API_KEY"

def get_hotels(place):

    # Get coordinates
    geo_url = f"https://api.geoapify.com/v1/geocode/search?text={place}&apiKey={API_KEY}"

    geo = requests.get(geo_url).json()

    if not geo.get("features"):
        return []

    lon, lat = geo["features"][0]["geometry"]["coordinates"]

    # Search hotels near coordinates
    hotel_url = (
        f"https://api.geoapify.com/v2/places"
        f"?categories=accommodation.hotel"
        f"&filter=circle:{lon},{lat},10000"
        f"&bias=proximity:{lon},{lat}"
        f"&limit=20"
        f"&apiKey={API_KEY}"
    )

    response = requests.get(hotel_url)

    print(response.text)   # <-- Keep this for debugging

    data = response.json()

    hotels = []

    for hotel in data.get("features", []):

        p = hotel["properties"]

        hotels.append({
            "name": p.get("name", "Hotel"),
            "address": p.get("formatted", "Address not available"),
            "lat": p.get("lat"),
            "lon": p.get("lon"),
            "rating": "4.5",
            "price": "Contact Hotel"
        })

    return hotels


# ================= ATTRACTIONS =================

def get_attractions(place):
    return [
        f"Popular attraction in {place}",
        f"Historical monument in {place}",
        f"Cultural center in {place}",
        f"Famous sightseeing spot in {place}"
    ]


# ================= FOOD =================


def get_foods(place):
    foods = {
        "Mysuru": [
            "Mysore Pak",
            "Mysore Masala Dosa",
            "Bisi Bele Bath",
            "Ragi Mudde",
            "Kesari Bath"
        ],
        "Bengaluru": [
            "Donne Biryani",
            "Benne Dosa",
            "Idli Vada",
            "Filter Coffee",
            "Bisi Bele Bath"
        ],
        "Coorg": [
            "Pandi Curry",
            "Kadumbuttu",
            "Noolputtu",
            "Bamboo Shoot Curry",
            "Coorg Coffee"
        ]
    }

    return [{"name": food} for food in foods.get(place, ["Local Special Food"])]

# ================= NEARBY =================

def get_nearby_places(place):
    return [
        f"Nearby attraction near {place}",
        f"Nature spot near {place}",
        f"Historic town near {place}"
    ]


# ================= ITINERARY =================
from google.genai.errors import ClientError

def generate_ai_itinerary(place, days, budget):
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
Create a detailed {days}-day travel itinerary for {place}
with a total budget of ₹{budget}.
Include:
- Morning
- Afternoon
- Evening
- Food suggestions
- Travel tips
"""
        )

        return response.text

    except ClientError:
        return f"""
⚠ AI itinerary is temporarily unavailable because the Gemini free quota has been reached.

Suggested {days}-Day Itinerary for {place}

Day 1
• Visit famous tourist attractions
• Enjoy local lunch
• Explore markets in the evening

Day 2
• Visit museums and temples
• Try local cuisine
• Sunset viewpoint

Budget: ₹{budget}

Please try again tomorrow for AI-generated itinerary.
"""

    except Exception:
        return f"""
Unable to generate AI itinerary.

Destination: {place}
Days: {days}
Budget: ₹{budget}
"""
# ================= TRAVEL TIPS =================

def get_travel_tips(place):
    return [
        f"Best time to visit {place}: October to March",
        "Carry water bottle",
        "Try local food",
        "Book hotels early"
    ]


# ================= PACKING =================

def get_packing_list():
    return [
        "Clothes",
        "Mobile Charger",
        "Power Bank",
        "ID Card",
        "Medicines",
        "Water Bottle"
    ]

import requests

API_KEY = "YOUR_GEOAPIFY_API_KEY"
def get_restaurants(place):

    try:
        # Step 1: Get latitude and longitude
        geo_url = (
            f"https://api.geoapify.com/v1/geocode/search"
            f"?text={place}&apiKey={API_KEY}"
        )

        geo_response = requests.get(geo_url, timeout=10)
        geo_data = geo_response.json()

        if not geo_data.get("features"):
            print("No location found")
            return []

        lon, lat = geo_data["features"][0]["geometry"]["coordinates"]

        # Step 2: Search nearby restaurants
        restaurant_url = (
            "https://api.geoapify.com/v2/places"
            f"?categories=catering.restaurant"
            f"&filter=circle:{lon},{lat},10000"
            f"&bias=proximity:{lon},{lat}"
            f"&limit=20"
            f"&apiKey={API_KEY}"
        )

        response = requests.get(restaurant_url, timeout=10)

        print("Status:", response.status_code)
        print(response.text)   # Debug output

        data = response.json()

        restaurants = []

        for feature in data.get("features", []):

            prop = feature.get("properties", {})

            restaurants.append({
                "name": prop.get("name", "Restaurant"),
                "address": prop.get("formatted", "Address not available"),
                "lat": prop.get("lat"),
                "lon": prop.get("lon"),
            })

        print("Restaurants Found:", len(restaurants))

        return restaurants

    except Exception as e:
        print("Restaurant API Error:", e)
        return []
   
# ================= HOME =================
@app.route('/')
def home():
    return redirect('/login')

@app.route('/index')
def index():
    return render_template('index.html')
# ================= REGISTER =================

@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/register', methods=['POST'])
def register_user():

    username = request.form['username']
    email = request.form['email']
    password = request.form['password']

    conn = sqlite3.connect("travel.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO users(username,email,password) VALUES(?,?,?)",
        (username, email, password)
    )

    conn.commit()
    conn.close()

    return redirect('/login')


# ================= LOGIN =================


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        print("Login button clicked")

        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect("travel.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = cursor.fetchone()

        print("User:", user)

        conn.close()

        if user:
            print("Login Success")
            return redirect('/index')
        else:
            print("Login Failed")
            return "Invalid Email or Password"

    return render_template('login.html')
# ================= SEARCH =================

@app.route('/search', methods=['POST'])
def search():

    place = request.form['place']
    days = int(request.form['days'])
    budget = int(request.form['budget'])

    conn = sqlite3.connect("travel.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO trips(place,days,budget) VALUES(?,?,?)",
        (place, days, budget)
    )

    conn.commit()
    conn.close()

    info = get_place_info(place)
    weather = get_weather(place)
    coordinates = get_coordinates(place)

    attractions = get_attractions(place)
    foods = get_foods(place)
    nearby_places = get_nearby_places(place)

    hotels = get_hotels(budget)

    itinerary = generate_ai_itinerary(place, days, budget)
    tips = get_travel_tips(place)
    packing_list = get_packing_list()

    hotel_budget = int(budget * 0.4)
    food_budget = int(budget * 0.3)
    transport_budget = int(budget * 0.2)
    activity_budget = int(budget * 0.1)

    return render_template(
    "place.html",
    place=place,
    days=days,
    budget=budget,
    info=info,
    weather=weather,
    temp=weather["temp"] if weather else None,
    coordinates=coordinates,
    attractions=attractions,
    foods=foods,
    nearby_places=nearby_places,
    hotels=hotels,
    hotel_budget=hotel_budget,
    food_budget=food_budget,
    transport_budget=transport_budget,
    activity_budget=activity_budget
)


# ================= HISTORY =================

@app.route('/history')
def history():

    conn = sqlite3.connect("travel.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT place, days, budget FROM trips ORDER BY id DESC"
    )

    trips = cursor.fetchall()

    conn.close()

    return render_template(
        "history.html",
        trips=trips
    
    )

@app.route("/saved_trips")
def saved_trips():

    conn = sqlite3.connect("travel.db")
    cursor = conn.cursor()

    cursor.execute("SELECT place, days, budget FROM saved_trips")
    trips = cursor.fetchall()

    conn.close()

    return render_template("saved_trips.html", trips=trips)

    conn.commit()
    conn.close()
    return redirect('/saved_trips')


@app.route('/add_review', methods=['POST'])
def add_review():

    place = request.form['place']
    username = request.form['username']
    rating = request.form['rating']
    review = request.form['review']

    conn = sqlite3.connect("travel.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO reviews(
            place,
            username,
            rating,
            review
        )
        VALUES(?,?,?,?)
        """,
        (place, username, rating, review)
    )

    conn.commit()
    conn.close()

    return redirect('/')
@app.route("/dashboard", methods=["POST"])
def dashboard():

    place = request.form["place"]
    days = request.form["days"]
    budget = request.form["budget"]

    return render_template(
        "dashboard.html",
        place=place,
        days=days,
        budget=budget
    )


@app.route("/attractions")
def attractions_page():

    place = request.args.get("place")

    attractions = get_attractions(place)

    return render_template(
        "attractions.html",
        place=place,
        attractions=attractions
    )

@app.route("/hotels")
def hotels():

    place = request.args.get("place", "Mysuru")
    days = request.args.get("days", 2)
    budget = request.args.get("budget", 5000)

    hotels = get_hotels(place)

    return render_template(
        "hotels.html",
        place=place,
        days=days,
        budget=budget,
        hotels=hotels
    )
@app.route("/restaurants")
def restaurants():

    place = request.args.get("place", "Mysuru")
    days = request.args.get("days", 2)
    budget = request.args.get("budget", 5000)

    restaurants = get_restaurants(place)

    return render_template(
        "restaurants.html",
        place=place,
        days=days,
        budget=budget,
        restaurants=restaurants
    )
@app.route("/itinerary")
def itinerary():
    place = request.args.get("place", "Unknown Place")

    days = request.args.get("days")
    budget = request.args.get("budget")

    # SAFE CONVERSION
    try:
        days = int(days) if days else 2
    except:
        days = 2

    try:
        budget = int(budget) if budget else 5000
    except:
        budget = 5000

    plan = generate_ai_itinerary(place, days, budget)

    return render_template(
        "itinerary.html",
        place=place,
        days=days,
        budget=budget,
        itinerary=plan
    )


@app.route("/budget")
def budget():

    place = request.args.get("place", "Unknown Place")

    days = request.args.get("days")
    budget = request.args.get("budget")

    # Safe conversion
    try:
        days = int(days) if days else 2
    except ValueError:
        days = 2

    try:
        budget = int(budget) if budget else 5000
    except ValueError:
        budget = 5000

    return render_template(
        "budget.html",
        place=place,
        days=days,
        budget=budget
    )


@app.route("/weather")
def weather():

    place = request.args.get("place", "Mysuru")
    days = request.args.get("days", 2)
    budget = request.args.get("budget", 5000)

    weather = get_weather(place)

    return render_template(
        "weather.html",
        place=place,
        days=days,
        budget=budget,
        weather=weather,
        temp=weather["temp"] if weather else None
    )


# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)