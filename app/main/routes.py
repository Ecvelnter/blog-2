# -*- coding: utf-8 -*-
import os
import time
from datetime import datetime
from flask import render_template, flash, redirect, url_for, request,current_app,send_from_directory
from flask_login import current_user, login_required
from flask_ckeditor import upload_success, upload_fail

from app.extensions import db
from app.models import Microblog,Blog,Category
from app.utils import redirect_back,allowed_file
from app.main import bp
from app.main.forms import MicroblogForm,BlogForm,CategoryForm


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@bp.route('/')
@bp.route('/index')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    pagination = current_user.get_releasedblogs().paginate(page, current_app.config['POSTS_PER_PAGE'])
    blogs = pagination.items
    categories = current_user.get_categories()
    links = current_user.get_links()
    return render_template('index.html', blogs=blogs,categories=categories, links=links, pagination=pagination)
    

@bp.route('/microblog/new',methods=['GET','POST'])
@login_required
def new_microblog():
    form = MicroblogForm()

    if form.validate_on_submit():
        microblog = Microblog(body=form.microblog.data,author=current_user)
        db.session.add(microblog)
        db.session.commit()
        flash('Your microblog is now live!')
        return redirect(url_for('main.new_microblog'))

    page = request.args.get('page',1,type=int)
    pagination = current_user.followed_microblogs().paginate(
        page,current_app.config['POSTS_PER_PAGE'])
    microblogs = pagination.items
    return render_template('microblog/new_microblog.html',form=form, microblogs=microblogs, pagination=pagination)


@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page',1,type=int)
    pagination = Microblog.query.order_by(Microblog.timestamp.desc()).paginate(
        page,current_app.config['POSTS_PER_PAGE'])
    microblogs = pagination.items
    return render_template('microblog/explore.html', microblogs=microblogs, pagination=pagination)
    

@bp.route('/blog/new',methods=['GET','POST'])
@login_required
def new_blog():
    if current_user.has_categories:
        form = BlogForm()
        if form.validate_on_submit():
            title = form.title.data
            body = form.body.data
            category = Category.query.get(form.category.data)
            author = current_user
            blog = Blog(title=title,body=body,category=category,author=author)
            db.session.add(blog)
            db.session.commit()
            flash('Blog created!')
            return redirect(url_for('main.manage_blog'))
        return render_template('blog/new_blog.html',form=form)
    else:
        flash('Your should create your categories first.')
        return redirect(url_for('main.new_category'))
    

@bp.route('/blog/<int:blog_id>', methods=['GET', 'POST'])
@login_required
def show_blog(blog_id):
    blog = Blog.query.filter_by(id=blog_id,is_released=True).first_or_404()
    is_favourited = current_user.is_favourited_blog(blog)
    is_author = blog.is_author(current_user)
    categories = blog.get_author_categories()
    links = blog.get_author_links()
    return render_template('blog/blog.html', blog=blog, is_favourited=is_favourited, is_author=is_author, categories=categories, links=links)
    

@bp.route('/blog/manage')
@login_required
def manage_blog():
    page = request.args.get('page', 1, type=int)
    pagination = current_user.get_allblogs().paginate(page, current_app.config['POSTS_PER_PAGE'])
    blogs = pagination.items
    return render_template('blog/manage_blog.html', blogs=blogs, pagination=pagination, page=page)
    

@bp.route('/blog/<int:blog_id>/release', methods=['GET', 'POST'])
@login_required
def release_blog(blog_id):
    blog = Blog.query.filter_by(id=blog_id,author=current_user).first_or_404()

    if blog.is_released:
        blog.is_released = False
        db.session.commit()
        flash('Blog drafted.', 'success')
    else:
        blog.is_released = True
        db.session.commit()
        flash('Blog released.', 'success')
    return redirect_back()


@bp.route('/blog/<int:blog_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_blog(blog_id):
    blog = Blog.query.filter_by(id=blog_id,author=current_user).first_or_404()
    form = BlogForm()

    if form.validate_on_submit():
        blog.title = form.title.data
        blog.body = form.body.data
        blog.category = Category.query.get(form.category.data)
        db.session.commit()
        flash('Blog updated.', 'success')
        return redirect(url_for('main.manage_blog', blog_id=blog.id))
    form.title.data = blog.title
    form.body.data = blog.body
    form.category.data = blog.category_id
    return render_template('blog/edit_blog.html', form=form)
    

@bp.route('/blog/<int:blog_id>/delete', methods=['GET','POST'])
@login_required
def delete_blog(blog_id):
    blog = Blog.query.filter_by(id=blog_id,author=current_user).first_or_404()
    db.session.delete(blog)
    db.session.commit()
    flash('Blog deleted.', 'success')
    return redirect_back()
    

@bp.route('/uploads/<path:filename>')
def uploaded_files(filename):
    path = current_app.config['UPLOADED_PATH']
    return send_from_directory(path, filename)


@bp.route('/upload', methods=['POST'])
def upload():
    f = request.files.get('upload')
    if not allowed_file(f.filename):
        return upload_fail('Image only!')

    f.filename = time.strftime('%Y%m%d%H%M%S',time.localtime()) + '_' + f.filename
    f.save(os.path.join(current_app.config['UPLOADED_PATH'],f.filename))
    url = url_for('main.uploaded_files', filename=f.filename)
    return upload_success(url,f.filename)


@bp.route('/category/<int:category_id>')
@login_required
def show_category(category_id):
    category = Category.query.get_or_404(category_id)
    page = request.args.get('page', 1, type=int)
    pagination = category.get_releasedblogs().paginate(page, current_app.config['POSTS_PER_PAGE'])
    blogs = pagination.items
    categories = category.get_author_categories()
    links = category.get_author_links()
    return render_template('blog/category.html', category=category, blogs=blogs, pagination=pagination, categories=categories, links=links)


@bp.route('/category/new', methods=['GET', 'POST'])
@login_required
def new_category():
    form = CategoryForm()

    if form.validate_on_submit():
        name = form.name.data
        author = current_user.id
        category = Category(name=name,user_id=author)
        db.session.add(category)
        if current_user.has_categories is not True:
            current_user.has_categories = True
        db.session.commit()
        flash('Category created.', 'success')
        return redirect(url_for('main.manage_category'))
    return render_template('blog/new_category.html', form=form)
    

@bp.route('/category/manage')
@login_required
def manage_category():
    page = request.args.get('page',1,type=int)
    pagination = Category.query.filter_by(author=current_user).order_by(Category.id).paginate(page, current_app.config['POSTS_PER_PAGE'])
    categories = pagination.items
    return render_template('blog/manage_category.html',categories=categories, pagination=pagination)
    

@bp.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    category = Category.query.filter_by(id=category_id,author=current_user).first_or_404()
    form = CategoryForm()

    if form.validate_on_submit():
        category.name = form.name.data
        db.session.commit()
        flash('Category updated.', 'success')
        return redirect(url_for('main.manage_category'))
    form.name.data = category.name
    return render_template('blog/edit_category.html', form=form)


@bp.route('/category/<int:category_id>/delete', methods=['GET','POST'])
@login_required
def delete_category(category_id):
    category = Category.query.filter_by(id=category_id,author=current_user).first_or_404()

    if category.is_blogsbelonged():
        flash('Can not delete the category with blogs undered')
    else:
        category.delete()
        if Category.query.filter_by(author=current_user).first() is None:
            current_user.has_categories = False
            db.session.commit()
            flash('Category deleted,and you have no category now.')
        else:
            flash('Category deleted.', 'success')
    return redirect_back()

