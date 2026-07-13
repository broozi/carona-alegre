"""Endpoints do motorista. As regras de negócio ficam nos controladores."""
from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user

from controllers.driver_controller import (
    accept_offer,
    active_vehicle_choices,
    create_ride,
    delete_vehicle,
    driver_home,
    get_vehicle,
    list_vehicles,
    location_choices,
    refuse_offer,
    ride_offers,
    save_vehicle,
)
from controllers.exceptions import BusinessError, NotFoundError
from controllers.forms import EmptyForm, RideForm, VehicleForm
from controllers.security import role_required

driver_bp = Blueprint("driver", __name__, url_prefix="/motorista")


@driver_bp.get("/home")
@role_required("MOTORISTA")
def home():
    return render_template("driver/home.html", caronas=driver_home(current_user.id_pessoa))


@driver_bp.route("/caronas/nova", methods=["GET", "POST"])
@role_required("MOTORISTA")
def create_ride_view():
    form = RideForm()
    vehicles = active_vehicle_choices(current_user.id_pessoa)
    form.veiculo.choices = vehicles

    if not vehicles:
        flash("Cadastre um veículo antes de criar uma carona.", "warning")
        return redirect(url_for("driver.vehicles"))

    if form.validate_on_submit():
        try:
            create_ride(current_user.id_pessoa, form)
            flash("Carona criada com sucesso.", "success")
            return redirect(url_for("driver.home"))
        except BusinessError as exc:
            flash(str(exc), "danger")
    return render_template("driver/ride_form.html", form=form)


@driver_bp.route("/veiculos", methods=["GET", "POST"])
@role_required("MOTORISTA")
def vehicles():
    form = VehicleForm()
    if form.validate_on_submit():
        try:
            save_vehicle(current_user.id_pessoa, form)
            flash("Veículo cadastrado com sucesso.", "success")
            return redirect(url_for("driver.vehicles"))
        except BusinessError as exc:
            flash(str(exc), "danger")
    return render_template(
        "driver/vehicles.html",
        form=form,
        veiculos=list_vehicles(current_user.id_pessoa),
        action_form=EmptyForm(),
    )


@driver_bp.route("/veiculos/<int:vehicle_id>/editar", methods=["GET", "POST"])
@role_required("MOTORISTA")
def edit_vehicle(vehicle_id: int):
    try:
        vehicle = get_vehicle(current_user.id_pessoa, vehicle_id)
    except NotFoundError:
        abort(404)

    form = VehicleForm(obj=vehicle)
    if form.validate_on_submit():
        try:
            save_vehicle(current_user.id_pessoa, form, vehicle_id)
            flash("Veículo atualizado com sucesso.", "success")
            return redirect(url_for("driver.vehicles"))
        except BusinessError as exc:
            flash(str(exc), "danger")
    return render_template("driver/vehicle_edit.html", form=form, veiculo=vehicle)


@driver_bp.post("/veiculos/<int:vehicle_id>/excluir")
@role_required("MOTORISTA")
def remove_vehicle(vehicle_id: int):
    form = EmptyForm()
    if not form.validate_on_submit():
        abort(400)
    try:
        message = delete_vehicle(current_user.id_pessoa, vehicle_id)
        flash(message, "success")
    except NotFoundError:
        abort(404)
    except BusinessError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("driver.vehicles"))


@driver_bp.get("/caronas/<int:ride_id>/ofertas")
@role_required("MOTORISTA")
def offers(ride_id: int):
    try:
        ride, pending, processed = ride_offers(current_user.id_pessoa, ride_id)
    except NotFoundError:
        abort(404)
    return render_template(
        "driver/offers.html",
        carona=ride,
        pendentes=pending,
        processadas=processed,
        action_form=EmptyForm(),
    )


@driver_bp.post("/ofertas/<int:reservation_id>/aceitar")
@role_required("MOTORISTA")
def accept(reservation_id: int):
    ride_id = None
    form = EmptyForm()
    if not form.validate_on_submit():
        abort(400)
    try:
        cancelled, ride_id = accept_offer(current_user.id_pessoa, reservation_id)
        message = "Solicitação aceita. A vaga foi reservada."
        if cancelled:
            message += f" {cancelled} solicitação(ões) pendente(s) foram canceladas porque a carona ficou lotada."
        flash(message, "success")
    except NotFoundError:
        abort(404)
    except BusinessError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("driver.offers", ride_id=ride_id)) if ride_id else redirect(url_for("driver.home"))


@driver_bp.post("/ofertas/<int:reservation_id>/recusar")
@role_required("MOTORISTA")
def refuse(reservation_id: int):
    ride_id = None
    form = EmptyForm()
    if not form.validate_on_submit():
        abort(400)
    try:
        ride_id = refuse_offer(current_user.id_pessoa, reservation_id)
        flash("Solicitação recusada.", "info")
    except NotFoundError:
        abort(404)
    except BusinessError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("driver.offers", ride_id=ride_id)) if ride_id else redirect(url_for("driver.home"))
