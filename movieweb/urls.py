from django.urls import path
from django.conf.urls import url
from . import views
# from movieweb.views import SignUpView

urlpatterns = [
    url(r'^signup/$', views.signup, name='signup'),
    path('activate/<slug:uidb64>/<slug:token>/',
        views.activate, name='activate'),
    path('', views.GameStarter, name='movieweb'),
    path('<int:game_id>/<str:entity>/<int:score>/', views.movieTurn, name='movieTurn')
]