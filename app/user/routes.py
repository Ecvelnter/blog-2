# -*- coding: utf-8 -*-
from datetime import datetime
from flask import render_template, flash, redirect, url_for, request,current_app
from flask_login import current_user, login_required

from app.extensions import db
from app.models import User,Microblog,Blog
from app.utils import redirect_back
from app.user import bp
from app.user.forms import EditProfileForm


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.microblogs.order_by(Microblog.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'])
    microblogs = pagination.items
    return render_template('user/user.html', user=user, microblogs=microblogs, pagination=pagination, page=page)


@bp.route('/user/<username>/blog')
@login_required
def user_blog(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    #pagination = Blog.query.filter_by(user_id=user.id, is_released=True).order_by(Blog.timestamp.desc()).paginate(page,current_app.config['POSTS_PER_PAGE'])
    pagination = user.get_releasedblogs().paginate(page,current_app.config['POSTS_PER_PAGE'])
    blogs = pagination.items
    categories = user.get_categories()
    links = user.get_links()
    return render_template('user/user_blog.html', user=user, blogs=blogs, pagination=pagination, categories=categories, links=links, page=page)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)

    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('user.user', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('user/edit_profile.html',  form=form)


@bp.route('/follow/<username>', methods=['GET', 'POST'])
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('user.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are following {}!'.format(username))
    #return redirect(url_for('user.user', username=username))
    return redirect_back()

@bp.route('/unfollow/<username>', methods=['GET', 'POST'])
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found'.format(username))
        return redirect(url_for('main.index'))
    if user == current_user:
        flash('You connot unfollow yourself!')
        return redirect(url_for('user.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You are not following {}.'.format(username))
    return redirect_back()


@bp.route('/user/<username>/favourite_blog',methods=['GET','POST'])
@login_required
def user_favourited_blog(username):
    if current_user.username == username:
        page = request.args.get('page',1,type=int)
        pagination = current_user.get_favourited_blogs().paginate(
            page,current_app.config['POSTS_PER_PAGE'])
        blogs = pagination.items
        return render_template('user/user_favourite_blog.html', user=user, blogs=blogs, pagination=pagination, page=page)
    else:
        return render_template('errors/404.html'),404


@bp.route('/blog/<int:blog_id>/favourite', methods=['GET', 'POST'])
@login_required
def favourite_blog(blog_id):
    blog = Blog.query.filter_by(id=blog_id).first()
    current_user.like_blog(blog)
    db.session.commit()
    flash('Blog liked.', 'success')
    return redirect_back()


@bp.route('/blog/<int:blog_id>/unfavourite', methods=['GET', 'POST'])
@login_required
def unfavourite_blog(blog_id):
    blog = Blog.query.filter_by(id=blog_id).first()
    current_user.dislike_blog(blog)
    db.session.commit()
    flash('Blog disliked.')
    return redirect_back()


@bp.route('/user/<username>/followed_list',methods=['GET','POST'])
@login_required
def show_followed_list(username):
    if username == current_user.username:
        user = current_user
        page = request.args.get('page',1,type=int)
        pagination = user.followed.paginate(
            page,current_app.config['POSTS_PER_PAGE'])
        followed = pagination.items
        return render_template('user/user_followed_list.html', user=user, followed=followed, pagination=pagination, page=page)
    else:
        return render_template('errors/404.html'),404


@bp.route('/user/<username>/follower_list',methods=['GET','POST'])
@login_required
def show_follower_list(username):
    if  username == current_user.username:
        user = current_user
        page = request.args.get('page',1,type=int)
        pagination = user.followers.paginate(
            page,current_app.config['POSTS_PER_PAGE'])
        followers = pagination.items
        return render_template('user/user_follower_list.html', user=user, followers=followers, pagination=pagination, page=page)
    else:
        return render_template('errors/404.html'),404