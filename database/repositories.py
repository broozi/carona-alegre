"""Camada de acesso a dados. Nenhuma rota consulta o banco diretamente."""
from __future__ import annotations

from datetime import date, datetime
import re

from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.orm import joinedload, selectinload

from database.extensions import db
from models import Carona, ContaUsuario, Local, Motorista, Passageiro, Pessoa, Reserva, Trecho, Veiculo


class UserRepository:
    @staticmethod
    def by_email(email: str) -> ContaUsuario | None:
        return db.session.scalar(
            select(ContaUsuario)
            .where(func.lower(ContaUsuario.email) == email.lower())
            .options(joinedload(ContaUsuario.pessoa))
        )

    @staticmethod
    def cpf_exists(cpf: str) -> bool:
        return bool(db.session.scalar(select(exists().where(Pessoa.cpf == cpf))))

    @staticmethod
    def email_exists(email: str, exclude_person_id: int | None = None) -> bool:
        query = select(exists().where(func.lower(ContaUsuario.email) == email.lower()))
        if exclude_person_id is not None:
            query = select(
                exists().where(
                    and_(
                        func.lower(ContaUsuario.email) == email.lower(),
                        ContaUsuario.id_pessoa != exclude_person_id,
                    )
                )
            )
        return bool(db.session.scalar(query))


class LocationRepository:
    @staticmethod
    def all() -> list[Local]:
        return list(db.session.scalars(select(Local).order_by(Local.distrito, Local.nome_local)))

    @staticmethod
    def get_by_description(description: str) -> Local | None:
        normalized = LocationRepository._normalize_description(description)
        return db.session.scalar(
            select(Local).where(func.lower(Local.nome_local) == normalized.lower())
        )

    @staticmethod
    def create(description: str, distrito: str = "") -> Local:
        normalized = LocationRepository._normalize_description(description)
        location = Local(nome_local=normalized, distrito=distrito or normalized)
        db.session.add(location)
        db.session.flush()
        return location

    @staticmethod
    def _normalize_description(value: str) -> str:
        return re.sub(r"\s+", " ", (value or "").strip())

    @staticmethod
    def trecho(origin_id: int, destination_id: int) -> Trecho | None:
        return db.session.scalar(
            select(Trecho).where(
                Trecho.id_local_origem == origin_id,
                Trecho.id_local_destino == destination_id,
            )
        )

    @staticmethod
    def get_or_create_route(origin_name: str, destination_name: str) -> Trecho:
        origin = LocationRepository.get_by_description(origin_name)
        if origin is None:
            origin = LocationRepository.create(origin_name)

        destination = LocationRepository.get_by_description(destination_name)
        if destination is None:
            destination = LocationRepository.create(destination_name)

        route = db.session.scalar(
            select(Trecho).where(
                Trecho.id_local_origem == origin.id_local,
                Trecho.id_local_destino == destination.id_local,
            )
        )
        if route is None:
            route = Trecho(id_local_origem=origin.id_local, id_local_destino=destination.id_local)
            db.session.add(route)
            db.session.flush()
        return route


class VehicleRepository:
    @staticmethod
    def list_by_driver(driver_id: int, include_inactive: bool = True) -> list[Veiculo]:
        query = select(Veiculo).where(Veiculo.id_motorista == driver_id)
        if not include_inactive:
            query = query.where(Veiculo.ativo.is_(True))
        return list(db.session.scalars(query.order_by(Veiculo.ativo.desc(), Veiculo.marca, Veiculo.modelo)))

    @staticmethod
    def owned(vehicle_id: int, driver_id: int, for_update: bool = False) -> Veiculo | None:
        query = select(Veiculo).where(
            Veiculo.id_veiculo == vehicle_id,
            Veiculo.id_motorista == driver_id,
        )
        if for_update:
            query = query.with_for_update()
        return db.session.scalar(query)

    @staticmethod
    def plate_exists(plate: str, exclude_vehicle_id: int | None = None) -> bool:
        conditions = [func.upper(Veiculo.placa) == plate.upper()]
        if exclude_vehicle_id is not None:
            conditions.append(Veiculo.id_veiculo != exclude_vehicle_id)
        return bool(db.session.scalar(select(exists().where(and_(*conditions)))))

    @staticmethod
    def has_any_rides(vehicle_id: int) -> bool:
        return bool(db.session.scalar(select(exists().where(Carona.id_veiculo == vehicle_id))))

    @staticmethod
    def has_future_rides(vehicle_id: int, now: datetime) -> bool:
        future = or_(
            Carona.data_saida > now.date(),
            and_(Carona.data_saida == now.date(), Carona.horario_saida > now.time()),
        )
        return bool(
            db.session.scalar(
                select(exists().where(and_(Carona.id_veiculo == vehicle_id, future, Carona.status != "CANCELADA")))
            )
        )


