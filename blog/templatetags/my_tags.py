from django import template
from blog import models
from django.db.models import Count

register = template.Library()


@register.inclusion_tag("left_menu.html")
def get_left_menu(username):
    user = models.UserInfo.objects.filter(username=username).first()
    blog = user.blog
    # 查询文章分类及对应的文章数
    category_list = models.Category.objects.filter(blog=blog).annotate(c=Count("article")).values("title", "c")
    # blog_list = models.Category.objects.filter(blog=blog)
    # print(category_list,blog_list,blog)
    # 查文章标签及对应的文章数
    tag_list = models.Tag.objects.filter(blog=blog).annotate(c=Count("article")).values("title", "c")



    return {
        "site":blog.site,
        "username": username,
        "category_list" :category_list,
        "tag_list": tag_list,
    }
