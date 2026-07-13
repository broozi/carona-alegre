"""Endpoints do passageiro."""
from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user

from controllers.exceptions import BusinessError, NotFoundError
from controllers.forms import EmptyForm, SearchRideForm
from controllers.passenger_controller import passenger_home, request_ride, search_location_choices, search_rides
from controllers.security import role_required

passenger_bp = Blueprint("passenger", __name__, url_prefix="/passageiro")


@passenger_bp.get("/home")
@role_required("PASSAGEIRO")
def home():
    confirmed, pending = passenger_home(current_user.id_pessoa)
    return render_template("passenger/home.html", confirmadas=confirmed, pendentes=pending)


@passenger_bp.route("/caronas/pesquisar", methods=["GET", "POST"])
@role_required("PASSAGEIRO")
def search():
    form = SearchRideForm()
    choices = search_location_choices()
    form.origem.choices = choices
    form.destino.choices = choices
    results = []
    searched = False

    if form.is_submitted() and form.validate():
        results = search_rides(current_user.id_pessoa, form)
        searched = True
    elif not form.is_submitted():
        results = search_rides(current_user.id_pessoa, form)

    return render_template(
        "passenger/search.html",
        form=form,
        caronas=results,
        searched=searched,
        action_form=EmptyForm(),
    )


@passenger_bp.post("/caronas/<int:ride_id>/solicitar")
@role_required("PASSAGEIRO")
def request(ride_id: int):
    form = EmptyForm()
    if not form.validate_on_submit():
        abort(400)
    try:
        request_ride(current_user.id_pessoa, ride_id)
        flash("Solicitação enviada ao motorista. O status inicial é Pendente.", "success")
        return redirect(url_for("passenger.home"))
    except NotFoundError:
        abort(404)
    except BusinessError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("passenger.search"))
