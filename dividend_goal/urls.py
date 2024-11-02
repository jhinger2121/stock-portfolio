from django.urls import path
from . import views

urlpatterns = [
    path('goal/', views.set_or_edit_goal, name='set_or_edit_goal'),
]