class RideRepository:
    @staticmethod
    def list_by_driver(driver_id: int) -> list[Carona]:
        query = (
            select(Carona)
            .where(Carona.id_motorista == driver_id)
            .options(
                joinedload(Carona.trecho).joinedload(Trecho.origem),
                joinedload(Carona.trecho).joinedload(Trecho.destino),
                joinedload(Carona.veiculo),
                selectinload(Carona.reservas),
            )
            .order_by(Carona.data_saida.desc(), Carona.horario_saida.desc())
        )
        return list(db.session.scalars(query).unique())

    @staticmethod
    def owned(ride_id: int, driver_id: int, for_update: bool = False) -> Carona | None:
        query = (
            select(Carona)
            .where(Carona.id_carona == ride_id, Carona.id_motorista == driver_id)
            .options(
                joinedload(Carona.trecho).joinedload(Trecho.origem),
                joinedload(Carona.trecho).joinedload(Trecho.destino),
                joinedload(Carona.veiculo),
                selectinload(Carona.reservas).joinedload(Reserva.passageiro).joinedload(Passageiro.pessoa),
            )
        )
        if for_update:
            query = query.with_for_update()
        return db.session.scalar(query)

    @staticmethod
    def by_id_for_update(ride_id: int) -> Carona | None:
        return db.session.scalar(
            select(Carona)
            .where(Carona.id_carona == ride_id)
            .options(selectinload(Carona.reservas))
            .with_for_update()
        )

    @staticmethod
    def search_available(
        passenger_id: int,
        now: datetime,
        origin_id: int | None = None,
        destination_id: int | None = None,
        ride_date: date | None = None,
    ) -> list[Carona]:
        confirmed_count = (
            select(Reserva.id_carona.label("ride_id"), func.count(Reserva.id_reserva).label("confirmed"))
            .where(Reserva.status == "CONFIRMADO")
            .group_by(Reserva.id_carona)
            .subquery()
        )
        has_requested = exists().where(
            Reserva.id_carona == Carona.id_carona,
            Reserva.id_passageiro == passenger_id,
        )
        future = or_(
            Carona.data_saida > now.date(),
            and_(Carona.data_saida == now.date(), Carona.horario_saida > now.time()),
        )
        query = (
            select(Carona)
            .outerjoin(confirmed_count, confirmed_count.c.ride_id == Carona.id_carona)
            .where(
                Carona.status == "DISPONIVEL",
                future,
                func.coalesce(confirmed_count.c.confirmed, 0) < Carona.numero_vagas,
                ~has_requested,
            )
            .options(
                joinedload(Carona.motorista).joinedload(Motorista.pessoa),
                joinedload(Carona.trecho).joinedload(Trecho.origem),
                joinedload(Carona.trecho).joinedload(Trecho.destino),
                joinedload(Carona.veiculo),
                selectinload(Carona.reservas),
            )
            .order_by(Carona.data_saida, Carona.horario_saida)
        )
        if origin_id:
            query = query.where(Carona.trecho.has(Trecho.id_local_origem == origin_id))
        if destination_id:
            query = query.where(Carona.trecho.has(Trecho.id_local_destino == destination_id))
        if ride_date:
            query = query.where(Carona.data_saida == ride_date)
        return list(db.session.scalars(query).unique())


class ReservationRepository:
    @staticmethod
    def existing(ride_id: int, passenger_id: int) -> Reserva | None:
        return db.session.scalar(
            select(Reserva).where(
                Reserva.id_carona == ride_id,
                Reserva.id_passageiro == passenger_id,
            )
        )

    @staticmethod
    def owned_by_driver(reservation_id: int, driver_id: int, for_update: bool = False) -> Reserva | None:
        query = (
            select(Reserva)
            .join(Reserva.carona)
            .where(Reserva.id_reserva == reservation_id, Carona.id_motorista == driver_id)
            .options(joinedload(Reserva.carona).selectinload(Carona.reservas))
        )
        if for_update:
            query = query.with_for_update()
        return db.session.scalar(query)

    @staticmethod
    def passenger_dashboard(passenger_id: int) -> tuple[list[Reserva], list[Reserva]]:
        query = (
            select(Reserva)
            .join(Reserva.carona)
            .where(Reserva.id_passageiro == passenger_id, Reserva.status.in_(["CONFIRMADO", "PENDENTE"]))
            .options(
                joinedload(Reserva.carona).joinedload(Carona.motorista).joinedload(Motorista.pessoa),
                joinedload(Reserva.carona).joinedload(Carona.trecho).joinedload(Trecho.origem),
                joinedload(Reserva.carona).joinedload(Carona.trecho).joinedload(Trecho.destino),
                joinedload(Reserva.carona).joinedload(Carona.veiculo),
            )
            .order_by(Carona.data_saida, Carona.horario_saida)
        )
        reservations = list(db.session.scalars(query).unique())
        confirmed = [item for item in reservations if item.status == "CONFIRMADO"]
        pending = [item for item in reservations if item.status == "PENDENTE"]
        return confirmed, pending

    @staticmethod
    def cancel_other_pending(ride_id: int, except_reservation_id: int) -> int:
        pending = list(
            db.session.scalars(
                select(Reserva).where(
                    Reserva.id_carona == ride_id,
                    Reserva.id_reserva != except_reservation_id,
                    Reserva.status == "PENDENTE",
                )
            )
        )
        for reservation in pending:
            reservation.status = "CANCELADO"
        return len(pending)
