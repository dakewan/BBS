from django.contrib import admin
from django.urls import path,re_path
from blog import views


urlpatterns = [
    # url和下方重复，放在上面比较好
    path("up_down/", views.up_down),
    path("comment/", views.comment),
    path('<str:site>/', views.home),
    path('<str:site>/tag/<str:tag>/', views.tag),
    path('<str:site>/category/<str:category>/', views.category),

    path('<str:site>/articles/<int:article_id>/', views.article),
    ]