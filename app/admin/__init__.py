# -*- coding: utf-8 -*-
"""
admin包用于博客的系统管理，如UI配置、首页推广链接、数据统计等
TODO:
1.UI配置
2.推广链接
3. 数据统计，如阅读统计、收藏统计等
"""
from flask import Blueprint

bp = Blueprint('admin',__name__)

from app.admin import routes