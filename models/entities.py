"""Mapeamento ORM das tabelas existentes e dos complementos necessários."""
from __future__ import annotations

from datetime import date, datetime, time
from typing import Optional

from flask_login import UserMixin
from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.extensions import db


class Pessoa(db.Model):
    __tablename__ = "pessoa"

    id_pessoa: Mapped[int] = mapped_column("idpessoa", Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    cpf: Mapped[str] = mapped_column(String(11), nullable=False, unique=True)
    data_nascimento: Mapped[Optional[date]] = mapped_column("datanascimento", Date, nullable=True)
    genero: Mapped[Optional[str]] = mapped_column(String(1), nullable=True)

    conta: Mapped["ContaUsuario"] = relationship(back_populates="pessoa", uselist=False)
    motorista: Mapped[Optional["Motorista"]] = relationship(back_populates="pessoa", uselist=False)
    passageiro: Mapped[Optional["Passageiro"]] = relationship(back_populates="pessoa", uselist=False)


class ContaUsuario(UserMixin, db.Model):
    __tablename__ = "conta_usuario"
    __table_args__ = (
        CheckConstraint("tipo IN ('MOTORISTA', 'PASSAGEIRO')", name="ck_conta_usuario_tipo"),
    )

    id_pessoa: Mapped[int] = mapped_column("idpessoa", ForeignKey("pessoa.idpessoa"), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    telefone: Mapped[str] = mapped_column(String(11), nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    ativo: Mapped[bool] = mapped_column(nullable=False, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    pessoa: Mapped[Pessoa] = relationship(back_populates="conta")

    def get_id(self) -> str:
        return str(self.id_pessoa)

    @property
    def is_active(self) -> bool:
        return self.ativo

    @property
    def nome(self) -> str:
        return self.pessoa.nome

    @property
    def primeiro_nome(self) -> str:
        return self.nome.split()[0] if self.nome else "Usuário"

    @property
    def is_motorista(self) -> bool:
        return self.tipo == "MOTORISTA"

    @property
    def is_passageiro(self) -> bool:
        return self.tipo == "PASSAGEIRO"


class Motorista(db.Model):
    __tablename__ = "motorista"

    id_motorista: Mapped[int] = mapped_column("idmotorista", ForeignKey("pessoa.idpessoa"), primary_key=True)
    cnh: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)
    metodo_pagamento: Mapped[Optional[str]] = mapped_column("metodopagamento", String(50), nullable=True)

    pessoa: Mapped[Pessoa] = relationship(back_populates="motorista")
    veiculos: Mapped[list["Veiculo"]] = relationship(back_populates="motorista", lazy="selectin")
    caronas: Mapped[list["Carona"]] = relationship(back_populates="motorista", lazy="selectin")


class Passageiro(db.Model):
    __tablename__ = "passageiro"

    id_passageiro: Mapped[int] = mapped_column("idpassageiro", ForeignKey("pessoa.idpessoa"), primary_key=True)

    pessoa: Mapped[Pessoa] = relationship(back_populates="passageiro")
    reservas: Mapped[list["Reserva"]] = relationship(back_populates="passageiro", lazy="selectin")


class Veiculo(db.Model):
    __tablename__ = "veiculo"
    __table_args__ = (
        CheckConstraint("capacidade > 0", name="ck_veiculo_capacidade"),
    )

    id_veiculo: Mapped[int] = mapped_column("idveiculo", Integer, primary_key=True)
    placa: Mapped[str] = mapped_column(String(7), nullable=False, unique=True)
    modelo: Mapped[str] = mapped_column(String(50), nullable=False)
    capacidade: Mapped[int] = mapped_column(Integer, nullable=False)
    id_motorista: Mapped[int] = mapped_column("idmotorista", ForeignKey("motorista.idmotorista"), nullable=False)
    marca: Mapped[str] = mapped_column(String(50), nullable=False)
    cor: Mapped[str] = mapped_column(String(30), nullable=False)
    ano: Mapped[int] = mapped_column(Integer, nullable=False)
    ativo: Mapped[bool] = mapped_column(nullable=False, default=True)

    motorista: Mapped[Motorista] = relationship(back_populates="veiculos")
    caronas: Mapped[list["Carona"]] = relationship(back_populates="veiculo")

    @property
    def descricao(self) -> str:
        return f"{self.marca} {self.modelo} • {self.placa}"


class Local(db.Model):
    __tablename__ = "local"

    id_local: Mapped[int] = mapped_column("idlocal", Integer, primary_key=True)
    nome_local: Mapped[str] = mapped_column("nomelocal", String(100), nullable=False)
    distrito: Mapped[str] = mapped_column(String(100), nullable=False)

    @property
    def descricao(self) -> str:
        return f"{self.nome_local} — {self.distrito}"


class Trecho(db.Model):
    __tablename__ = "trecho"
    __table_args__ = (
        UniqueConstraint("idlocalorigem", "idlocaldestino", name="uq_trecho_origem_destino"),
    )

    id_trecho: Mapped[int] = mapped_column("idtrecho", Integer, primary_key=True)
    id_local_origem: Mapped[int] = mapped_column("idlocalorigem", ForeignKey("local.idlocal"), nullable=False)
    id_local_destino: Mapped[int] = mapped_column("idlocaldestino", ForeignKey("local.idlocal"), nullable=False)

    origem: Mapped[Local] = relationship(foreign_keys=[id_local_origem])
    destino: Mapped[Local] = relationship(foreign_keys=[id_local_destino])
    caronas: Mapped[list["Carona"]] = relationship(back_populates="trecho")


class Carona(db.Model):
    __tablename__ = "carona"
    __table_args__ = (
        CheckConstraint("numerovagas > 0", name="ck_carona_numero_vagas"),
        CheckConstraint("status IN ('DISPONIVEL', 'LOTADA', 'CANCELADA', 'ENCERRADA')", name="ck_carona_status"),
    )

    id_carona: Mapped[int] = mapped_column("idcarona", Integer, primary_key=True)
    data_saida: Mapped[date] = mapped_column("datasaida", Date, nullable=False)
    horario_saida: Mapped[time] = mapped_column("horariosaida", Time, nullable=False)
    valor: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    id_motorista: Mapped[int] = mapped_column("idmotorista", ForeignKey("motorista.idmotorista"), nullable=False)
    id_veiculo: Mapped[int] = mapped_column("idveiculo", ForeignKey("veiculo.idveiculo"), nullable=False)
    id_trecho: Mapped[int] = mapped_column("idtrecho", ForeignKey("trecho.idtrecho"), nullable=False)
    numero_vagas: Mapped[int] = mapped_column("numerovagas", Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DISPONIVEL")

    motorista: Mapped[Motorista] = relationship(back_populates="caronas")
    veiculo: Mapped[Veiculo] = relationship(back_populates="caronas")
    trecho: Mapped[Trecho] = relationship(back_populates="caronas")
    reservas: Mapped[list["Reserva"]] = relationship(back_populates="carona", lazy="selectin")

    @property
    def data_hora_saida(self) -> datetime:
        return datetime.combine(self.data_saida, self.horario_saida)

    @property
    def reservas_confirmadas(self) -> int:
        return sum(1 for reserva in self.reservas if reserva.status == "CONFIRMADO")

    @property
    def vagas_restantes(self) -> int:
        return max(self.numero_vagas - self.reservas_confirmadas, 0)

    @property
    def status_exibicao(self) -> str:
        if self.status == "CANCELADA":
            return "Cancelada"
        if self.data_hora_saida <= datetime.now():
            return "Encerrada"
        if self.vagas_restantes <= 0 or self.status == "LOTADA":
            return "Lotada"
        return "Disponível"


class Reserva(db.Model):
    __tablename__ = "reserva"
    __table_args__ = (
        UniqueConstraint("idcarona", "idpassageiro", name="uq_reserva_carona_passageiro"),
        CheckConstraint("status IN ('PENDENTE', 'CONFIRMADO', 'RECUSADO', 'CANCELADO')", name="ck_reserva_status"),
    )

    id_reserva: Mapped[int] = mapped_column("idreserva", Integer, primary_key=True)
    data_reserva: Mapped[datetime] = mapped_column("datareserva", DateTime, nullable=False, default=datetime.now)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDENTE")
    id_carona: Mapped[int] = mapped_column("idcarona", ForeignKey("carona.idcarona"), nullable=False)
    id_passageiro: Mapped[int] = mapped_column("idpassageiro", ForeignKey("passageiro.idpassageiro"), nullable=False)

    carona: Mapped[Carona] = relationship(back_populates="reservas")
    passageiro: Mapped[Passageiro] = relationship(back_populates="reservas")


class Avaliacao(db.Model):
    __tablename__ = "avaliacao"

    id_avaliacao: Mapped[int] = mapped_column("idavaliacao", Integer, primary_key=True)
    nota: Mapped[int] = mapped_column(Integer, nullable=False)
    comentario: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    id_carona: Mapped[int] = mapped_column("idcarona", ForeignKey("carona.idcarona"), nullable=False)
    id_avaliador: Mapped[int] = mapped_column("idavaliador", ForeignKey("pessoa.idpessoa"), nullable=False)
    id_avaliado: Mapped[int] = mapped_column("idavaliado", ForeignKey("pessoa.idpessoa"), nullable=False)
