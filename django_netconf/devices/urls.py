from django.conf.urls import url

from . import views

app_name = 'devices'

urlpatterns = [
    url(r'^$', views.DeviceListView.as_view(), name='index'),
]