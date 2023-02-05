import json
import random
import ast
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.db.models import Q
from .models import Room, Roster, Drafted, Rankings, Teams, User, Drafts


class MyConsumer(WebsocketConsumer):
    
    def connect(self):
        self.room_group_name = 'test'
        
    
        
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        print("we are in the starter area")

        self.accept()
        self.send(text_data=json.dumps({
            'type':'firstload',
            'message':"doesnt go anywhere"
            #This can just send out the initial list
        }))
        

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        # if command is "claim", message is team roster number. If its "draft", message is name of player drafted.
        message = text_data_json['message']
        roomid = text_data_json['roomid']
        username = text_data_json['username']
        command = text_data_json['command']
        counter = 0
        print("this is the command",command)

        # simulateddraft() auto picks for AI controlled teams
        def simulatedraft():
            room= Room.objects.get(id = int(roomid))
            room.timer =0
            room.save()
            room_drafted = Room.objects.get(pk = int(roomid))
            # gets list of undrafted players
            players = Rankings.objects.all().exclude(playername__in= room_drafted.serialize()['drafted'])
            player_list =[player.serialize() for player in players]
            # gets list of team owners
            teams = Teams.objects.filter(room_id= roomid)
            team_owners =[team.serialize()['owner'] for team in teams]     
            counter = team_owners.index(username) +1
            flipped= False
            # Depending on how many rounds there are we set the variable rounds_left equal to room.rounds_remaining +1 or just room.rounds_remaining.
            # We do this to maintain the right flipping order
            # Lines 60-94 exist to make sure the draft order is correct
            if room.rounds != 15:
                rounds_left = room.rounds_remaining +1
            else:
                rounds_left = room.rounds_remaining

            if counter >= len(team_owners) and rounds_left%2!=0:
                team_owners=team_owners[::-1]
                counter=0
                flipped=True
                room.rounds_remaining= int(room.rounds_remaining) -1
                room.save()

            # flipped will later determine the direction for the list
            elif counter -1 == len(team_owners) or counter -1 == 0 and rounds_left%2==0:
                counter=0
                flipped=False
                room.rounds_remaining= int(room.rounds_remaining) -1
                room.save()
            elif rounds_left%2==0:
                flipped= True
                counter = (len(team_owners)-1) - team_owners.index(username)+1 
                if counter <0:
                    counter = 0
                    room.rounds_remaining= int(room.rounds_remaining) -1
                    room.save()
                team_owners = team_owners[::-1]    

            

            elif counter -1 == len(team_owners)  and rounds_left%2!=0:
                    counter=0
                    flipped=True
                    room.rounds_remaining= int(room.rounds_remaining) -1
                    room.save()
                    team_owners = team_owners[::-1]

            
            # After the user drafts, loop through team owners list and draft for all AI      
            while team_owners[counter] =="AI" and room.rounds_remaining > 0:
                # this creates a list of the excluded positions if the draft is currently moving in the opposite diraction
                if flipped:
                    exclude_pos= ast.literal_eval(Teams.objects.filter(room_id=roomid)[len(team_owners)-counter-1].req_position)
    
                else:
                    exclude_pos= ast.literal_eval(Teams.objects.filter(room_id=roomid)[counter].req_position)
                players = players.exclude(~Q (pos__in= exclude_pos ))
                player_list =[player.serialize() for player in players]
                
                room= Room.objects.get(id = int(roomid))
                player_drafted= player_list[random.randrange(0,9)]
                drafted = Drafted(
                    player = player_drafted['playername']
                )
                drafted.save()
                room.drafted.add(drafted)
                # save player and position to Roster table, and then add it to team_roster
                if flipped:
                    team_roster = Teams.objects.filter(room_id=roomid)[len(team_owners)-counter -1]
                    the_roster = Roster(
                        team_players = player_drafted['playername'],
                        pos = player_drafted['pos']
                    )
                    the_roster.save()
                    team_roster.roster.add(the_roster)
                    # now we just have to update team_roster's req_position
                else:
                    team_roster = Teams.objects.filter(room_id=roomid)[counter]
                    the_roster = Roster(
                        team_players = player_drafted['playername'],
                        pos = player_drafted['pos']
                    )
                    the_roster.save()
                    team_roster.roster.add(the_roster)

                # remove position of drafted player from team_roster.req_position
                position_list = ast.literal_eval(team_roster.req_position)
                position_index = position_list.index(player_drafted['pos'])
                position_list.pop(position_index)
    
                team_roster.req_position= position_list
                team_roster.save()
                counter +=1
                players = Rankings.objects.all().exclude(playername__in= room_drafted.serialize()['drafted'])
                player_list =[player.serialize() for player in players]
                # reset counter and flip list once we've reached the end of the list for drafting users
                if counter == len(team_owners):
                    team_owners = team_owners[::-1]
                    counter=0
                    if flipped:
                        flipped=False
                    else:
                        flipped=True

                    room.rounds_remaining= int(room.rounds_remaining) -1
                    room.save()
            room= Room.objects.filter(id = int(roomid)).update(user_turn= team_owners[counter])
            return(async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type':'draft_message',
                    'message':message,
                    'turn': team_owners[counter],
                    'started': Room.objects.get(pk = int(roomid)).started,
                    'room_num': roomid
                    #This can update and display the new list
                }
            ))

        # this is essentially here to just get the user to interact with the page
        if command =="rejoin":
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type':'draft_message',
                    'message':message,
                    'turn': Room.objects.get(id=int(roomid)).user_turn,
                    'started': Room.objects.get(pk = int(roomid)).started,
                    'room_num': roomid
                }
            )

        # assigns a team to the user to claimed it
        elif command == "claim":
            theteam = Teams.objects.filter(room_id=roomid)[int(message[0])-1]
            teams = Teams.objects.filter(room_id= roomid, id= theteam.id)
            teams.update(owner= username)
            user_drafts = User.objects.get(username= username)
            print(message)
            draftrooms = Drafts(
                rooms = message[1]
            )
            draftrooms.save()
            user_drafts.drafts.add(draftrooms)
        
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type':'draft_message',
                    'message':message,
                    'turn':"nothing yet",
                    'started': Room.objects.get(pk = int(roomid)).started,
                    'room_num': roomid
                }
            )

            
        # takes the user entered inputs
        elif command == "draft":
            room= Room.objects.get(id = int(roomid))
            room.timer =0
            room.save()
            drafted = Drafted(
                player = message[0]
            )
            drafted.save()
            room.drafted.add(drafted)

            team_roster = Teams.objects.get(room_id=roomid, owner=username)
            the_roster = Roster(
                team_players = message[0],
                pos = message[1]
            )
            the_roster.save()
            team_roster.roster.add(the_roster)
  
            return(simulatedraft())
            
            
        elif command == "autodraft":
            room= Room.objects.get(id = int(roomid))
            room.timer =0
            room.save()
            room= Room.objects.filter(id = int(roomid)).update(started= True )
            room_drafted = Room.objects.get(pk = int(roomid))
            #gets list of undrafted players
            players = Rankings.objects.all().exclude(playername__in= room_drafted.serialize()['drafted'])
            teams = Teams.objects.filter(room_id= roomid)
            team_owners =[team.serialize()['owner'] for team in teams]
            counter = team_owners.index(username) 
            exclude_pos= ast.literal_eval(Teams.objects.filter(room_id=roomid)[counter].req_position)
            players = players.exclude(~Q (pos__in= exclude_pos ))
            player_list =[player.serialize() for player in players]
            #gets list of team owners
            
            
            
            print("this should print once")
            
            print((team_owners)[counter])
            room= Room.objects.get(id = int(roomid))
            player_drafted= player_list[random.randrange(0,9)]
            drafted = Drafted(
                player = player_drafted[ 'playername']
            )
            drafted.save()
            room.drafted.add(drafted)

            team_roster = Teams.objects.filter(room_id=roomid)[counter]
            the_roster = Roster(
                team_players = player_drafted[ 'playername'],
                pos = player_drafted['pos']
            )
            position_list = ast.literal_eval(team_roster.req_position)
            position_index = position_list.index(player_drafted['pos'])
            position_list.pop(position_index)
            #right now, position_list is being treated as a string, not a list. We have to fix that.
            print("this is the index, player, and position",position_list, player_drafted['playername'], player_drafted['pos'])
            team_roster.req_position= position_list
            team_roster.save()
            the_roster.save()
            team_roster.roster.add(the_roster)
            players = Rankings.objects.all().exclude(playername__in= room_drafted.serialize()['drafted'])
            player_list =[player.serialize() for player in players]
            room= Room.objects.filter(id = int(roomid)).update(user_turn= team_owners[counter])
            
            return(simulatedraft())

        else:
            room= Room.objects.filter(id = int(roomid)).update(started= True )
            room_drafted = Room.objects.get(pk = int(roomid))
            #gets list of undrafted players
            players = Rankings.objects.all().exclude(playername__in= room_drafted.serialize()['drafted'])
            player_list =[player.serialize() for player in players]
            #gets list of team owners
            teams = Teams.objects.filter(room_id= roomid)
            team_owners =[team.serialize()['owner'] for team in teams]
            counter = 0
            print("this should print once")
            while team_owners[counter] =="AI":
                print((team_owners)[counter])
                room= Room.objects.get(id = int(roomid))
                player_drafted= player_list[random.randrange(0,9)]
                drafted = Drafted(
                    player = player_drafted[ 'playername']
                )
                drafted.save()
                room.drafted.add(drafted)

                team_roster = Teams.objects.filter(room_id=roomid)[counter]
                the_roster = Roster(
                    team_players = player_drafted[ 'playername'],
                    pos = player_drafted['pos']
                )
                position_list = ast.literal_eval(team_roster.req_position)
                position_index = position_list.index(player_drafted['pos'])
                position_list.pop(position_index)
                #right now, position_list is being treated as a string, not a list. We have to fix that.
                print("this is the index, player, and position",position_list, player_drafted['playername'], player_drafted['pos'])
                team_roster.req_position= position_list
                team_roster.save()
                the_roster.save()
                team_roster.roster.add(the_roster)
                counter +=1
                players = Rankings.objects.all().exclude(playername__in= room_drafted.serialize()['drafted'])
                player_list =[player.serialize() for player in players]
                if counter == len(team_owners):
                    #once everything is working, we will instead flip the list and reset counter to 0
                    team_owners=team_owners[::-1]
                    counter=0
            room= Room.objects.filter(id = int(roomid)).update(user_turn= team_owners[counter])
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type':'draft_message',
                    'message':message,
                    'turn': team_owners[counter],
                    'started': Room.objects.get(pk = int(roomid)).started,
                    'room_num': roomid
                    #This can update and display the new list
                }
            )
            return HttpResponseRedirect(reverse("index"))
        

    def draft_message(self, event):
        message = event['message']
        turn = event['turn']
        started = event['started']
        room_num = event['room_num']
        print("this is turn and message", turn, message)
        

        self.send(text_data=json.dumps({
            'type': room_num,
            'message':message,
            'turn':turn,
            'started': started
            #we can use the type of chat to update the player
        }))



