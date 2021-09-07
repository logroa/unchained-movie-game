
from django.http import HttpResponseRedirect, Http404
from django.views.generic.edit import FormView, View, DeleteView
from .forms import ActorForm, MovieForm, RoleForm
from .models import Actor, Movie, Role, Scoreboard, Turn, Profile

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

from difflib import SequenceMatcher

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
            uidG = urlsafe_base64_encode(force_bytes(user.pk))
            tok = account_activation_token.make_token(user)
            message = render_to_string('acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid':uidG,
                'token':tok,
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                        mail_subject, message, to=[to_email]
            )
            try: 
                email.send()
                return HttpResponse('Please confirm your email address to complete the registration')
            except:
                return activate(request, uidG, tok)
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
        return HttpResponse('Email confirmed. Now you can login to your account.')
    else:
        return HttpResponse('Activation link is invalid!')

#render user profile
def userProfile(request, template_name="movieweb/profile.html"):
    prof = Profile.objects.get(user = request.user)
    return render(request, template_name, {"highscore": prof.highscore})

#render top ten highscores
def highScoreboard(request, template_name="movieweb/highscoreboard.html"):
    scores1 = Scoreboard.objects.order_by('-score', 'date')[:10]
    scores = {
        "scores": scores1
    }
    return render(request, template_name, scores)

def scoreboardGameLog(request, game_id, template_name="movieweb/scoreboardGameLog.html"):
    played = Turn.objects.filter(game_id=game_id)
    turns = []    
    sb = Scoreboard.objects.get(id = game_id)
    user = sb.user
    score = sb.score
    for i in played:
        if i.movie:
            ent = Movie.objects.get(id = i.entity).tmdbID

        else:
            ent = Actor.objects.get(id = i.entity).tmdbID
        
        entity = properName(ent, i.movie)
        turns.append(entity)

    entities = {
        "played": turns,
        "username": user.username,
        "score": score
    }

    return render(request, template_name, entities)





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
    user = request.user
    user.save()
    if score > 0:
        t = Turn.objects.get(game_id = game_id, order = score)
        t.last = True
        t.save()
    return render(request, template_name, {"wrong": wrong, "score": score, "game_id": game_id, "dd": dd})

#attempt at identifying minorly misspelled names and titles
#this uses difflib SequenceMatcher
#other solutions in the future could include
#   Hamming Distance: distance between two strings of EQUAL LENGTH (prob not for that reason)
#   Levenshtein Distance: minimum # of single character edits to get from one word to the other (could work, but I don't like lack of proportionality)
#   Jaro-Winkler: similar to hamming but same length but gives more similarity to beginning w same characters (I like this; could be helpful solving article adj issue)
def misspellCorrect(misspell, right):
    return SequenceMatcher(None, misspell, right).ratio()

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

    maxSim = 0.0
    maxSimWord = ""
    for i in data["results"]:
        if standardInput(actor) == standardInput(i['name']):
            actorAdd(request, standardInput(i["name"]), i["id"])
            return i["id"]

    possibleGuys = Actor.objects.filter(name__startswith = standardInput(actor)[0])
    for i in possibleGuys:        
        sim = misspellCorrect(standardInput(actor), i.name)
        if sim > maxSim:
            maxSim = sim
            maxSimWord = i
            if maxSim == 1.0:
                break

    if maxSim >= .85:
        act = Actor.objects.get(tmdbID = maxSimWord.tmdbID)
        act.refAct()
        act.save()
        return maxSimWord.tmdbID

    return -1

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

    maxSim = 0
    maxSimWord = ""
    for i in data["cast"]:
        sim = misspellCorrect(standardInput(movie), standardInput(i["title"]))
        if sim > maxSim:
            maxSim = sim
            maxSimWord = i
            if maxSim == 1.0:
                break

    if maxSim >= .85:
        if Movie.objects.filter(title = standardInput(maxSimWord["title"])).exists():
            mov = Movie.objects.get(tmdbID = maxSimWord["id"])
            mov.refMov()
            mov.save()
        else:
            movieAdd(request, standardInput(maxSimWord["title"]), maxSimWord["id"])
        return maxSimWord["id"]
    return -1

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

    maxSim = 0
    maxSimWord = ""
    for i in newData["cast"]:
        sim = misspellCorrect(standardInput(actor), standardInput(i["name"]))
        if i["known_for_department"] == "Acting" and sim > maxSim:
            maxSim = sim
            maxSimWord = i
            if maxSim == 1.0:
                break

    if maxSim >= .85:
        if Actor.objects.filter(name = standardInput(maxSimWord["name"])).exists():
            act = Actor.objects.get(tmdbID = maxSimWord["id"])
            act.refAct()
            act.save()
        else:
            actorAdd(request, standardInput(maxSimWord["name"]), maxSimWord["id"])
        return maxSimWord["id"]
    return -1

