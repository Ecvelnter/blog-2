# -*- coding: utf-8 -*-
from flask import render_template
from flask_wtf.csrf import CSRFError

from app.extensions import db
from app.errors import bp


@bp.app_errorhandler(400)
def bad_request(error):
    return render_template('errors/400.html'),400


@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'),404


@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'),500


@bp.app_errorhandler(CSRFError)
def handle_csrf_error(error):
        return render_template('errors/400.html', description=error.description), 400