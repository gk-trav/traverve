import random
import string
from pymongo import MongoClient


# client = MongoClient(
#     'mongodb://34.136.177.220:27017/')
client = MongoClient('mongodb://localhost:27017/')
db = client["traverve_db"]
user_ids = db["user_ids"]

def generate_cookie_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

class SetCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only set cookie if it doesn't already exist
        if not request.COOKIES.get("cookie_id"):
            visitor_id = generate_cookie_id()

            # Save to MongoDB
            user_ids.insert_one({"cookie_id": visitor_id})

            # Set the cookie (1 year)
            response.set_cookie("cookie_id", visitor_id, max_age=60 * 60 * 24 * 365, path="/")

        return response
