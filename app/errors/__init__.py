# -*- coding: utf-8 -*-
"""
errors包用于处理错误
"""
from flask import Blueprint

bp = Blueprint('errors',__name__)

from app.errors import handlers