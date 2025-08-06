from datetime import date
import io
import json
import random
import re
import string
from django.shortcuts import render
from pymongo import MongoClient
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.utils.xmlutils import SimplerXMLGenerator
from django.core.paginator import Paginator
from slugify import slugify
import os
from django.conf import settings
from django.http import FileResponse, Http404

# client = MongoClient(
#     'mongodb://34.136.177.220:27017/')
client = MongoClient('mongodb://localhost:27017/')
db = client['traverve_db']


def get_footer_data():
    footer_data = {}
    top_destinations = list(
        db.countries.find(
            {"seo_tags": {"$ne": ""}},
            {"_id": 0, "id": 1, "name": 1}
        ).limit(10)
    )

    top_cities = list(
        db.cities.find(
            {"seo_tags": {"$ne": ""}},
            {"_id": 0, "id": 1, "city_ascii": 1}
        ).limit(10)
    )

    footer_data["top_destinations"] = top_destinations
    footer_data["top_cities"] = top_cities

    return footer_data


def home(request):

    footer_data = get_footer_data()

    reels = list(
        db.reels_list.find(
            {
                "video_url": {"$ne": None, "$ne": ""},
                "thumbnail_image": {"$ne": "", "$ne": "NULL"}
            },
            {"_id": 0}
        ).sort("id", -1).limit(5)
    )

    tagdata = db.static_page_seo.find_one({"id": 1})
    seo_data = {}
    if tagdata and tagdata.get("home_seo_tags", "") != "":
        seo_data = tagdata.get("home_seo_tags", {})

    home_dests = db.home_cities.find({}, {"_id": 0})

    return render(request, 'trav_web/index.html', {
        "footer_data": footer_data,
        "reels": reels,
        "seo_data": seo_data,
        "home_dests": home_dests
    })


def explore_page(request):
    footer_data = get_footer_data()
    city_col = db['cities']

    seo_data = {
        "title": "Top Tourist Destinations Around the World",
        "seo_description": "Discover the most popular cities and countries for tourism. Explore their top attractions, nearest airports, and more.",
        "og_title": "Top Tourist Destinations Around the World",
        "og_description": "Explore the best cities and countries for tourism. Find key attractions, travel tips, and nearest airports for a memorable journey."
    }

    country_list = []
    country_list = db.countries.find(
        {}, {"name": 1, "id": 1, "image_url": 1}).sort("image_url", 1).limit(8)
    country_count = db.countries.count_documents({})

    # city_list_pipeline = [
    #     {
    #         '$lookup': {
    #             'from': 'city_tags',
    #             'localField': 'id',
    #             'foreignField': 'city_id',
    #             'as': 'tags'
    #         }
    #     },
    #     {
    #         '$match': {
    #             'tags.0': {'$exists': True}
    #         }
    #     },
    #     {
    #         '$project': {
    #             '_id': 0,
    #             'id': 1,
    #             'city_ascii': 1,
    #             'filter_logo': 1
    #         }
    #     },
    #     {
    #         '$sort': {
    #             'filter_logo': -1
    #         }
    #     },
    #     {
    #         '$limit': 8
    #     }
    # ]

    # city_list = list(city_col.aggregate(city_list_pipeline))

    city_list = list(db.cities.aggregate([
        {
            "$addFields": {
                "empty_image": {
                    "$or": [
                        {"$eq": ["$filter_logo", None]},
                        {"$eq": ["$filter_logo", ""]},
                        {"$not": ["$filter_logo"]}
                    ]
                }
            }
        },
        {
            "$sort": {
                "empty_image": 1,
                "filter_logo": 1
            }
        },
        {"$limit": 8},
        {
            "$project": {
                "city_ascii": 1,
                "id": 1,
                "filter_logo": 1,
                "_id": 0
            }
        }
    ]))

    # count_pipeline = [
    #     {
    #         '$lookup': {
    #             'from': 'city_tags',
    #             'localField': 'id',
    #             'foreignField': 'city_id',
    #             'as': 'tags'
    #         }
    #     },
    #     {
    #         '$match': {
    #             'tags.0': {'$exists': True}
    #         }
    #     },
    #     {
    #         '$count': 'totalCount'
    #     }
    # ]

    count_result = city_col.count_documents({})
    total_count = count_result if count_result else 0

    return render(request, 'trav_web/explore.html', {
        "footer_data": footer_data,
        "country_list": country_list,
        "city_list": city_list,
        "city_count": total_count,
        "country_count": country_count,
        "seo_data": seo_data
    })


