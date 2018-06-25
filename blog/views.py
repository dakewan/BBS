from django.shortcuts import render,HttpResponse,redirect
from django.contrib import auth
from django.http import JsonResponse
from geetest import GeetestLib
from . import models
from . import forms
import json
from django.db.models import F
# Create your views here.


def login(request):
    if request.method == 'POST':
        ret = {'status': 0, "msg":''}
        username = request.POST.get('username')
        password = request.POST.get('password')


        # 获取极验 滑动验证码相关的参数
        gt = GeetestLib(pc_geetest_id, pc_geetest_key)
        challenge = request.POST.get(gt.FN_CHALLENGE, '')
        validate = request.POST.get(gt.FN_VALIDATE, '')
        seccode = request.POST.get(gt.FN_SECCODE, '')
        status = request.session[gt.GT_STATUS_SESSION_KEY]
        user_id = request.session["user_id"]

        if status:
            result = gt.success_validate(challenge, validate, seccode, user_id)
        else:
            result = gt.failback_validate(challenge, validate, seccode)
        if result:
            # 利用auth模块做用户名和密码的校验
            user = auth.authenticate(username=username, password=password)
            if user:
                # 用户名密码正确
                # 给用户做登录
                auth.login(request, user)  # 将登录用户赋值给 request.user
                ret["msg"] = "/index/"
            else:
                # 用户名密码错误
                ret["status"] = 1
                ret["msg"] = "用户名或密码错误！"
            return JsonResponse(ret)
    else:
        return render(request,'login.html',)



def index(request):
    article_list = models.Article.objects.all()
    return render(request,'index.html',locals())


def logout(request):
    auth.logout(request)
    return redirect("/login/")


# 请在官网申请ID使用，示例ID不可使用
pc_geetest_id = "b46d1900d0a894591916ea94ea91bd2c"
pc_geetest_key = "36fc3fe98530eea08dfc6ce76e3d24c4"


# 处理极验 获取验证码的视图
def get_geetest(request):
    user_id = 'test'
    gt = GeetestLib(pc_geetest_id, pc_geetest_key)
    status = gt.pre_process(user_id)
    request.session[gt.GT_STATUS_SESSION_KEY] = status
    request.session["user_id"] = user_id
    response_str = gt.get_response_str()
    return HttpResponse(response_str)


def register(request):
    if request.method=="POST":
        print(request.POST)
        ret = {"status": 0, "msg": ""}
        form_obj = forms.RegForm(request.POST)
        if form_obj.is_valid():
            # 校验通过，去数据库创建一个新的用户
            form_obj.cleaned_data.pop("re_password")
            avatar_img = request.FILES.get("avatar")
            models.UserInfo.objects.create_user(**form_obj.cleaned_data, avatar=avatar_img)
            ret["msg"] = "/login/"
            return JsonResponse(ret)
        else:
            # print(form_obj.errors)
            ret["status"] = 1
            ret["msg"] = form_obj.errors
            return JsonResponse(ret)

    # 生成一个form对象

    form_obj = forms.RegForm()
    return render(request, 'register.html', locals())

def check_username_exist(request):
    ret = {'status': 0, 'msg': ''}
    username = request.GET.get('username')
    user = models.UserInfo.objects.filter(username=username)
    if user:
        ret['status'] = 1
        ret['msg'] = ' 用户名已注册'

    else:
        ret['msg'] = ' 可注册'
    return JsonResponse(ret)


def home(request,site,*args):
    # print(site,args)
    blog = models.Blog.objects.filter(site=site).first()

    if not blog:
        return HttpResponse("404")
    else:
        username = blog.userinfo.username
        user = blog.userinfo
        article_list = models.Article.objects.filter(user=blog.userinfo)
        return render(request,'blog.html',locals())


def tag(request,site,tag):
    blog = models.Blog.objects.filter(site=site).first()
    if not blog:
        return HttpResponse("404")
    else:
        username = blog.userinfo.username
        user = blog.userinfo
        article_list = models.Article.objects.filter(user=blog.userinfo,article2tag__tag__title=tag)
        return render(request,'blog.html',locals())


def category(request,site,category):
    blog = models.Blog.objects.filter(site=site).first()
    if not blog:
        return HttpResponse("404")
    else:
        username = blog.userinfo.username
        user = blog.userinfo
        article_list = models.Article.objects.filter(user=user,category__title=category)
        # print(article_list)
        return render(request,'blog.html',locals())


def article(request,site,article_id):
    blog = models.Blog.objects.filter(site=site).first()
    if blog:
        username = blog.userinfo.username
        user = blog.userinfo
        article = models.Article.objects.filter(nid=article_id,user=user).first()
        comment_list = models.Comment.objects.filter(article=article)
        if article:
            return render(request,'article.html',locals())
        else:
            return HttpResponse("404")
    else:
        return HttpResponse("404")


def blog_reg(request):
    if request.method == 'POST':
        print(request.POST)
        ret = {"status": 0, "msg": ""}
        form_obj = forms.BlogForm(request.POST)
        if form_obj.is_valid():
            blog = models.Blog.objects.create(**form_obj.cleaned_data)
            models.UserInfo.objects.filter(username=request.user).update(blog=blog)
            ret["msg"] = "/blog/%s" % blog.site
            return JsonResponse(ret)
        else:
            # print(form_obj.errors)
            ret["status"] = 1
            ret["msg"] = form_obj.errors
            return JsonResponse(ret)

    blog_form = forms.BlogForm()

    return render(request,"blog-reg.html",locals())


def up_down(request):
    article_id = request.POST.get('article_id')
    is_up = json.loads(request.POST.get('is_up'))
    user = request.user
    response = {"state": True}
    try:
        models.ArticleUpDown.objects.create(user=user, article_id=article_id, is_up=is_up)
        models.Article.objects.filter(nid=article_id).update(up_count=F("up_count") + 1)

    except Exception as e:
        response["state"] = False
        response["fisrt_action"] = models.ArticleUpDown.objects.filter(user=user, article_id=article_id).first().is_up

    return JsonResponse(response)


def comment(request):
    # print(request.POST)
    # {'content': ['hhhhhhhh'], 'parent_comment_id': [''], 'article_id': ['1'], 'user_id': ['1'],
    content = request.POST.get("content")
    parent_comment_id = request.POST.get("parent_comment_id")
    article_id = request.POST.get("article_id")
    user_id = request.POST.get("user_id")
    comment = models.Comment.objects.create(
        content=content,
        parent_comment_id=parent_comment_id,
        article_id=article_id,
        user_id=user_id
    )
    models.Article.objects.filter(nid=article_id).update(comment_count=F("comment_count")+1)
    # print(comment)
    return HttpResponse("评论成功")