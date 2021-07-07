
from django.http import HttpResponseRedirect, Http404
from django.views.generic.edit import FormView, View, DeleteView
from .forms import ActorForm, MovieForm, RoleForm
from .models import Actor, Movie, Role, Scoreboard, Turn, playerRole

from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .forms import SignupForm
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.contrib.auth.models import User
from django.core.mail import EmailMessage

import random
import requests, json, re
from datetime import datetime


#user signup / signin
def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            mail_subject = 'Activate your Movie Account.'
            message = render_to_string('acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                        mail_subject, message, to=[to_email]
            )
            email.send()
            return HttpResponse('Please confirm your email address to complete the registration')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        # return redirect('home')
        context = {'uidb64':uidb64, 'token': token}
        #return render(request, 'acc_active_email.html', context)
        return HttpResponse('Thank you for your email confirmation. Now you can login to your account.')
    else:
        return HttpResponse('Activation link is invalid!')

#misc
def randMov():
   firstmovies = Movie.objects.raw("SELECT id, title from movieweb_movie ORDER BY count DESC LIMIT 5")
   index = random.randint(0, 4)
   return firstmovies[index]

#database helpers
def scoreBoarder(id):
    sb = Scoreboard.objects.get(id=id)
    sb.incScore()
    sb.save()

def turner(request, game_id, movieOr, entity, first, last, order):
    tn = Turn(user = request.user, game_id=game_id, movie = movieOr, 
              entity = entity, first = first, last = last, order = order)
    tn.save()

def actorAdd(request, actor, tmdbID):
    a = Actor(name=actor, tmdbID = tmdbID, discovered_by=request.user)
    a.save()

def movieAdd(request, movie, tmdbID):
    m = Movie(title=movie, tmdbID = tmdbID, discovered_by=request.user)
    m.save()

def roleAdd(request, tmdbIDa, tmdbIDm):
    if not Role.objects.filter(actor=Actor.objects.get(tmdbID = tmdbIDa), movie=Movie.objects.get(tmdbID = tmdbIDm)).exists():
        r = Role(actor=Actor.objects.get(tmdbID = tmdbIDa), movie=Movie.objects.get(tmdbID = tmdbIDm), discovered_by=request.user)
        r.save()

#end of game page
def gameOver(request, game_id, wrong, score, dd, template_name = 'movieweb/gameover.html'):
    if score > 0:
        t = Turn.objects.get(game_id = game_id, order = score)
        t.last = True
        t.save()
    return render(request, template_name, {"wrong": wrong, "score": score, "game_id": game_id, "dd": dd})

#get proper movie or actor name
def properName(entity, movieOr):
    key = "582466104084889c8affefe2494c9278"
    token = '''eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI1ODI0NjYxMD
                        QwODQ4ODljOGFmZmVmZTI0OTRjOTI3OCIsInN1YiI6I
                        jYwYjdmMWQ2NjkwNWZiMDA2ZjYyMDYyMSIsInNjb3Bl
                        cyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.44pR
                        dm5gZVVr5ZyJ9P8yPGdhtFEM79IeKGuwKYqNbDc'''
    url = "https://api.themoviedb.org/3/"   

    if movieOr:
        link = url + "movie/" + str(entity) + "?api_key=" + key + "&language=en-US"
        response = requests.get(link).text
        data = json.loads(response)
        return data["title"]
    
    else:
        link = url + "person/" + str(entity) + "?api_key=" + key + "&language=en-US"
        response = requests.get(link).text
        data = json.loads(response)
        return data["name"]

#validate actor at beginning of game
def validateActor(request, actor):
    key = "582466104084889c8affefe2494c9278"
    token = '''eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI1ODI0NjYxMD
                        QwODQ4ODljOGFmZmVmZTI0OTRjOTI3OCIsInN1YiI6I
                        jYwYjdmMWQ2NjkwNWZiMDA2ZjYyMDYyMSIsInNjb3Bl
                        cyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.44pR
                        dm5gZVVr5ZyJ9P8yPGdhtFEM79IeKGuwKYqNbDc'''
    url = "https://api.themoviedb.org/3/"

    link = url + "search/person?api_key=" + key + "&query=" + actor
    response = requests.get(link).text
    data = json.loads(response)

    if data["total_results"] == 0:
        return False
    else:
        for i in data["results"]:
            if standardInput(actor) == standardInput(i['name']):
                actorAdd(request, standardInput(i["name"]), i["id"])
                return True
        return False

#see if inputted movie is in actor's credits
def actorCredits(request, actor, movie):
    key = "582466104084889c8affefe2494c9278"
    token = '''eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI1ODI0NjYxMD
                        QwODQ4ODljOGFmZmVmZTI0OTRjOTI3OCIsInN1YiI6I
                        jYwYjdmMWQ2NjkwNWZiMDA2ZjYyMDYyMSIsInNjb3Bl
                        cyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.44pR
                        dm5gZVVr5ZyJ9P8yPGdhtFEM79IeKGuwKYqNbDc'''
    url = "https://api.themoviedb.org/3/"

    link = url + "person/" + str(actor) + "/movie_credits?api_key=" + key + "&language=en-US"
    response = requests.get(link).text
    data = json.loads(response)   

    for i in data["cast"]:
        if standardInput(movie) == standardInput(i["title"]):
            movieAdd(request, standardInput(i["title"]), i["id"])
            return True
    return False

