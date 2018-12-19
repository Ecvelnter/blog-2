# -*- coding: utf-8 -*-
import os
import time
from datetime import datetime
from flask import render_template, flash, redirect, url_for, request,current_app,send_from_directory
from flask_login import current_user, login_required
from flask_ckeditor import upload_success,upload_fail

from app import db
from app.models import User,Microblog,Blog,Category
from app.utils import redirect_back
from app.main import bp
from app.main.forms import EditProfileForm,MicroblogForm,BlogForm,CategoryForm


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
    categories = Category.query.filter_by(author=current_user).order_by(Category.id)
    blogs = Blog.query.filter_by(author=current_user,is_released=True).order_by(Blog.timestamp.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'],False)
    next_url = url_for('main.index',page=blogs.next_num) \
        if blogs.has_next else None
    prev_url = url_for('main.index',page=blogs.prev_num) \
        if blogs.has_prev else None
    return render_template('index.html',categories=categories, blogs=blogs.items,next_url=next_url,prev_url=prev_url)
    

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
    microblogs = current_user.followed_microblogs().paginate(
        page,current_app.config['POSTS_PER_PAGE'],False)
    next_url = url_for('main.new_microblog',page=microblogs.next_num) \
        if microblogs.has_next else None
    prev_url = url_for('main.new_microblog',page=microblogs.prev_num) \
        if microblogs.has_prev else None
    return render_template('microblog/new_microblog.html',title='Microblog',form=form,microblogs=microblogs.items,next_url=next_url,prev_url=prev_url)


@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page',1,type=int)
    microblogs = Microblog.query.order_by(Microblog.timestamp.desc()).paginate(
        page,current_app.config['POSTS_PER_PAGE'],False)
    next_url = url_for('main.explore',page=microblogs.next_num) \
        if microblogs.has_next else None
    prev_url = url_for('main.explore',page=microblogs.prev_num) \
        if microblogs.has_prev else None
    return render_template('microblog/explore.html',title='Explore',microblogs=microblogs.items,next_url=next_url,prev_url=prev_url)
    

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
        return render_template('admin/new_blog.html',form=form)
    else:
        flash('Your should create your categories first.')
        return redirect(url_for('main.new_category'))
    

@bp.route('/blog/<int:blog_id>', methods=['GET', 'POST'])
@login_required
def show_blog(blog_id):
    blog = Blog.query.filter_by(id=blog_id,is_released=True).first_or_404()
    is_favourited = current_user.is_favourited_blog(blog)
    return render_template('blog/blog.html', blog=blog,is_favourited=is_favourited)
    

@bp.route('/blog/manage')
@login_required
def manage_blog():
    page = request.args.get('page', 1, type=int)
    blogs = Blog.query.filter_by(author=current_user).order_by(Blog.timestamp.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'],False)
    next_url = url_for('main.index',page=blogs.next_num) \
        if blogs.has_next else None
    prev_url = url_for('main.index',page=blogs.prev_num) \
        if blogs.has_prev else None
    return render_template('admin/manage_blog.html', page=page, blogs=blogs.items,next_url=next_url,prev_url=prev_url)
    

@bp.route('/blog/<int:blog_id>/release', methods=['POST'])
@login_required
def release_blog(blog_id):
    blog = Blog.query.filter_by(id=blog_id,author=current_user).first_or_404()

    if blog.is_released:
        blog.is_released = False
        flash('Blog drafted.', 'success')
    else:
        blog.is_released = True
        flash('Blog released.', 'success')
    db.session.commit()
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
    return render_template('admin/edit_blog.html', form=form)
    

@bp.route('/blog/<int:blog_id>/delete', methods=['POST'])
@login_required
def delete_blog(blog_id):
    blog = Blog.query.filter_by(id=blog_id,author=current_user).first_or_404()
    db.session.delete(blog)
    db.session.commit()
    flash('Blog deleted.', 'success')
    return redirect_back()
    

@bp.route('/files/<filename>')
def uploaded_files(filename):
    path = current_app.config['UPLOADED_PATH']
    return send_from_directory(path, filename)


@bp.route('/upload', methods=['POST'])
def upload():
    f = request.files.get('upload')
    extension = f.filename.split('.')[1].lower()
    if extension not in ['jpg', 'gif', 'png', 'jpeg']:
        return upload_fail(message='Image only!')
    f.save(os.path.join(current_app.config['UPLOADED_PATH'], time.strftime('%Y%m%d%H%M%S',time.localtime()) + '_' + f.filename))
    url = url_for('main.uploaded_files', filename=time.strftime('%Y%m%d%H%M%S',time.localtime()) + '_' + f.filename)
    return upload_success(url=url)


@bp.route('/category/<int:category_id>')
def show_category(category_id):
    category = Category.query.get_or_404(category_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['POSTS_PER_PAGE']
    pagination = Blog.query.with_parent(category).order_by(Blog.timestamp.desc()).paginate(page, per_page)
    blogs = pagination.items
    return render_template('blog/category.html', category=category, pagination=pagination, blogs=blogs)


@bp.route('/category/new', methods=['GET', 'POST'])
@login_required
def new_category():
    form = CategoryForm()

    if form.validate_on_submit():
        name = form.name.data
        author = current_user
        category = Category(name=name,author=author)
        db.session.add(category)
        if current_user.has_categories is not True:
            current_user.has_categories = True
        db.session.commit()
        flash('Category created.', 'success')
        return redirect(url_for('main.manage_category'))
    return render_template('admin/new_category.html', form=form)
    

@bp.route('/category/manage')
@login_required
def manage_category():
    page = request.args.get('page',1,type=int)
    categories = Category.query.filter_by(author=current_user).order_by(Category.id).paginate(page, current_app.config['POSTS_PER_PAGE'],False)
    next_url = url_for('main.index',page=categories.next_num) \
        if categories.has_next else None
    prev_url = url_for('main.index',page=categories.prev_num) \
        if categories.has_prev else None
    return render_template('admin/manage_category.html',categories=categories.items, page=page,next_url=next_url,prev_url=prev_url)
    

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
    return render_template('admin/edit_category.html', form=form)


@bp.route('/category/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    category = Category.query.filter_by(id=category_id,author=current_user).first_or_404()
    category.delete()
    if Category.query.filter_by(author=current_user).first() is None:
        current_user.has_categories = False
        db.session.commit()
        flash('Category deleted,and you have no category now.')
    else: 
        flash('Category deleted.', 'success')
    return redirect(url_for('main.manage_category'))
    

