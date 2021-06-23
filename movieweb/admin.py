from django.contrib import admin

from .models import Actor
from .models import Movie
from .models import Role
from .models import Scoreboard
from .models import Turn

# Register your models here.
admin.site.register(Actor)
admin.site.register(Movie)
admin.site.register(Role)
admin.site.register(Scoreboard)
admin.site.register(Turn)