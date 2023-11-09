from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.mail import message
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from main.models import User, Voting, VoteVariant, VoteFact, VoteFactVariant


def get_menu_context():
    return [
        {'url_name': 'index', 'name': 'Главная'},
        {'url_name': 'about', 'name': 'О сайте'},
    ]


def index_page(request):
    context = {
        'pagename': 'Главная',
        'menu': get_menu_context()
    }
    if request.user.is_authenticated:
        votings = Voting.objects.filter(author=request.user).order_by('-id')
        context['votings'] = votings

    return render(request, 'pages/index.html', context)


def about_page(request):
    context = {
        'pagename': 'О сайте',
        'menu': get_menu_context()
    }
    return render(request, 'pages/about.html', context)


@login_required
def profile_page(request, user_id):
    context = {'menu': get_menu_context()}
    if request.method == 'POST':
        record = User.objects.get(id=user_id)
        record.username = request.POST.get('name') if request.POST.get('name') else request.user.username
        record.email = request.POST.get('email') if request.POST.get('email') else request.user.email
        if request.POST.get('password'):
            record.set_password(request.POST.get('password'))
        record.save()
    context['user'] = get_object_or_404(User, id=user_id)
    votefacts = reversed(list(VoteFact.objects.filter(user=context['user'])))
    context['votefacts'] = [{'fact': fact, 'voting': fact.get_voting()} for fact in votefacts]
    return render(request, 'pages/profile.html', context)


@login_required
def voting_results_page(request, voting_id):
    voting = get_object_or_404(Voting, id=voting_id, published=True)
    context = {
        'menu': get_menu_context(),
        'voting': voting,
        'variants': voting.get_all_variants(),
        'facts': voting.get_results()
    }

    for variant in context['facts']:
        context['facts'][variant]['percentage'] = f"{context['facts'][variant]['percentage']:.0%}"

    return render(request, 'pages/voting/results.html', context)


@login_required
def voting_public_page(request, voting_id):
    context = {
        'menu': get_menu_context()
    }
    voting = get_object_or_404(Voting, id=voting_id, published=True)
    variants = voting.get_all_variants()
    context['voting'] = voting
    context['variants'] = variants
    if request.method == 'POST':
        user = request.user
        variant_ids = request.POST.getlist('variant_id', [])
        try:
            variant_ids = [int(variant_id) for variant_id in variant_ids]
            voting.make_votefact(variant_ids, user)
            return redirect(f'/voting/{voting_id}/results/')
        except ValueError:
            context['error'] = 'В id не может быть строки'
        except PermissionError as ex:
            context['error'] = str(ex)

    return render(request, 'pages/voting/public.html', context)


@login_required
def voting_details_page(request, voting_id):
    context = {
        'menu': get_menu_context()
    }
    voting = get_object_or_404(Voting, id=voting_id)
    context['voting'] = voting

    if request.method == 'POST':
        if len(request.POST.keys()) == 1:
            voting.published = True
            voting.save()
        if 'variant_id' in request.POST.keys():
            VoteVariant.objects.filter(id=request.POST.get('variant_id', -1)).delete()
        if request.POST.get('new_variant', -1) != -1:
            VoteVariant(voting=voting, description=request.POST.get('new_variant')).save()
        if request.POST.get('voting_name', -1) != -1 and request.POST.get('voting_description', -1) != -1:
            if request.POST.get('voting_name'): voting.name = request.POST.get('voting_name')
            if request.POST.get('voting_description'): voting.description = request.POST.get('voting_description')
            voting.save()

    variants = VoteVariant.objects.filter(voting=voting)
    context['variants'] = variants
    context['norm_count_of_variants'] = variants.count() < 10
    return render(request, 'pages/voting/details.html', context)


@login_required
def votevariant_delete_page(request, voting_id, variant_id):
    if request.method == 'get':
        raise PermissionError('Only POST allowed')
    voting = get_object_or_404(Voting, id=voting_id)
    try:
        voting.delete_variant(variant_id, request.user)
    except PermissionError as ex:
        messages.error(request, message=str(ex))
    return redirect(reverse('voting_details', kwargs={'voting_id': voting_id}))


@login_required
def create_voting_page(request):
    context = {
        'pagename': 'Создание голосования',
        'menu': get_menu_context()
    }
    if request.method == 'POST':
        try:
            voting = Voting.create(
                author=request.user,
                name=request.POST.get('voting_name', 'НАЗВАНИЕ'),
                description=request.POST.get('voting_description', 'ОПИСАНИЕ'),
                voting_type=request.POST.get('voting_type', '3'),
                variants=[
                    request.POST.get('first_variant', 'ПЕРВЫЙ ВАРИАНТ'),
                    request.POST.get('second_variant', 'ВТОРОЙ ВАРИАНТ')
                ]
            )
            return redirect(reverse('voting_details', kwargs={'voting_id': voting.id}))
        except ValidationError as ex:
            context['error'] = ex.message
    return render(request, 'pages/voting/create.html', context)


def all_votings(request):
    context = {
        'pagename': 'Создание голосования',
        'menu': get_menu_context(),
        'votings': Voting.objects.filter(published=True).order_by('-id')
    }
    return render(request, 'pages/all_votings.html', context)
