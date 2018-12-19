# -*- coding: utf-8 -*-
"""
user包用于用户类相关操作的路由
"""
from flask import Blueprint

bp = Blueprint('user',__name__)

from app.user import routes