from django.conf.urls import url

from . import views

app_name = 'get'

urlpatterns = [
    url(r'^$', views.single_get, name='index'),
]