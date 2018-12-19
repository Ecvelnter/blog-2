# -*- coding: utf-8 -*-
from flask_login import current_user
from flask_wtf import FlaskForm
from flask_ckeditor import CKEditorField
from wtforms import StringField,SubmitField,TextAreaField, SelectField
from wtforms.validators import DataRequired,ValidationError, Length

from app.models import User,Category


class MicroblogForm(FlaskForm):
    microblog = TextAreaField('Say something',validators=[DataRequired()])
    submit = SubmitField('Submit')
    
    

class BlogForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(1, 60)])
    category = SelectField('Category', coerce=int, default=1)
    body = CKEditorField('Blog', validators=[DataRequired()])
    submit = SubmitField()

    def __init__(self, *args, **kwargs):
        super(BlogForm, self).__init__(*args, **kwargs)
        self.category.choices = [(category.id, category.name)
                                 for category in Category.query.filter_by(author=current_user).order_by(Category.name).all()]
    

class CategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(1, 30)])
    submit = SubmitField()

    def validate_name(self, field):
        if Category.query.filter_by(name=field.data).first():
            raise ValidationError('Name already in use.')