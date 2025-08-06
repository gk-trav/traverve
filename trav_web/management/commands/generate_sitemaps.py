import os
from datetime import date
from django.core.management.base import BaseCommand
from django.conf import settings
from xml.sax.saxutils import XMLGenerator
from django.core.paginator import Paginator
# from trav_web.d import db  # update as per your project
from django.utils.text import slugify
from pymongo import MongoClient

# client = MongoClient(
#     'mongodb://34.136.177.220:27017/')
client = MongoClient('mongodb://localhost:27017/')
db = client['traverve_db']

SITEMAP_DIR = os.path.join(settings.BASE_DIR, 'static', 'sitemaps')

class Command(BaseCommand):
    help = "Generates static sitemap XML files"

    def handle(self, *args, **kwargs):
        os.makedirs(SITEMAP_DIR, exist_ok=True)

        sitemap_list = []

        sitemap_list += self.generate_sitemap_for_collection(
            coll=db.cities,
            proj={},
            fields={"city_ascii": 1, "id": 1},
            name="cities",
            url_builder=lambda item: f"https://traverve.com/city/{slugify(item['city_ascii'])}/{item['id']}"
        )

        sitemap_list += self.generate_sitemap_for_collection(
            coll=db.countries,
            proj = {},
            fields={"name": 1, "id": 1},
            name="countries",
            url_builder=lambda item: f"https://traverve.com/country/{slugify(item['name'])}/{item['id']}"
        )

        sitemap_list += self.generate_sitemap_for_collection(
            coll=db.country_tags,
            proj={},
            fields={"country_name": 1, "tag_cat_name": 1, "tag_name": 1, "id": 1},
            name="country_tags",
            url_builder=lambda item: f"https://traverve.com/country/{slugify(item['country_name'])}/category/{slugify(item['tag_cat_name'])}/{slugify(item['tag_name'])}/{item['id']}"
        )

        sitemap_list += self.generate_sitemap_for_collection(
            coll=db.city_tags,
            proj={"city_name" : {"$exists": True}},
            fields={"city_name": 1, "tag_cat_name": 1, "tag_name": 1, "id": 1},
            name="city_tags",
            url_builder=lambda item: f"https://traverve.com/city/{slugify(item['city_name'])}/category/{slugify(item['tag_cat_name'])}/{slugify(item['tag_name'])}/{item['id']}"
        )

        sitemap_list += self.generate_sitemap_for_collection(
            coll=db.routes_list_details,
            proj={},
            fields={"route": 1},
            name="routes_list_details",
            url_builder=lambda item: f"https://traverve.com/flights/{item['route']}"
        )

        self.generate_index_file(sitemap_list)

        self.stdout.write(self.style.SUCCESS("✅ Sitemaps generated successfully."))

    def generate_sitemap_for_collection(self, coll, proj, fields, name, url_builder):
        all_items = list(coll.find(proj, fields))
        paginator = Paginator(all_items, 5000)

        file_list = []

        for page in range(1, paginator.num_pages + 1):
            page_items = paginator.page(page).object_list
            filename = f"sitemap-{name}-{page}.xml"
            filepath = os.path.join(SITEMAP_DIR, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                xml = XMLGenerator(f, 'utf-8')
                xml.startDocument()
                xml.startElement("urlset", {"xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9"})

                for item in page_items:
                    url = url_builder(item)
                    self.create_url_element(xml, url)

                xml.endElement("urlset")
                xml.endDocument()

            file_list.append(filename)

        return file_list

    def generate_index_file(self, sitemap_files):
        filepath = os.path.join(SITEMAP_DIR, "sitemap.xml")
        with open(filepath, 'w', encoding='utf-8') as f:
            xml = XMLGenerator(f, 'utf-8')
            xml.startDocument()
            xml.startElement("sitemapindex", {"xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9"})

            for filename in sitemap_files:
                xml.startElement("sitemap", {})
                xml.startElement("loc", {})
                xml.characters(f"https://traverve.com/{filename}")
                xml.endElement("loc")
                xml.startElement("lastmod", {})
                xml.characters(date.today().strftime('%Y-%m-%d'))
                xml.endElement("lastmod")
                xml.endElement("sitemap")

            xml.endElement("sitemapindex")
            xml.endDocument()

    def create_url_element(self, xml, url):
        xml.startElement("url", {})
        xml.startElement("loc", {})
        xml.characters(url)
        xml.endElement("loc")
        xml.startElement("lastmod", {})
        xml.characters(date.today().strftime('%Y-%m-%d'))
        xml.endElement("lastmod")
        xml.startElement("changefreq", {})
        xml.characters('daily')
        xml.endElement("changefreq")
        xml.startElement("priority", {})
        xml.characters('0.9')
        xml.endElement("priority")
        xml.endElement("url")
