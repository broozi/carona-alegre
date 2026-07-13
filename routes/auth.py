"""Endpoints de autenticação."""
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, logout_user

from controllers.auth_controller import authenticate, register_user
from controllers.exceptions import BusinessError
from controllers.forms import EmptyForm, LoginForm, RegisterForm

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = authenticate(form.email.data, form.senha.data, form.lembrar.data == "1")
            flash(f"Bem-vindo(a), {user.primeiro_nome}!", "success")
            return redirect(url_for("driver.home" if user.is_motorista else "passenger.home"))
        except BusinessError as exc:
            flash(str(exc), "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/cadastro", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegisterForm()
    if form.validate_on_submit():
        try:
            register_user(form)
            flash("Cadastro realizado com sucesso. Entre com seu email e senha.", "success")
            return redirect(url_for("auth.login"))
        except BusinessError as exc:
            flash(str(exc), "danger")
    return render_template("auth/register.html", form=form)


@auth_bp.post("/sair")
def logout():
    form = EmptyForm()
    if form.validate_on_submit():
        logout_user()
        flash("Sessão encerrada com segurança.", "info")
    return redirect(url_for("auth.login"))
