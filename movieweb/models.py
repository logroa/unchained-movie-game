from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

from django.db.models import Max

from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils.timezone import now

class Actor(models.Model):
    name = models.CharField(max_length=200)
    count = models.IntegerField(default = 1)
    tmdbID = models.IntegerField(default = 1)
    discovered_by = models.ForeignKey(User, default=1, blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def refAct(self):
        self.count += 1

class Movie(models.Model):
    title = models.CharField(max_length=200)
    count = models.IntegerField(default = 1)
    tmdbID = models.IntegerField(default = 1)
    discovered_by = models.ForeignKey(User, default=1, blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def refMov(self):
        self.count += 1

class Role(models.Model):
    actor = models.ForeignKey(Actor, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    count = models.IntegerField(default = 1)
    discovered_by = models.ForeignKey(User, default=1, blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.actor.name.upper() + " acted in " + self.movie.title.upper()

    def refRole(self):
        self.count += 1

class Scoreboard(models.Model):
    user = models.ForeignKey(User, default=1, blank=True, null=True, on_delete=models.CASCADE)
    score = models.IntegerField(default = 0)
    date = models.DateTimeField(default=now, blank=True, null=True)

    def __str__(self):
        return self.user.username + ": " + str(self.score) + ", " + str(self.date)

    def incScore(self):
        self.score += 1

class Turn(models.Model):
    user = models.ForeignKey(User, default=1, blank=True, null=True, on_delete=models.CASCADE)
    game_id = models.IntegerField(default = 0)
    movie = models.BooleanField(default = True)
    entity = models.IntegerField(default = 0)
    first = models.BooleanField(default = False)
    last = models.BooleanField(default = False)
    order = models.IntegerField(default = 1)

    def __str__(self):
        return str([self.user.id, self.game_id, self.movie, self.entity, self.first, self.last, self.order])

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    highscore = models.OneToOneField(Scoreboard, on_delete=models.PROTECT, null=True)

    favMov = models.ForeignKey(Movie, related_name="playersFM", on_delete=models.CASCADE, null=True)
    favAct = models.ForeignKey(Actor, related_name="playersFA", on_delete=models.CASCADE, null=True)

    favStart = models.ForeignKey(Actor, related_name="playersFS", on_delete=models.CASCADE, null=True)
    #alwaysEndMov = models.ForeignKey(Turn, related_name="playersEM", on_delete=models.PROTECT)
    #alwaysEndAct = models.ForeignKey(Turn, related_name="playersEA", on_delete=models.PROTECT)

    #actsDisc = models.ManyToManyField(Actor)
    #movsDisc = models.ManyToManyField(Movie)
    #rolsDisc = models.ManyToManyField(Role)

    def __str__(self):
        return self.user.username + "'s profile page"

    #connect our function to User's post_save signal
    #when User is saved, these functions are called
    #...what else could i do with this???
    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        
        try:
            scores = Scoreboard.objects.filter(user = instance)
            best = scores[0]
            for i in scores:
                if i.score > best.score:
                    best = i

            instance.profile.highscore = best

            movies_played = Turn.objects.filter(user=instance).filter(movie=True)
            movies = {}
            for i in movies_played:
                if i.entity in movies:
                    movies[i.entity] += 1
                else:
                    movies[i.entity] = 1
            max_movie_id = max(movies, key = lambda x: movies[x])
            max_movie = Movie.objects.get(id = max_movie_id)
            instance.profile.favMov = max_movie

            actors_played = Turn.objects.filter(user=instance).filter(movie=False)
            actors = {}
            for i in actors_played:
                if i.entity in actors:
                    actors[i.entity] += 1
                else:
                    actors[i.entity] = 1
            max_actor_id = max(actors, key = lambda x: actors[x])
            max_actor = Actor.objects.get(id = max_actor_id)
            instance.profile.favAct = max_actor

            actors_played = Turn.objects.filter(user=instance).filter(first=True)
            actors = {}
            for i in actors_played:
                if i.entity in actors:
                    actors[i.entity] += 1
                else:
                    actors[i.entity] = 1
            max_actor_id = max(actors, key = lambda x: actors[x])
            max_actor = Actor.objects.get(id = max_actor_id)
            instance.profile.favStart = max_actor
            instance.profile.save()
        except:
            instance.profile.save()
    