def generate_faq_schema(faqs):
    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": []
    }

    if "FAQs" in faqs:
        for category, questions in faqs["FAQs"].items():
            for qa in questions:
                faq_schema["mainEntity"].append({
                    "@type": "Question",
                    "name": qa["Question"],
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": qa["Answer"]
                    }
                })

    return json.dumps(faq_schema, ensure_ascii=False, indent=2)


def country_page(request, country_name, id):
    country_id = id
    footer_data = get_footer_data()

    reels = db.reels_list.find(
        {"category_id": country_id}, {"_id": 0}).limit(5)
    data = db.countries.find_one({"id": country_id}, {"_id": 0})
    home_dests = db.cities.find({"country_id": country_id, "is_popular": 1}, {
                                "_id": 0}).sort("is_popular", -1).limit(8)
    city_count = db.cities.count_documents({"country_id": country_id})
    tags = db.country_tags.find({"country_id": country_id}, {"_id": 0})

    seo_data = data.get("seo_tags", "")
    faqs_data = data.get("faqs") if data.get("faqs") else ""

    return render(request, 'trav_web/country_page.html', {
        "footer_data": footer_data,
        "data": data,
        "seo_data": seo_data,
        "faqs_data": faqs_data,
        "faq_schema_json": generate_faq_schema(faqs_data),
        "reels": reels,
        "home_dests": home_dests,
        "tags": tags,
        "city_count": city_count
    })


def city_page(request, city_name, id):
    city_id = id
    footer_data = get_footer_data()

    data = db.cities.find_one({'id': city_id}, {"_id": 0})
    reels = db.reels_list.find(
        {"subcategory_id": data.get("map_id")}, {"_id": 0}).limit(5)

    home_dests = db.cities.find({"country_id": data.get("country_id"), "is_popular": 1, "id": {"$ne": city_id}}, {
                                "_id": 0}).sort("is_popular", -1).limit(8)

    tags = db.city_tags.find({"city_id": city_id}, {"_id": 0})

    seo_data = data.get("seo_tags", "")
    faqs_data = data.get("faqs") if data.get("faqs") else ""

    return render(request, 'trav_web/city_page.html', {
        "footer_data": footer_data,
        "data": data,
        "seo_data": seo_data,
        "faqs_data": faqs_data,
        "faq_schema_json": generate_faq_schema(faqs_data),
        "reels": reels,
        "home_dests": home_dests,
        "tags": tags
    })


def tag_page(request, type, name, cat_name, tag_name, id):

    tag_id = id
    footer_data = get_footer_data()

    if type == "city":
        data = db.city_tags.find_one({"id": tag_id}, {"_id": 0})
        page_name = db.cities.find_one({"id": data.get("city_id", "")}, {
                                       "city_ascii": 1, "country": 1, "country_id": 1})
        other_tags = db.city_tags.find(
            {"city_id": data.get("city_id", ""), "id": {"$ne": tag_id}})
    else:
        data = db.country_tags.find_one({"id": tag_id}, {"_id": 0})
        page_name = db.countries.find_one(
            {"id": data.get("country_id", "")}, {"name": 1})
        other_tags = db.city_tags.find(
            {"country_id": data.get("country_id", ""), "id": {"$ne": tag_id}})

    return render(request, 'trav_web/tag_page.html', {
        "footer_data": footer_data,
        "data": data,
        "tags": other_tags,
        "page_name": page_name
    })


