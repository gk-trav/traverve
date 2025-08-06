"""
URL configuration for trav_web project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from . import views
from django.contrib import admin
from django.urls import path

from django.urls import path, re_path
from trav_web.views import serve_sitemap

urlpatterns = [
    path('<slug:type>/<slug:name>/category/<slug:cat_name>/<slug:tag_name>/<int:id>',views.tag_page, name="tags"),
    path('flights/<slug:fromcity>/<slug:tocity>', views.flights_routes, name="flight_routes"),
    path('details/<slug:url>/<slug:name>/<int:id>', views.blog_page, name="blog_page"),
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('explore', views.explore_page, name='explore'),
    path('country/<slug:country_name>/<int:id>', views.country_page, name='country'),
    path('city/<slug:city_name>/<int:id>', views.city_page, name='city'),
    path('api/searchdestinations', views.search_destinations, name='search_destinations'),
    path('api/getcitiesbypage', views.getcitiesbypage, name='getcitiesbypage'),
    path('api/getcountriesbypage', views.getcountriesbypage, name='getcountriesbypage'),
    path('api/gettododata',views.gettododata,name='gettododata'),
    path('trips', views.trips_list, name='trips_list'),
    path('savetrip',views.savetrip, name='savetrip'),
    path('trip-planner/<slug:trip_id>',views.trip_planner, name='trip_planner'),
    # path('sitemap.xml', views.sitemap_index),
    # path('sitemap-countries-<int:page>.xml', views.sitemap_countries),
    # path('sitemap-cities-<int:page>.xml', views.sitemap_cities),
    # path('sitemap-country_tags-<int:page>.xml', views.sitemap_country_tags),
    # path('sitemap-city_tags-<int:page>.xml', views.sitemap_city_tags),
    # # path('sitemap-blogs-<int:page>.xml', views.sitemap_blogs),
    # path('sitemap-routes_list_details-<int:page>.xml', views.sitemap_routes_list_details)
    path('sitemap.xml', lambda r: serve_sitemap(r, 'sitemap.xml')),
    re_path(r'^sitemap-(?P<name>[\w\-]+)-(?P<page>\d+)\.xml$', lambda r, name, page: serve_sitemap(r, f'sitemap-{name}-{page}.xml')),

]