#check if entity has been played this game
def noRepeats(game_id, entity, movieOr):
    if Turn.objects.filter(game_id = game_id, entity = entity, movie = movieOr).exists():
        if not movieOr and Actor.objects.get(id = entity).name == "kevinbacon":
            return True
        return False
    return True

#input standardizer - removing spaces and punctuation
def standardInput(entity):
    entity = re.sub(r'[&]', 'and', entity)
    return re.sub(r'[^\w]', '', entity).lower()

#actor turn helper
def getActor(request, actor, movie):
    try:
        rol = Role.objects.get(actor = Actor.objects.get(name = standardInput(actor)).id, movie=Movie.objects.get(tmdbID = movie).id)
        rol.refRole()
        rol.save()
  
        act = Actor.objects.get(name = standardInput(actor))
        act.refAct()
        act.save()

        return act.tmdbID
    except:
        return movieCast(request, actor, movie)

#movie turn helper
def getMovie(request, actor, movie):
    try:
        rol = Role.objects.get(actor = Actor.objects.get(tmdbID = actor).id, movie=Movie.objects.get(title = standardInput(movie)).id)
        rol.refRole()
        rol.save()
  
        mov = Movie.objects.get(title = standardInput(movie))
        mov.refMov()
        mov.save()

        return mov.tmdbID
    except:
        return actorCredits(request, actor, movie)

#actor helper for beginning of the game
def actorStart(request, actor):
    try:
        act = Actor.objects.get(name=standardInput(actor))
        act.refAct()
        act.save()
        return act.tmdbID
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

            if gA > 0 and noRepeats(game_id, Actor.objects.get(tmdbID = gA).id, False):
                score += 1
           
                scoreBoarder(game_id)
                turner(request, game_id, False, Actor.objects.get(tmdbID = gA).id, False, False, score)
                roleAdd(request, gA, entity)

                return redirect("movieTurn", game_id = game_id, entity = gA, score = score)

            else:
                dd = 1
                if gA < 0:
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

            if gM > 0 and noRepeats(game_id, Movie.objects.get(tmdbID = gM).id, True):
                score += 1
           
                scoreBoarder(game_id)
                turner(request, game_id, True, Movie.objects.get(tmdbID = gM).id, False, False, score)
                roleAdd(request, entity, gM)

                return redirect("actorTurn", game_id = game_id, entity = gM, score = score)

            else:
                dd = 1
                if gM < 0:
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

            aS = actorStart(request, name)
            if aS > 0:
                score += 1

                sb.incScore()
                sb.save()

                turner(request, sb.id, False, Actor.objects.get(tmdbID = aS).id, True, False, 1)

                return redirect("movieTurn", game_id = sb.id, entity = aS, score = score)
            
            else:
                return redirect("gameOver", game_id = sb.id, wrong = name, score = 0, dd = 0)
    
    else:
        form = ActorForm()
        return render(request, template_name, {'form': form})

