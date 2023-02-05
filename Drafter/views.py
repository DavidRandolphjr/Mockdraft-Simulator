import json
import time
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import os

from .models import User, Rankings, Room, Teams, Roster

# Create your views here.
@csrf_exempt
@login_required
def index(request):
    print(request.user)
    user_drafts = User.objects.get(username = request.user)
    return render(request, "Drafter/index.html",user_drafts.serialize())

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "Drafter/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "Drafter/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("login"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "Drafter/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "Drafter/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "Drafter/register.html")

def player_list(request):
    roomid = str(request.GET.get("roomid"))
    room_drafted = Room.objects.get(pk = int(roomid))
    players = Rankings.objects.all().exclude(playername__in= room_drafted.serialize()['drafted'])
    return JsonResponse([player.serialize() for player in players], safe=False)

# rooms() takes info from rooms.html and redirects user to draftroom.html if room either already exists, or is unique.
# If room number exists with different name, we get an error.
def rooms(request):
    if request.method == "GET":
        return render(request, "Drafter/rooms.html")
    elif request.method == "POST":
        roomId = request.POST.get("room-id", None)
        roomname = request.POST.get("room-name", None)
        if roomId and roomname:
            try: 
                room = Room.objects.get(id=roomId, room_name=roomname)
                return redirect(f"/draftroom/{room.id}/{roomname}/")
            except Room.DoesNotExist:
                #messages.error(request, "Room does not exist.")
                print("whoops")
                return redirect("index")
            
        if not roomId and not roomname:
            print("shucks")
            #messages.error(request, "Room does not exist.")
            return redirect("index")
                
        else:
            room = Room.objects.create()
            team_amount= request.POST.get("teams_amount","")
            req_positions= request.POST.get("positions","")
            # positions sets what the ai will need when auto-picking the team.
            positions = {
                "standard": ["QB","RB","RB","WR","WR","TE","WR","TE","RB","RB","WR","WR","RB","QB","K"],
                "2flex": ["QB","RB","RB","WR","WR","TE","WR","TE","RB","RB","WR","WR","RB","QB","WR","K"],
                "nokicker": ["QB","RB","RB","WR","WR","TE","WR","TE","RB","RB","WR","WR","RB","QB"],
                }
            # create and add teams to the Room model
            for i in range(0,int(team_amount)):
                team = Teams(
                    room_id = Room.objects.get(pk = room.id),
                    req_position = positions[str(req_positions)]
                )

                team.save()
                room.team.add(team)
                room.rounds = len(positions[str(req_positions)])
                room.rounds_remaining = len(positions[str(req_positions)])
                room.room_name = roomname
                room.save()
                
            return redirect(f"/draftroom/{room.id}/{roomname}/")

# create the draft room   
def draftroom(request, id=None, name=None):
    # Attempt to create the draftroom
    print("this is the room name",name)
    try:
        room = Room.objects.get(id=id, room_name=name)
        room_teams = Room.objects.filter(id=id)
        teams_list =[teams.serialize()["teams"] for teams in room_teams][0]
        number_of_teams = []
        for i in range(1, len(teams_list) +1):
            number_of_teams.append(i)
        number_of_rounds = []
        for i in range(1,room.rounds +1):
            number_of_rounds.append(i)
        print("it still got to here")
        return render(request, "Drafter/draftroom.html", {"room": room.id, "name": name, "started":room.started, "range_list": number_of_teams, "rounds": number_of_rounds})
    # If room doesnt exist
    except Room.DoesNotExist:
        print("the problem is here")
        #messages.error(request, "Room does not exist.")
        return redirect("index")
 

def teamsinfo(request, roomid):
    teams = Teams.objects.filter(room_id= roomid)
    return JsonResponse([team.serialize() for team in teams], safe=False)

# create timer for each pick.
def timer(request, roomid):
    room_time= Room.objects.get(pk = roomid)
    current_time= time.time()
    if room_time.timer == 0:
        room_time.timer = current_time
        room_time.save()
        return JsonResponse(0, safe=False)

    if current_time -room_time.timer >= 60:
        #Instead of resetting the timer to 0 here, I will just set the timer to 0 in consumers.py when a draft pick is made.
        return JsonResponse(60, safe=False)
    else:
        print("this is where it gets", current_time- room_time.timer )
        return JsonResponse(int(current_time -room_time.timer), safe=False)