# -*- coding: utf-8 -*-
"""
auth包用于用户登录验证等

"""
from flask import Blueprint

bp = Blueprint('auth',__name__)

from app.auth import routes