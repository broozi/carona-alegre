"""Casos de uso exclusivos do passageiro."""
from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from controllers.exceptions import BusinessError, NotFoundError
from controllers.utils import local_now
from database.extensions import db
from database.repositories import LocationRepository, ReservationRepository, RideRepository
from models import Reserva


def passenger_home(passenger_id: int):
    return ReservationRepository.passenger_dashboard(passenger_id)


def search_location_choices() -> list[tuple[int, str]]:
    return [(0, "Todos")] + [(item.id_local, item.descricao) for item in LocationRepository.all()]


def search_rides(passenger_id: int, form):
    return RideRepository.search_available(
        passenger_id=passenger_id,
        now=local_now(),
        origin_id=form.origem.data or None,
        destination_id=form.destino.data or None,
        ride_date=form.data.data,
    )


def request_ride(passenger_id: int, ride_id: int) -> None:
    ride = RideRepository.by_id_for_update(ride_id)
    if not ride:
        raise NotFoundError("Carona não encontrada.")
    if ride.id_motorista == passenger_id:
        raise BusinessError("Você não pode solicitar uma carona criada por você.")
    if ride.status != "DISPONIVEL" or ride.data_hora_saida <= local_now():
        raise BusinessError("Esta carona não está mais disponível.")
    if ReservationRepository.existing(ride_id, passenger_id):
        raise BusinessError("Você já solicitou esta carona.")

    confirmed = sum(1 for item in ride.reservas if item.status == "CONFIRMADO")
    if confirmed >= ride.numero_vagas:
        ride.status = "LOTADA"
        db.session.commit()
        raise BusinessError("As vagas desta carona já foram preenchidas.")

    db.session.add(
        Reserva(
            id_carona=ride_id,
            id_passageiro=passenger_id,
            status="PENDENTE",
            data_reserva=local_now(),
        )
    )
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise BusinessError("Você já solicitou esta carona.") from exc
