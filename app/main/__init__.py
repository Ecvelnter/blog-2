# -*- coding: utf-8 -*-
"""
main包用于blog、category、microblog等的新建、阅读、编辑、管理等
"""
from flask import Blueprint

bp = Blueprint('main',__name__)

from app.main import routes