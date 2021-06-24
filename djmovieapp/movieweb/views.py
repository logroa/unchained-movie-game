
from django.http import HttpResponseRedirect, Http404
from django.views.generic.edit import FormView, View, DeleteView
from .forms import ActorForm, MovieForm, RoleForm
from .models import Actor, Movie, Role, Scoreboard, Turn

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
import requests, json
from datetime import datetime


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

def randMov():
   firstmovies = Movie.objects.raw("SELECT id, title from movieweb_movie ORDER BY count DESC LIMIT 5")
   index = random.randint(0, 4)
   return firstmovies[index]

def scoreBoarder(id):
    sb = Scoreboard.objects.get(id=id)
    sb.incScore()
    sb.save()

def turner(request, game_id, movieOr, entity, first, last, order):
    tn = Turn(user = request.user, game_id=game_id, movie = movieOr, 
              entity = entity, first = first, last = last, order = order)
    tn.save()

def gameOver(request, game_id, entity, score, template_name = 'movieweb/gameover.html'):
    return render(request, template_name, {"entity": entity, "score": score, "game_id": game_id})


def movieTurn(request, game_id, entity, score, template_name = 'movieweb/movieturn.html'):

    if request.method == 'POST':
        form = Movie(request.POST)
        if form.is_valid():
            title = form.cleaned_data['title'].lower()
            mov = getActor(request, title)
            form = MovieForm()
            #if act != " ":
            #    score += 1  

        args = {'form': form, 'title': title, 'entity': mov, 'score': score}
    
        return  render(request, template_name, args)
    else:
        form = MovieForm()
        return render(request, template_name, {'form': form, 'entity': entity, 'score': score, 'game_id': game_id})    

#validate actor at beginning of game
def validateActor(actor):
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
        return True

def actorApi(actor, movie):

    key = "582466104084889c8affefe2494c9278"
    token = '''eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI1ODI0NjYxMD
                        QwODQ4ODljOGFmZmVmZTI0OTRjOTI3OCIsInN1YiI6I
                        jYwYjdmMWQ2NjkwNWZiMDA2ZjYyMDYyMSIsInNjb3Bl
                        cyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.44pR
                        dm5gZVVr5ZyJ9P8yPGdhtFEM79IeKGuwKYqNbDc'''
    url = "https://api.themoviedb.org/3/"

    link = url + "search/movie?api_key=" + key + "&query=" + movie
    response = requests.get(link).text
    data = json.loads(response)

    for i in data["results"]:
        if movie == i["title"].lower():
            break
    newLink = url + "movie/" + str(i["id"]) + "/credits?api_key=" + key + "&language=en-US"
    newResponse = requests.get(newLink).text
    newData = json.loads(newResponse)
            
    for j in newData["cast"]:
        if j["known_for_department"] == "Acting" and actor == j["name"].lower():
            return True
    return False

def actorAdd(request, actor):
    a = Actor(name=actor, discovered_by=request.user)
    a.save()

def getActor(request, actor, movie):
    try:
        act = Actor.objects.get(name=actor)
        act.refAct()
        act.save()
        return True
    except:
        if actorApi(actor, movie):
            actorAdd(request, actor)
            return True
        else:
            return False

def actorStart(request, actor):
    try:
        act = Actor.objects.get(name=actor)
        act.refAct()
        act.save()
        return True
    except:
        if validateActor(actor):
            actorAdd(request, actor)
            return True
        else:
            return False

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

                turner(request, sb.id, False, Actor.objects.get(name = name).id, True, False, 1)

                return redirect("movieTurn", game_id = sb.id, entity = name, score = score)
            
            else:
                return redirect("gameOver", game_id = sb.id, entity = name, score = 0)

        #args = {'form': form, 'name': name, 'actor': act, 'score': score}
    
    else:
        form = ActorForm()
        return render(request, template_name, {'form': form})

