from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, make_response
from flask_babel import lazy_gettext as _
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

from app.extensions import db, csrf, limiter
from app.models import User, UserSettings

auth_bp = Blueprint("auth", __name__, template_folder="../templates")


class LoginForm(FlaskForm):
    email = StringField(
        _("Email"),
        validators=[DataRequired(message=_("This field is required")), Email(message=_("Enter a valid email address"))],
    )
    password = PasswordField(
        _("Password"), validators=[DataRequired(message=_("This field is required"))]
    )
    submit = SubmitField(_("Sign in"))


class RegisterForm(FlaskForm):
    username = StringField(
        _("Username"),
        validators=[
            DataRequired(message=_("This field is required")),
            Length(min=2, max=100, message=_("Username must be between 2 and 100 characters")),
        ],
    )
    email = StringField(
        _("Email"),
        validators=[DataRequired(message=_("This field is required")), Email(message=_("Enter a valid email address"))],
    )
    password = PasswordField(
        _("Password"),
        validators=[
            DataRequired(message=_("This field is required")),
            Length(min=8, message=_("Password must be at least 8 characters")),
        ],
    )
    confirm_password = PasswordField(
        _("Confirm password"),
        validators=[
            DataRequired(message=_("This field is required")),
            EqualTo("password", message=_("Passwords do not match")),
        ],
    )
    submit = SubmitField(_("Register"))


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
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
            flash(_("A user with this email already exists"), "error")
            return render_template("auth/register.html", form=form)

        existing_username = (
            db.session.execute(
                sa.select(User).where(User.username == form.username.data)
            )
            .scalar_one_or_none()
        )
        if existing_username:
            flash(_("Username is already taken"), "error")
            return render_template("auth/register.html", form=form)

        user = User(email=form.email.data, username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        settings = UserSettings(user_id=user.id)
        db.session.add(settings)
        db.session.commit()

        flash(_("Registration successful! You can sign in now."), "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
@limiter.limit("30 per hour", methods=["POST"])
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
            flash(_("Signed in successfully!"), "success")
            return resp
        else:
            flash(_("Wrong email or password"), "error")

    return render_template("auth/login.html", form=form)


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
@csrf.exempt
@limiter.limit("30 per minute")
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
    flash(_("You have signed out"), "info")
    return resp
