# -*- coding: utf-8 -*-
from flask import render_template, flash, redirect, url_for, request, current_app
from flask_login import login_required,current_user

from app.extensions import db
from app.models import Link
from app.admin import bp
from app.admin.forms import LinkForm, EditLinkForm


@bp.route('/link/new', methods=['GET', 'POST'])
@login_required
def new_link():
    form = LinkForm()
    if form.validate_on_submit():
        name = form.name.data
        url = form.url.data
        user_id = current_user.id
        link = Link(name=name, url=url, user_id=user_id)
        db.session.add(link)
        db.session.commit()
        flash('Link created.', 'success')
        return redirect(url_for('admin.manage_link'))
    return render_template('admin/new_link.html', form=form)


@bp.route('/link/manage')
@login_required
def manage_link():
    page = request.args.get('page', 1, type=int)
    pagination = Link.query.filter_by(user_id=current_user.id).order_by(Link.id).paginate(page, current_app.config['POSTS_PER_PAGE'])
    links = pagination.items
    return render_template('admin/manage_link.html',links=links, pagination=pagination, page=page)


@bp.route('/link/<int:link_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_link(link_id):
    form = EditLinkForm()
    link = Link.query.filter_by(id=link_id,author=current_user).first_or_404()
    if form.validate_on_submit():
        link.name = form.name.data
        link.url = form.url.data
        db.session.commit()
        flash('Link updated.', 'success')
        return redirect(url_for('admin.manage_link'))
    form.former_name.data = link.name
    form.former_url.data = link.url
    return render_template('admin/edit_link.html', form=form)


@bp.route('/link/<int:link_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_link(link_id):
    link = Link.query.filter_by(id=link_id,author=current_user).first_or_404()
    db.session.delete(link)
    db.session.commit()
    flash('Link deleted.', 'success')
    return redirect(url_for('admin.manage_link'))