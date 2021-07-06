from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

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
    date = models.DateTimeField(default=datetime.now(), blank=True, null=True)

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
        return [self.user.id, self.game_id, self.movie, self.entity, self.first, self.last, self.order]

        
            

class playerRole(models.Model):
    user = models.ForeignKey(User, default=1, blank=True, null=True, on_delete=models.CASCADE)
    role_id = models.IntegerField(default = 0)
    count = models.IntegerField(default = 1)

    def __str__(self):
        return self.user.username + ": " + Role.objects.get(id = self.role_id) + ", " + str(self.count)

    def refConnect(self):
        self.count += 1