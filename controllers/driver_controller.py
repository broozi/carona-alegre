"""Casos de uso exclusivos do motorista."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.exc import IntegrityError

from controllers.exceptions import BusinessError, NotFoundError
from controllers.utils import local_now, normalize_plate
from database.extensions import db
from database.repositories import LocationRepository, ReservationRepository, RideRepository, VehicleRepository
from models import Carona, Veiculo


def driver_home(driver_id: int):
    return RideRepository.list_by_driver(driver_id)


def location_choices() -> list[tuple[int, str]]:
    return [(location.id_local, location.descricao) for location in LocationRepository.all()]


def active_vehicle_choices(driver_id: int) -> list[tuple[int, str]]:
    return [
        (vehicle.id_veiculo, vehicle.descricao)
        for vehicle in VehicleRepository.list_by_driver(driver_id, include_inactive=False)
    ]


def create_ride(driver_id: int, form) -> Carona:
    vehicle = VehicleRepository.owned(form.veiculo.data, driver_id)
    if not vehicle or not vehicle.ativo:
        raise BusinessError("Selecione um veículo ativo pertencente à sua conta.")
    if form.numero_vagas.data > vehicle.capacidade:
        raise BusinessError(f"Este veículo comporta no máximo {vehicle.capacidade} passageiro(s).")

    departure = datetime.combine(form.data.data, form.horario.data)
    if departure <= local_now():
        raise BusinessError("A data e o horário da carona devem estar no futuro.")

    route = LocationRepository.get_or_create_route(form.origem.data, form.destino.data)

    ride = Carona(
        data_saida=form.data.data,
        horario_saida=form.horario.data,
        valor=None,
        id_motorista=driver_id,
        id_veiculo=vehicle.id_veiculo,
        id_trecho=route.id_trecho,
        numero_vagas=form.numero_vagas.data,
        status="DISPONIVEL",
    )
    db.session.add(ride)
    db.session.commit()
    return ride


def list_vehicles(driver_id: int):
    return VehicleRepository.list_by_driver(driver_id)


def get_vehicle(driver_id: int, vehicle_id: int) -> Veiculo:
    vehicle = VehicleRepository.owned(vehicle_id, driver_id)
    if not vehicle:
        raise NotFoundError("Veículo não encontrado.")
    return vehicle


def save_vehicle(driver_id: int, form, vehicle_id: int | None = None) -> Veiculo:
    plate = normalize_plate(form.placa.data)
    vehicle = None
    if vehicle_id is not None:
        vehicle = VehicleRepository.owned(vehicle_id, driver_id, for_update=True)
        if not vehicle:
            raise NotFoundError("Veículo não encontrado.")

    if VehicleRepository.plate_exists(plate, exclude_vehicle_id=vehicle_id):
        raise BusinessError("Já existe um veículo cadastrado com esta placa.")

    if vehicle is None:
        vehicle = Veiculo(id_motorista=driver_id)
        db.session.add(vehicle)

    vehicle.modelo = form.modelo.data.strip()
    vehicle.marca = form.marca.data.strip()
    vehicle.cor = form.cor.data.strip()
    vehicle.placa = plate
    vehicle.ano = form.ano.data
    vehicle.capacidade = form.capacidade.data
    vehicle.ativo = True

    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise BusinessError("Não foi possível salvar o veículo. Verifique os dados informados.") from exc
    return vehicle


def delete_vehicle(driver_id: int, vehicle_id: int) -> str:
    vehicle = VehicleRepository.owned(vehicle_id, driver_id, for_update=True)
    if not vehicle:
        raise NotFoundError("Veículo não encontrado.")
    if VehicleRepository.has_future_rides(vehicle.id_veiculo, local_now()):
        raise BusinessError("Este veículo possui caronas futuras e não pode ser excluído.")

    if VehicleRepository.has_any_rides(vehicle.id_veiculo):
        vehicle.ativo = False
        db.session.commit()
        return "Veículo desativado para preservar o histórico das caronas anteriores."

    db.session.delete(vehicle)
    db.session.commit()
    return "Veículo excluído com sucesso."


def ride_offers(driver_id: int, ride_id: int):
    ride = RideRepository.owned(ride_id, driver_id)
    if not ride:
        raise NotFoundError("Carona não encontrada.")
    pending = sorted(
        [item for item in ride.reservas if item.status == "PENDENTE"],
        key=lambda item: item.data_reserva,
    )
    processed = sorted(
        [item for item in ride.reservas if item.status != "PENDENTE"],
        key=lambda item: item.data_reserva,
        reverse=True,
    )
    return ride, pending, processed


def accept_offer(driver_id: int, reservation_id: int) -> tuple[int, int]:
    reservation = ReservationRepository.owned_by_driver(reservation_id, driver_id, for_update=True)
    if not reservation:
        raise NotFoundError("Solicitação não encontrada.")
    if reservation.status != "PENDENTE":
        raise BusinessError("Esta solicitação já foi processada.")

    ride = RideRepository.by_id_for_update(reservation.id_carona)
    if not ride or ride.id_motorista != driver_id:
        raise NotFoundError("Carona não encontrada.")
    if ride.data_hora_saida <= local_now() or ride.status in {"CANCELADA", "ENCERRADA"}:
        raise BusinessError("Não é possível aceitar solicitações para uma carona encerrada.")

    confirmed = sum(1 for item in ride.reservas if item.status == "CONFIRMADO")
    if confirmed >= ride.numero_vagas:
        ride.status = "LOTADA"
        db.session.commit()
        raise BusinessError("Todas as vagas desta carona já foram preenchidas.")

    reservation.status = "CONFIRMADO"
    confirmed += 1
    cancelled = 0
    if confirmed >= ride.numero_vagas:
        ride.status = "LOTADA"
        cancelled = ReservationRepository.cancel_other_pending(ride.id_carona, reservation.id_reserva)
    else:
        ride.status = "DISPONIVEL"

    db.session.commit()
    return cancelled, ride.id_carona


def refuse_offer(driver_id: int, reservation_id: int) -> int:
    reservation = ReservationRepository.owned_by_driver(reservation_id, driver_id, for_update=True)
    if not reservation:
        raise NotFoundError("Solicitação não encontrada.")
    if reservation.status != "PENDENTE":
        raise BusinessError("Esta solicitação já foi processada.")
    reservation.status = "RECUSADO"
    ride_id = reservation.id_carona
    db.session.commit()
    return ride_id
