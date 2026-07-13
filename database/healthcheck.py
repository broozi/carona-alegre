"""Comando CLI para validar se o banco de dados possui a estrutura esperada."""
from __future__ import annotations

import click
from flask import Flask
from sqlalchemy import inspect, text

from database.extensions import db


REQUIRED_COLUMNS = {
    "pessoa": {"idpessoa", "nome", "cpf", "datanascimento", "genero"},
    "motorista": {"idmotorista", "cnh", "metodopagamento"},
    "passageiro": {"idpassageiro"},
    "veiculo": {"idveiculo", "placa", "modelo", "capacidade", "idmotorista", "marca", "cor", "ano", "ativo"},
    "local": {"idlocal", "nomelocal", "distrito"},
    "trecho": {"idtrecho", "idlocalorigem", "idlocaldestino"},
    "carona": {"idcarona", "datasaida", "horariosaida", "valor", "idmotorista", "idveiculo", "idtrecho", "numerovagas", "status"},
    "reserva": {"idreserva", "datareserva", "status", "idcarona", "idpassageiro"},
    "conta_usuario": {"idpessoa", "email", "telefone", "senha_hash", "tipo", "ativo", "criado_em", "atualizado_em"},
}


def register_commands(app: Flask) -> None:
    @app.cli.command("check-db")
    def check_db():
        """Confere conexão, tabelas e colunas obrigatórias."""
        db.session.execute(text("SELECT 1"))
        inspector = inspect(db.engine)
        existing_tables = set(inspector.get_table_names())
        errors: list[str] = []

        for table, expected_columns in REQUIRED_COLUMNS.items():
            if table not in existing_tables:
                errors.append(f"Tabela ausente: {table}")
                continue
            existing_columns = {column["name"] for column in inspector.get_columns(table)}
            missing = expected_columns - existing_columns
            if missing:
                errors.append(f"Colunas ausentes em {table}: {', '.join(sorted(missing))}")

        if errors:
            click.secho("Banco conectado, mas a estrutura está incompleta:", fg="yellow", bold=True)
            for error in errors:
                click.echo(f"  - {error}")
            raise click.ClickException("Verifique a estrutura do banco de dados e ajuste o esquema conforme necessário.")

        click.secho("Conexão e estrutura do banco validadas com sucesso.", fg="green", bold=True)
