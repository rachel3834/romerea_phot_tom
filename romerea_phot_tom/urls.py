"""django URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.urls import path, include
from django.conf.urls import url
from custom_views import views

app_name = 'custom_views'

urlpatterns = [
    path('', include('tom_common.urls')),
    url(r'^search/$', views.search, name='search'),
    url(r'^search/name=(?P<name>[0-9a-zA-Z]+)/$', views.search, {'search_type':'name'}, name='search'),
    url(r'^search/target_name/$', views.search, {'search_type':'name'}, name='search_target_name'),
    url(r'^search/target_position/$', views.search, {'search_type':'position'}, name='search_target_position'),

]

urlpatterns += [url(r'^silk/', include('silk.urls', namespace='silk'))]
