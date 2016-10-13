#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import copy
import datetime
import json

from django.shortcuts import render, HttpResponse
from django.db.models import F

from web import models
from web.forms.home import IndexForm

from backend.utils.pager import Pagination
from backend.utils.response import BaseResponse,StatusCodeEnum
from backend import commons

def index(request):
    # print(request.session['is_login'])
    # print(request.session['user_info'])

    if request.method == 'GET':
        page = request.GET.get('page', 1)
        all_count = models.News.objects.all().count()

        obj = Pagination(page, all_count)

        result = models.News.objects.all().values_list('nid',
                                                      'title',
                                                      'url',
                                                      'content',
                                                      'ctime',
                                                      'user_info__username',
                                                      'news_type__caption',
                                                      'favor_count',
                                                      'comment_count',
                                                      'favor__nid')[obj.start: obj.end]
        # print(result.query)
        print(result[1])
        str_page = obj.string_pager('/index/')

        return render(request, 'index.html', {'str_page': str_page, 'news_list': result})
    else:
        rep = BaseResponse()

        form = IndexForm(request.POST)
        if form.is_valid():
            # title,content,href,news_type,user_info_id
            _value_dict = form.clean()
            input_dict = copy.deepcopy(_value_dict)
            input_dict['ctime'] = datetime.datetime.now()
            input_dict['user_info_id'] = request.session['user_info']['nid']
            models.News.objects.create(**input_dict)
            rep.status = True
        else:

            error_msg = form.errors.as_json()
            rep.message = json.loads(error_msg)

        return HttpResponse(json.dumps(rep.__dict__))


def favor(request):
    rep = BaseResponse()

    news_id = request.POST.get('news_id', None)
    if not news_id:
        rep.summary = "新闻ID不能为空."
    else:
        user_info_id = request.session['user_info']['nid']

        has_favor = models.Favor.objects.filter(user_info_id=user_info_id, news_id=news_id).count()
        if has_favor:
            models.Favor.objects.filter(user_info_id=user_info_id, news_id=news_id).delete()
            models.News.objects.filter(nid=news_id).update(favor_count=F('favor_count')-1)

            rep.code = StatusCodeEnum.FavorMinus
        else:
            models.Favor.objects.create(user_info_id=user_info_id, news_id=news_id, ctime=datetime.datetime.now())
            models.News.objects.filter(nid=news_id).update(favor_count=F('favor_count')+1)

            rep.code = StatusCodeEnum.FavorPlus

        rep.status = True

    return HttpResponse(json.dumps(rep.__dict__))


def upload_image(request):

    rep = BaseResponse()
    try:
        obj = request.FILES.get('img')
        file_path = os.path.join('statics', 'upload', commons.generate_md5(obj.name))

        f = open(file_path, 'wb')
        for chunk in obj.chunks():
            f.write(chunk)
        f.close()

        rep.status = True
        rep.data = file_path
    except Exception as ex:
        rep.summary = str(ex)
    return HttpResponse(json.dumps(rep.__dict__))


def comment(request):
    if request.method == 'GET':
        nid = request.GET.get('nid',None)
        content_item = models.Comment.objects.filter(nid=nid).all()
        print(content_item)
        return HttpResponse(content_item)