#see if inputted actor is in the cast of the movie
def movieCast(request, actor, movie):
    key = "582466104084889c8affefe2494c9278"
    token = '''eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI1ODI0NjYxMD
                        QwODQ4ODljOGFmZmVmZTI0OTRjOTI3OCIsInN1YiI6I
                        jYwYjdmMWQ2NjkwNWZiMDA2ZjYyMDYyMSIsInNjb3Bl
                        cyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.44pR
                        dm5gZVVr5ZyJ9P8yPGdhtFEM79IeKGuwKYqNbDc'''
    url = "https://api.themoviedb.org/3/"

    newLink = url + "movie/" + str(movie) + "/credits?api_key=" + key + "&language=en-US"
    newResponse = requests.get(newLink).text
    newData = json.loads(newResponse)

    for i in newData["cast"]:
        if i["known_for_department"] == "Acting" and standardInput(actor) == standardInput(i["name"]):
            actorAdd(request, standardInput(i["name"]), i["id"])
            return True
    return False

#check if entity has been played this game
def noRepeats(game_id, entity, movieOr):
    if Turn.objects.filter(game_id = game_id, entity = entity, movie = movieOr).exists():
        return False
    
    return True

#input standardizer - removing spaces and punctuation
def standardInput(entity):
    entity = re.sub(r'[&]', 'and', entity)
    return re.sub(r'[^\w]', '', entity).lower()

#actor turn helper
def getActor(request, actor, movie):
    try:
        rol = Role.objects.get(actor = Actor.objects.get(name = standardInput(actor)).name, movie=Movie.objects.get(tmdb = movie).title)
        rol.refRole()
        rol.save()
  
        act = Actor.objects.get(name = standardInput(name))
        act.refAct()
        act.save()

        return True
    except:
        return movieCast(request, actor, movie)

#movie turn helper
def getMovie(request, actor, movie):
    try:
        rol = Role.objects.get(actor = Actor.objects.get(tmdbID = actor).name, movie=Movie.objects.get(title = standardInput(movie)).title)
        rol.refRole()
        rol.save()
  
        mov = Movie.objects.get(title = standardInput(movie))
        mov.refMov()
        mov.save()

        return True
    except:
        return actorCredits(request, actor, movie)

#actor helper for beginning of the game
def actorStart(request, actor):
    try:
        act = Actor.objects.get(name=standardInput(actor))
        act.refAct()
        act.save()
        return True
    except:
        return validateActor(request, actor)

#actor turn
def actorTurn(request, game_id, entity, score, template_name= 'movieweb/actorturn.html'):

    if request.method == 'POST':
        form = ActorForm(request.POST)
        if form.is_valid():

            name = form.cleaned_data['name'].lower()
            form = ActorForm()
            
            gA = getActor(request, name, entity) 

            if gA and noRepeats(game_id, Actor.objects.get(name = standardInput(name)).id, False):
                score += 1
           
                scoreBoarder(game_id)
                turner(request, game_id, False, Actor.objects.get(name = standardInput(name)).id, False, False, score)
                roleAdd(request, Actor.objects.get(name=standardInput(name)).tmdbID, entity)

                return redirect("movieTurn", game_id = game_id, entity = Actor.objects.get(name=standardInput(name)).tmdbID, score = score)

            else:
                dd = 1
                if not gA:
                    dd = 0
                return redirect("gameOver", game_id = game_id, wrong = name, score = score, dd = dd)
    else:
        form = ActorForm()
        prev = entity
        ent = properName(prev, True)
    return render(request, template_name, {'form': form, 'entity': ent, 'score': score, 'game_id': game_id})   

#movie turn
def movieTurn(request, game_id, entity, score, template_name = 'movieweb/movieturn.html'):

    if request.method == 'POST':
        form = MovieForm(request.POST)
        if form.is_valid():

            title = form.cleaned_data['title'].lower()
            form = MovieForm()

            gM = getMovie(request, entity, title)

            if gM and noRepeats(game_id, Movie.objects.get(title = standardInput(title)).id, True):
                score += 1
           
                scoreBoarder(game_id)
                turner(request, game_id, True, Movie.objects.get(title = standardInput(title)).id, False, False, score)
                roleAdd(request, entity, Movie.objects.get(title=standardInput(title)).tmdbID)

                return redirect("actorTurn", game_id = game_id, entity = Movie.objects.get(title=standardInput(title)).tmdbID, score = score)

            else:
                dd = 1
                if not gM:
                    dd = 0
                return redirect("gameOver", game_id = game_id, wrong = title, score = score, dd = dd)
    else:
        form = MovieForm()
        prev = entity
        ent = properName(prev, False)
    return render(request, template_name, {'form': form, 'entity': ent, 'score': score, 'game_id': game_id})    

#start the game w actor
def GameStarter(request, template_name = 'movieweb/index.html'):

    score = 0
    
    if request.method == 'POST':
        form = ActorForm(request.POST)
        if form.is_valid():
            
            sb = Scoreboard(user = request.user, date = datetime.now())
            sb.save()

            name = form.cleaned_data['name'].lower()
            form = ActorForm()

            if actorStart(request, name):
                score += 1

                sb.incScore()
                sb.save()

                turner(request, sb.id, False, Actor.objects.get(name = standardInput(name)).id, True, False, 1)

                return redirect("movieTurn", game_id = sb.id, entity = Actor.objects.get(name = standardInput(name)).tmdbID, score = score)
            
            else:
                return redirect("gameOver", game_id = sb.id, wrong = name, score = 0, dd = 0)
    
    else:
        form = ActorForm()
        return render(request, template_name, {'form': form})

