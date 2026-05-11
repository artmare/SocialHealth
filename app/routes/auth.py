from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, make_response
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies,
    jwt_required,
    get_jwt_identity,
)
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo
import sqlalchemy as sa

from app.extensions import db, csrf
from app.models import User, UserSettings

auth_bp = Blueprint("auth", __name__, template_folder="../templates")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    submit = SubmitField("Войти")


class RegisterForm(FlaskForm):
    username = StringField(
        "Имя пользователя", validators=[DataRequired(), Length(min=2, max=100)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        "Пароль", validators=[DataRequired(), Length(min=8)]
    )
    confirm_password = PasswordField(
        "Подтвердите пароль",
        validators=[DataRequired(), EqualTo("password")],
    )
    submit = SubmitField("Зарегистрироваться")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_email = (
            db.session.execute(
                sa.select(User).where(User.email == form.email.data)
            )
            .scalar_one_or_none()
        )
        if existing_email:
            flash("Пользователь с таким email уже существует", "error")
            return render_template("auth/register.html", form=form)

        existing_username = (
            db.session.execute(
                sa.select(User).where(User.username == form.username.data)
            )
            .scalar_one_or_none()
        )
        if existing_username:
            flash("Имя пользователя уже занято", "error")
            return render_template("auth/register.html", form=form)

        user = User(email=form.email.data, username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        settings = UserSettings(user_id=user.id)
        db.session.add(settings)
        db.session.commit()

        flash("Регистрация прошла успешно! Теперь вы можете войти.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = (
            db.session.execute(
                sa.select(User).where(User.email == form.email.data)
            )
            .scalar_one_or_none()
        )
        if user and user.check_password(form.password.data):
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))
            resp = make_response(redirect(url_for("dashboard.index")))
            set_access_cookies(resp, access_token)
            set_refresh_cookies(resp, refresh_token)
            flash("Вход выполнен успешно!", "success")
            return resp
        else:
            flash("Неверный email или пароль", "error")

    return render_template("auth/login.html", form=form)


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
@csrf.exempt
def refresh():
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    resp = jsonify(access_token=access_token)
    set_access_cookies(resp, access_token)
    return resp, 200


@auth_bp.post("/logout")
@csrf.exempt
def logout():
    resp = make_response(redirect(url_for("auth.login")))
    unset_jwt_cookies(resp)
    flash("Вы вышли из аккаунта", "info")
    return resp