def flights_routes(request, fromcity, tocity):

    footer_data = get_footer_data()
    route = fromcity + "/" + tocity + '/'
    data = db.routes_list_details.find_one(
        {"route": route}, {"_id": 0})

    from_city = data['json']['flight_route']['departure_city'].split(',')[0]
    to_city = data['json']['flight_route']['destination_city'].split(',')[0]

    airlines = [e['airline'] for e in data['json']
                ['flight_route']['top_5_airlines_with_average_price_inr']]
    airlines_str = ','.join(airlines)

    nearby_cities = data['json']['flight_route']['nearby_cities']
    nearby_airport_codes = data['json']['flight_route']['nearby_airport_codes']
    trip_plans = data['json']['tourist_trip_plans']

    return render(request, 'trav_web/routes.html', {
        "footer_data": footer_data,
        "data": data,
        "from_city": from_city,
        "to_city": to_city,
        "airlines_str": airlines_str,
        "nearby_cities": nearby_cities,
        "nearby_airport_codes": nearby_airport_codes,
        'trip_plans': trip_plans
    })


def blog_page(request, url, name, id):
    footer_data = get_footer_data()

    data = db.blogs.find_one({"id": id}, {"_id": 0})

    seo_data = data.get("seo_tags", "")
    return render(request, 'trav_web/blogs.html', {
        "footer_data": footer_data,
        "data": data,
        "seo_data": seo_data
    })


@csrf_exempt
def search_destinations(request):
    data = json.loads(request.body.decode("utf-8"))
    search = data.get("search_key", "")
    search_type = data.get("type", "")
    search_lower = search.lower()
    search_regex = re.compile(f"^{re.escape(search_lower)}", re.IGNORECASE)
    country_id = data.get("country_id", None)
    list_result = []

    if search_type == 'country_to':
        data = db.cities.find({"country_id": int(search), "is_popular": 1}, {
                              "id": 1, "city_ascii": 1, "country": 1, "filter_logo": 1}).limit(10)
        for li in data:
            list_result.append({
                "destination": li.get('city_ascii'),
                "country": li.get('country'),
                "code": "",
                "id": li.get('id'),
                "type": "city",
                "image": li.get('filter_logo')
            })
    elif search_type == 'from':
        data = list(db.cities.find({"city_ascii": search_regex}, {
            "id": 1, "city_ascii": 1, "country": 1, "filter_logo": 1}).limit(10))
        for li in data:
            list_result.append({
                "destination": li.get('city_ascii', ''),
                "country": li.get('country'),
                "code": "",
                "id": li.get('id'),
                "type": "city",
                "image": li.get('filter_logo')
            })
    elif data["type"] == "country":
        country_id = data.get("country_id")
        cities = db.cities.find({
            "city_ascii": search_regex,
            "country_id": int(country_id)
        }).limit(10)

        for city in cities:
            list_result.append({
                "destination": city.get("city_ascii", ""),
                "country": city.get("country", ""),
                "code": "",
                "id": city.get("id", ""),
                "type": "city",
                "image": city.get("filter_logo", "")
            })

    elif data["type"] == "explorecountry":
        country_id = int(search)
        reels = list(db.reels_list.find({"category_id": country_id}).limit(5))
        countries = db.countries.find_one({"id": country_id})
        cities = list(db.cities.find({"country_id": country_id}).sort(
            "is_popular", -1).limit(8))
        tags = list(db.country_tags.find({"country_id": country_id}).limit(6))

        return {
            "data": {
                "reels": reels,
                "data": countries,
                "cities": cities,
                "tags": tags
            }
        }

    elif data["type"] == "explorecity":
        city_id = int(search)
        reels = list(db.reels_list.find({"subcategory_id": city_id}).limit(5))
        city_data = db.cities.find_one({"id": city_id})

        # Find cities in same country that are popular and not this city
        related_cities = list(db.cities.find({
            "country_id": city_data["country_id"],
            "id": {"$ne": city_id},
            "is_popular": 1
        }).limit(8))

        tags = list(db.city_tags.find({"city_id": city_id}).limit(4))

        return {
            "data": {
                "reels": reels,
                "data": city_data,
                "cities": related_cities,
                "tags": tags
            }
        }

    else:
        # Default city search
        cities = db.cities.find({
            "city_ascii": search_regex
        }).limit(10)

        for city in cities:
            list_result.append({
                "destination": city.get("city_ascii", ""),
                "country": city.get("country", ""),
                "code": "",
                "id": city.get("id", ""),
                "type": "city",
                "image": city.get("filter_logo", "")
            })

        # Also search matching countries
        categories = db.countries.find({
            "name": {"$regex": search_lower, "$options": "i"}
        }).limit(5)

        for cat in categories:
            list_result.append({
                "destination": cat.get("name", ""),
                "type": "country",
                "id": cat.get("id", ""),
                "image": cat.get("image_url", "")
            })

    return JsonResponse({"list": list_result}, safe=False)


