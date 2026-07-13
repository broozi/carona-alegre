"""Endpoints comuns de perfil."""
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from controllers.exceptions import BusinessError
from controllers.forms import PasswordChangeForm, ProfileForm
from controllers.profile_controller import change_password, profile_vehicles, update_profile

profile_bp = Blueprint("profile", __name__, url_prefix="/perfil")


@profile_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    form = ProfileForm(obj=current_user)
    if not form.is_submitted():
        form.nome.data = current_user.nome
        form.telefone.data = current_user.telefone
        form.email.data = current_user.email

    if form.validate_on_submit():
        try:
            update_profile(current_user, form)
            flash("Perfil atualizado com sucesso.", "success")
            return redirect(url_for("profile.index"))
        except BusinessError as exc:
            flash(str(exc), "danger")

    return render_template("profile/index.html", form=form, veiculos=profile_vehicles(current_user))


@profile_bp.route("/alterar-senha", methods=["GET", "POST"])
@login_required
def password():
    form = PasswordChangeForm()
    if form.validate_on_submit():
        try:
            change_password(current_user, form)
            flash("Senha alterada com sucesso.", "success")
            return redirect(url_for("profile.index"))
        except BusinessError as exc:
            flash(str(exc), "danger")
    return render_template("profile/password.html", form=form)
