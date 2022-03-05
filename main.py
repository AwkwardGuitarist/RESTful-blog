from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditor, CKEditorField
from datetime import datetime as dt
import bleach
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
DNE = os.environ["DNE"]
app.config['SECRET_KEY'] = os.environ["SECRET_KEY"]
ckeditor = CKEditor(app)
Bootstrap(app)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# CONFIGURE TABLE
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)


# WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    author = StringField("Your Name", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField('Content')
    submit = SubmitField("Submit Post")


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts)


@app.route("/post/<int:index>")
def show_post(index):
    requested_post = BlogPost.query.get(index)
    if requested_post:
        return render_template("post.html", post=requested_post)
    else:
        return DNE, 404


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


# strips invalid tags/attributes
def strip_invalid_html(content):
    allowed_tags = ['a', 'abbr', 'acronym', 'address', 'b', 'br', 'div', 'dl', 'dt',
                    'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img',
                    'li', 'ol', 'p', 'pre', 'q', 's', 'small', 'strike',
                    'span', 'strong', 'sub', 'sup', 'table', 'tbody', 'td', 'tfoot', 'th',
                    'thead', 'tr', 'tt', 'u', 'ul']
    allowed_attrs = {
        'a': ['href', 'target', 'title'],
        'img': ['src', 'alt', 'width', 'height'],
    }
    cleaned = bleach.clean(content,
                           tags=allowed_tags,
                           attributes=allowed_attrs,
                           strip=True)
    return cleaned


@app.route('/edit/<int:post_id>', methods=["GET", "POST"])
def edit_post(post_id):
    form = CreatePostForm()
    if request.method == "GET" and post_id is not None:
        post = BlogPost.query.get(post_id)
        form.title.data = post.title
        form.subtitle.data = post.subtitle
        form.author.data = post.author
        form.img_url.data = post.img_url
        form.body.data = post.body
        return render_template('make-post.html', form=form)
    elif request.method == "POST" and form.validate_on_submit():
        # add the post
        post = BlogPost.query.get(post_id)
        post.title = strip_invalid_html(form.title.data)
        post.subtitle = strip_invalid_html(form.subtitle.data)
        post.author = strip_invalid_html(form.author.data)
        post.img_url = strip_invalid_html(form.img_url.data)
        post.body = strip_invalid_html(form.body.data)
        db.session.commit()
        return redirect(url_for('show_post', index=post.id))
    else:
        return DNE, 404


@app.route('/new-post', methods=["GET", "POST"])
def new_post():
    form = CreatePostForm()
    if request.method == "POST" and form.validate_on_submit():
        # add the post
        post = BlogPost(title=strip_invalid_html(form.title.data),
                        subtitle=strip_invalid_html(form.subtitle.data),
                        date=dt.today().strftime("%B %d, %Y"),
                        body=strip_invalid_html(form.body.data),
                        author=strip_invalid_html(form.author.data),
                        img_url=strip_invalid_html(form.img_url.data))
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('show_post', index=post.id))
    return render_template('make-post.html', form=form)


@app.route('/delete/<int:index>')
def delete_post(index):
    post = BlogPost.query.get(index)
    if post:
        db.session.delete(post)
        db.session.commit()
        return redirect(url_for('get_all_posts'))
    else:
        return DNE, 404


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