@csrf_exempt
def getcitiesbypage(request):
    page = json.loads(request.body.decode("utf-8"))
    skip = (int(page.get('page', 0))-1)*8

    if 'type' in page:
        city_list = list(db.cities.find({"country": page.get('country')}, {
            "_id": 0}).skip(skip).limit(10))
    else:
        # city_list_pipeline = [
        #     {
        #         '$lookup': {
        #             'from': 'city_tags',
        #             'localField': 'id',
        #             'foreignField': 'city_id',
        #             'as': 'tags'
        #         }
        #     },
        #     {
        #         '$match': {
        #             'tags.0': {'$exists': True}
        #         }
        #     },
        #     {
        #         '$project': {
        #             '_id': 0,
        #             'id': 1,
        #             'city_ascii': 1,
        #             'filter_logo': 1
        #         }
        #     },
        #     {
        #         '$sort': {
        #             'filter_logo': -1
        #         }
        #     }, {
        #         '$skip': skip
        #     },
        #     {
        #         '$limit': 8
        #     }
        # ]

        # city_list = list(db.cities.aggregate(city_list_pipeline))
        city_list = list(db.cities.aggregate([
            {
                "$addFields": {
                    "empty_image": {
                        "$or": [
                            {"$eq": ["$filter_logo", None]},
                            {"$eq": ["$filter_logo", ""]},
                            {"$not": ["$filter_logo"]}
                        ]
                    }
                }
            },
            {
                "$sort": {
                    "empty_image": 1,
                    "filter_logo": 1
                }
            },
            {"$skip": skip},
            {"$limit": 8},
            {
                "$project": {
                    "city_ascii": 1,
                    "id": 1,
                    "filter_logo": 1,
                    "_id": 0
                }
            }
        ]))

    return JsonResponse(city_list, safe=False)


@csrf_exempt
def getcountriesbypage(request):
    page = json.loads(request.body.decode("utf-8"))
    skip = (int(page.get('page', 0))-1)*8

    countries = list(db.countries.aggregate([
        {
            "$addFields": {
                "empty_image": {"$eq": ["$image_url", ""]}
            }
        },
        {
            "$sort": {
                "empty_image": 1,  # False (non-empty) first, True (empty) last
                "image_url": 1
            }
        },
        {"$skip": skip},
        {"$limit": 8},
        {
            "$project": {
                "name": 1,
                "id": 1,
                "image_url": 1,
                "_id": 0
            }
        }
    ]))
    # countries = db.countries.find({}, {"name": 1, "id": 1, "image_url": 1}).sort([
    #     ("image_url", 1)]).skip(skip).limit(8)
    return JsonResponse(countries, safe=False)


