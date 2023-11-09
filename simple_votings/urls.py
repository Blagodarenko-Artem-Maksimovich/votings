"""simple_votings URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django_registration.backends.one_step.views import RegistrationView

from main import views
from main.forms import VotingRegistrationForm
from main.views import voting_public_page, voting_details_page, voting_results_page, votevariant_delete_page

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index_page, name='index'),
    path('accounts/register/', RegistrationView.as_view(form_class=VotingRegistrationForm),
         name='django_registration_register'),
    path('accounts/', include('django_registration.backends.one_step.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('voting/<int:voting_id>/public/', voting_public_page, name='voting_public'),
    path('voting/<int:voting_id>/', voting_details_page, name='voting_details'),
    path('voting/<int:voting_id>/variants/<int:variant_id>/delete/', votevariant_delete_page, name='votevariant_delete'),
    path('voting/<int:voting_id>/results/', voting_results_page, name='voting_results'),
    path('create_voting/', views.create_voting_page, name='create_voting'),
    path('profile/<str:user_id>/', views.profile_page, name='profile'),
    path('all_votings/', views.all_votings, name='all_votings'),
    path('about/', views.about_page, name='about')
]
