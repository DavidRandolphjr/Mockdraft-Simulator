from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("Mydrafts", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("player_list", views.player_list, name="player_list"),
    path("teamsinfo/<int:roomid>", views.teamsinfo, name="teamsinfo"),
    path("teamrosters/<int:roomid>", views.teamsinfo, name="teamsinfo"),
    path("timer/<int:roomid>", views.timer, name="timer"),
    path("rooms", views.rooms, name="rooms"),
    path("draftroom/<int:id>/<str:name>/", views.draftroom, name="draftroom")
]