def trips_list(request):
    footer_data = get_footer_data()
    cookie_id = request.COOKIES.get("cookie_id")

    user_trips = []
    all_trips = []

    if cookie_id:
        pipeline_user_trips = [
            {"$match": {"cookie_id": cookie_id}},
            {"$lookup": {
                "from": "cities_list",
                "localField": "from_id",
                "foreignField": "id",
                "as": "city_data"
            }},
            {"$unwind": {"path": "$city_data", "preserveNullAndEmptyArrays": True}},
            {"$addFields": {
                "filter_logo": "$city_data.filter_logo"
            }},
            {"$project": {
                "city_data": 0
            }}
        ]
        user_trips = list(db.trip_list.aggregate(pipeline_user_trips))

    all_trips = list(db.trip_list.find({
        "cookie_id": {"$ne": cookie_id}
    }))

    return render(request, 'trav_web/trips_list.html', {
        "footer_data": footer_data,
        "user_trips": user_trips,
        "all_trips": all_trips
    })


@csrf_exempt
def savetrip(request):
    data = json.loads(request.body)
    obj = {}

    if "trip_name" in data:
        obj["trip_name"] = data["trip_name"]
        obj["json"] = json.dumps([])
    else:
        trip_data = data.get("data", [])
        if trip_data:
            d = trip_data[0]
            obj["trip_name"] = data.get("title", "")
            obj["from_code"] = d["destinationa"]["code"]
            obj["from_id"] = d["destinationa"]["id"]
            obj["to_code"] = d["destinationb"]["code"]
            obj["to_id"] = d["destinationb"]["id"]
            obj["json"] = json.dumps(trip_data)
            obj["status"] = data.get("status", 0)

    # Get cookie ID
    obj["cookie_id"] = request.COOKIES.get("cookie_id")

    # Update or insert
    if "id" in data:
        db.trip_list.update_one({"trip_id": data["id"]}, {"$set": obj})
        trip_id = data["id"]
    else:
        while True:
            trip_id = ''.join(random.choices(
                string.ascii_letters + string.digits, k=random.randint(2, 5)))
            if not is_id_present(trip_id):
                break
        obj["trip_id"] = trip_id
        db.trip_list.insert_one(obj)

    return JsonResponse({"trip": trip_id})


def is_id_present(trip_id):
    return db.trip_list.find_one({"trip_id": trip_id}) is not None


def trip_planner(request, trip_id):
    country_list = db.countries.find(
        {}, {"name": 1, "id": 1, "image_url": 1}).sort("image_url", 1).limit(4)

    city_list = list(db.cities.aggregate([
        {
            "$addFields": {
                "empty_image": {
                    "$or": [
                        {"$eq": ["$filter_logo", None]},
                        {"$eq": ["$filter_logo", ""]},
                        {"$not": ["$filter_logo"]}
                    ]
                }
            }
        },
        {
            "$sort": {
                "empty_image": 1,
                "filter_logo": 1
            }
        },
        {"$limit": 8},
        {
            "$project": {
                "city_ascii": 1,
                "id": 1,
                "filter_logo": 1,
                "_id": 0
            }
        }
    ]))
    tripdata = {}
    if trip_id:
        trip = db.trip_list.find_one(
            {"trip_id": trip_id}, {"_id": 0, "trip_id": 1, "json": 1, "trip_name": 1})
        if trip:
            tripdata = {
                "trip_id": trip["trip_id"],
                "trip_name": trip["trip_name"],
                "data": (trip["json"]) if trip.get("json") else "[]"
            }

    return render(request, 'trav_web/trip_planner.html', {
        "country_list": country_list,
        "city_list": city_list,
        "trip": tripdata
    })


@csrf_exempt
def gettododata(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            todata = data.get('to', '').lower()

            todo_items = db.todo_list.find({'z_city_name': todata}).limit(20)

            result = [{"id": item.get('id'), "name": item.get('name')}
                      for item in todo_items]

            return JsonResponse({"list": result}, safe=False)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=400)



