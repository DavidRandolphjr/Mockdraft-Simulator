from email.policy import default
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext as _


class User(AbstractUser):
    drafts = models.ManyToManyField("Drafts", related_name="drafts")
    def serialize(self):
        return{
            "drafts": [draft.rooms for draft in self.drafts.all()]
        }
        
# Rankings() is meant to take the information from an uploaded csv file (Rankingslist.csv)
class Rankings (models.Model):
    tiers = models.IntegerField(_("TIERS"), max_length=15, null=True)
    playername = models.CharField(_("PLAYER NAME"), max_length=50, null=True)
    team = models.CharField(_("TEAM"), max_length=50, null=True)
    posrank = models.CharField(_("POSRANK"), max_length=50, null=True)
    pos = models.CharField(_("POS"), max_length=50, null=True)
    byeweek = models.CharField(_("BYE WEEK"), max_length=15, null=True)
    age = models.CharField(_("AGE"), max_length=15, null=True)
    rank = models.IntegerField(_("RK"), max_length=15, null=True)
    def serialize(self):  
        return{
            "rank": self.rank,
            "tiers": self.tiers,
            "playername": self.playername,
            "team": self.team,
            "pos": self.pos,
            "posrank": self.posrank,
            "byeweek": self.byeweek,
            "age": self.age
        }

# Room() records all of the parameters for the draftroom
class Room(models.Model):
    room_name = models.CharField(max_length=50)
    team = models.ManyToManyField("Teams", related_name="teams_list")
    drafted = models.ManyToManyField("Drafted", related_name="drafted")
    rounds = models.IntegerField(default=15)
    rounds_remaining = models.IntegerField(default=15)
    started = models.BooleanField(default=False)
    user_turn = models.CharField(max_length=50, default="AI")
    timer = models.IntegerField(default=0)
    def serialize(self):
        return{
                "drafted": [draftee.player for draftee in self.drafted.all()],
                "teams": [teams for teams in self.team.all()],
                
            }

# Drafted() stores the data for every drafted player
class Drafted(models.Model):
    player = models.CharField( max_length=50)

# Teams() stores the data for every drafted team
class Teams(models.Model):
    room_id= models.ForeignKey("Room", on_delete=models.CASCADE, related_name="roomid_list")
    owner = models.CharField(max_length=50, default="AI")
    roster = models.ManyToManyField("Roster", related_name="player_roster")
    req_position = models.CharField(max_length=200)
    def serialize(self):

        return{
            "roster": [theroster.team_players for theroster in self.roster.all()],
            "pos": [theroster.pos for theroster in self.roster.all()],
            "owner": self.owner,
            "id": self.id,
            "req_position": self.req_position
        }
    
# When editing teams we will filter teams by user.id and add drafted players to roster
class Roster(models.Model):
    team_players = models.CharField(max_length=50)
    pos = models.CharField(max_length=50)

# Drafts() just keeps the links for all of the drafts that have happened.
class Drafts(models.Model):
    rooms = models.CharField(max_length=100)