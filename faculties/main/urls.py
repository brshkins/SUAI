from django.urls import path
from . import views
urlpatterns = [
    path('', views.index, name = 'index'),
    path('test/', views.test_views, name='test'),
    path('test/result/', views.test_result, name ='test_result'),
    path('nps/', views.nps_submit, name='nps_submit')
]