def serve_sitemap(request, filename):
    sitemap_dir = os.path.join(settings.BASE_DIR, 'static', 'sitemaps')
    file_path = os.path.join(sitemap_dir, filename)

    if not os.path.exists(file_path):
        raise Http404("Sitemap not found")

    return FileResponse(open(file_path, 'rb'), content_type='application/xml')

# def sitemap_index(request):
#     output = io.StringIO()
#     xml = SimplerXMLGenerator(output, 'utf-8')
#     xml.startDocument()
#     xml.startElement("sitemapindex", {
#                      "xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9"})

#     count = db.countries.count_documents({})
#     pages = (count // 5000) + (1 if count % 5000 else 0)
#     xml = prepareSitemapList(pages, 'countries', xml)

#     count = db.cities.count_documents({})
#     pages = (count // 5000) + (1 if count % 5000 else 0)
#     xml = prepareSitemapList(pages, 'cities', xml)

#     count = db.country_tags.count_documents({})
#     pages = (count // 5000) + (1 if count % 5000 else 0)
#     xml = prepareSitemapList(pages, 'country_tags', xml)

#     count = db.city_tags.count_documents({})
#     pages = (count // 5000) + (1 if count % 5000 else 0)
#     xml = prepareSitemapList(pages, 'city_tags', xml)

#     # count = db.blogs.count_documents({})
#     # pages = (count // 5000) + (1 if count % 5000 else 0)
#     # xml = prepareSitemapList(pages, 'blogs', xml)

#     count = db.routes_list_details.count_documents({})
#     pages = (count // 5000) + (1 if count % 5000 else 0)
#     xml = prepareSitemapList(pages, 'routes_list_details', xml)

#     xml.endElement("sitemapindex")
#     xml.endDocument()

#     return HttpResponse(output.getvalue(), content_type="application/xml")


# def prepareSitemapList(pages, type, xml):

#     for i in range(1, pages + 1):
#         xml.startElement("sitemap", {})
#         xml.startElement("loc", {})
#         xml.characters(f"https://traverve.com/sitemap-{type}-{i}.xml")
#         xml.endElement("loc")
#         xml.startElement("lastmod", {})
#         xml.characters(date.today().strftime('%Y-%m-%d'))
#         xml.endElement("lastmod")
#         xml.endElement("sitemap")

#     return xml


# def sitemap_cities(request, page=1):

#     cities_cursor = db.cities.find(
#         {}, {"city_ascii": 1, "id": 1}).sort("_id", 1)
#     cities = list(cities_cursor)

#     paginator = Paginator(cities, 5000)

#     if page > paginator.num_pages:
#         return HttpResponse("Page not found", status=404)

#     page_items = paginator.page(page).object_list

#     output = io.StringIO()
#     xml = SimplerXMLGenerator(output, 'utf-8')
#     xml.startDocument()
#     xml.startElement(
#         "urlset", {"xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9"})

#     for item in page_items:
#         slug = slugify(item.get('city_ascii', ''))
#         url = f"https://traverve.com/city/{slug}/{item.get('id')}"
#         xml = creatingUrl(xml, url)

#     xml.endElement("urlset")
#     xml.endDocument()

#     return HttpResponse(output.getvalue(), content_type="application/xml")


# def sitemap_countries(request, page=1):
#     cursor = db.countries.find({}, {"name": 1, "id": 1}).sort("_id", 1)
#     countries = list(cursor)

#     paginator = Paginator(countries, 5000)

#     if page > paginator.num_pages:
#         return HttpResponse("Page not found", status=404)

#     page_items = paginator.page(page).object_list

#     output = io.StringIO()
#     xml = SimplerXMLGenerator(output, 'utf-8')
#     xml.startDocument()
#     xml.startElement(
#         "urlset", {"xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9"})

