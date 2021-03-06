# -*- coding: utf-8 -*-
from datetime import datetime
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import UserMixin
from app.extensions import db, login
from hashlib import md5
from time import time
import jwt
from flask import current_app


followers = db.Table(
    'followers',
    db.Column('follower_id',db.Integer,db.ForeignKey('user.id')),
    db.Column('followed_id',db.Integer,db.ForeignKey('user.id'))
    )


favourite_blog = db.Table(
    'favourite_blog',
    db.Column('owner_id',db.Integer,db.ForeignKey('user.id')),
    db.Column('blog_id',db.Integer,db.ForeignKey('blog.id')),
    db.Column('timestamp',db.DateTime,index=True,default=datetime.utcnow)
    )


class User(UserMixin,db.Model):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(64),index=True,unique=True)
    email = db.Column(db.String(120),index=True,unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    has_categories = db.Column(db.Boolean,default=False)
    last_seen = db.Column(db.DateTime,default=datetime.utcnow)

    microblogs = db.relationship('Microblog',backref='author',lazy='dynamic')
    blogs = db.relationship('Blog',backref='author',lazy='dynamic')
    categories = db.relationship('Category',backref='author',lazy='dynamic')
    links = db.relationship('Link', backref='author', lazy='dynamic')

    followed = db.relationship(
        'User',secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers',lazy='dynamic'),lazy='dynamic')
        
    favourited_blogs = db.relationship('Blog',
        secondary=favourite_blog, 
        backref=db.backref('lover', lazy='dynamic'), 
        lazy='dynamic')

    def set_password(self,password):
        self.password_hash = generate_password_hash(password)

    def check_password(self,password):
        return check_password_hash(self.password_hash,password)

    def avatar(self,size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest,size)

    def follow(self,user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self,user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self,user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def followed_microblogs(self):
        followed = Microblog.query.join(
            followers,(followers.c.followed_id == Microblog.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Microblog.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Microblog.timestamp.desc())
    
    def get_reset_password_token(self,expires_in=600):
        return jwt.encode(
            {'reset_password':self.id,'exp':time() + expires_in},
            current_app.config['SECRET_KEY'],algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token,current_app.config['SECRET_KEY'],
                algorithm=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)
        
    def is_favourited_blog(self,blog):
        return self.favourited_blogs.filter(favourite_blog.c.blog_id == blog.id).count() > 0
        
    def like_blog(self,blog):
        if not self.is_favourited_blog(blog):
            self.favourited_blogs.append(blog)
    
    def dislike_blog(self,blog):
        if self.is_favourited_blog(blog):
            self.favourited_blogs.remove(blog)
        
    def get_favourited_blogs(self):
        return Blog.query.join(
            favourite_blog,(favourite_blog.c.blog_id == Blog.id)).filter(
                favourite_blog.c.owner_id == self.id).order_by(Blog.timestamp.desc())

    def get_categories(self):
        return Category.query.filter_by(user_id=self.id).order_by(Category.name.desc())

    def get_links(self):
        return Link.query.filter_by(user_id=self.id).order_by(Link.name.desc())

    def get_releasedblogs(self):
        return Blog.query.filter_by(user_id=self.id, is_released =True).order_by(Blog.timestamp.desc())

    def get_allblogs(self):
        return Blog.query.filter_by(user_id=self.id).order_by(Blog.timestamp.desc())

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Microblog(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Microblog {}>'.format(self.body)


class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60))
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True,default=datetime.utcnow)
    is_released = db.Column(db.Boolean,default=False)

    category = db.relationship('Category', back_populates='blogs')

    def is_author(self,user):
        return self.query.filter_by(user_id=user.id).count() > 0

    def get_author_categories(self):
        return Category.query.filter_by(user_id=self.user_id).order_by(Category.name.desc())

    def get_author_links(self):
        return Link.query.filter_by(user_id=self.user_id).order_by(Link.name.desc())

    def __repr__(self):
        return '<Blog {}>'.format(self.body)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'))

    blogs = db.relationship('Blog', back_populates='category')

    def get_author_categories(self):
        return Category.query.filter_by(user_id=self.user_id).order_by(Category.name.desc())

    def get_author_links(self):
        return Link.query.filter_by(user_id=self.user_id).order_by(Link.name.desc())

    def is_blogsbelonged(self):
        return Blog.query.filter_by(category_id=self.id).count() > 0

    def get_releasedblogs(self):
        return Blog.query.filter_by(category_id=self.id,is_released=True).order_by(Blog.timestamp.desc())

    def get_releasedblogs_count(self):
        return Blog.query.filter_by(category_id=self.id,is_released=True).count()

    def __repr__(self):
        return '<Category {}>'.format(self.body)

        
class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    name = db.Column(db.String(30))
    url = db.Column(db.String(255))


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


    
    
    
    
    
    
    