#     for item in page_items:
#         slug = slugify(item.get('name', ''))
#         url = f"https://traverve.com/country/{slug}/{item.get('id')}"
#         xml = creatingUrl(xml, url)

#     xml.endElement("urlset")
#     xml.endDocument()

#     return HttpResponse(output.getvalue(), content_type="application/xml")

# def sitemap_country_tags(request, page=1):
#     cursor = db.country_tags.find({}, {"country_name": 1,"tag_cat_name": 1, "tag_name": 1, "id": 1}).sort("_id", 1)
#     countries = list(cursor)

#     paginator = Paginator(countries, 5000)

#     if page > paginator.num_pages:
#         return HttpResponse("Page not found", status=404)

#     page_items = paginator.page(page).object_list

#     output = io.StringIO()
#     xml = SimplerXMLGenerator(output, 'utf-8')
#     xml.startDocument()
#     xml.startElement(
#         "urlset", {"xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9"})
#     for item in page_items:
#         slug = slugify(item.get('country_name',''))
#         slug1 = slugify(item.get('tag_cat_name', ''))
#         slug2 = slugify(item.get('tag_name', ''))
#         url = f"https://traverve.com/country/{slug}/category/{slug1}/{slug2}/{item.get('id')}"
#         xml = creatingUrl(xml, url)

#     xml.endElement("urlset")
#     xml.endDocument()

#     return HttpResponse(output.getvalue(), content_type="application/xml")

# def sitemap_city_tags(request, page=1):
#     cursor = db.city_tags.find({"city_name" : {"$exists": True}}, {"city_name": 1,"tag_cat_name": 1, "tag_name": 1, "id": 1}).sort("_id", 1)
#     countries = list(cursor)

#     paginator = Paginator(countries, 5000)

#     if page > paginator.num_pages:
#         return HttpResponse("Page not found", status=404)

#     page_items = paginator.page(page).object_list

#     output = io.StringIO()
#     xml = SimplerXMLGenerator(output, 'utf-8')
#     xml.startDocument()
#     xml.startElement(
#         "urlset", {"xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9"})
#     for item in page_items:
#         slug = slugify(item.get('city_name',''))
#         slug1 = slugify(item.get('tag_cat_name', ''))
#         slug2 = slugify(item.get('tag_name', ''))
#         url = f"https://traverve.com/city/{slug}/category/{slug1}/{slug2}/{item.get('id')}"
#         xml = creatingUrl(xml, url)

#     xml.endElement("urlset")
#     xml.endDocument()

#     return HttpResponse(output.getvalue(), content_type="application/xml")

# def sitemap_routes_list_details(request, page=1):
#     cursor = db.routes_list_details.find({}, {"route": 1})
#     countries = list(cursor)

#     paginator = Paginator(countries, 5000)

#     if page > paginator.num_pages:
#         return HttpResponse("Page not found", status=404)

#     page_items = paginator.page(page).object_list

#     output = io.StringIO()
#     xml = SimplerXMLGenerator(output, 'utf-8')
#     xml.startDocument()
#     xml.startElement(
#         "urlset", {"xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9"})
#     for item in page_items:
#         slug = item.get('route')
#         url = f"https://traverve.com/flights/{slug}"
#         xml = creatingUrl(xml, url)

#     xml.endElement("urlset")
#     xml.endDocument()

#     return HttpResponse(output.getvalue(), content_type="application/xml")

# def creatingUrl(xml, url):
#     xml.startElement("url", {})
#     xml.startElement("loc", {})
#     xml.characters(url)
#     xml.endElement("loc")
#     xml.startElement("lastmod", {})
#     xml.characters(date.today().strftime('%Y-%m-%d'))
#     xml.endElement("lastmod")
#     xml.startElement("changefreq", {})
#     xml.characters('daily')
#     xml.endElement("changefreq")
#     xml.startElement("priority", {})
#     xml.characters('0.9')
#     xml.endElement("priority")
#     xml.endElement("url")
    
#     return xml

