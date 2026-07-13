"""Regras de autenticação e cadastro."""
from __future__ import annotations

from flask_login import login_user
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from controllers.exceptions import BusinessError
from controllers.utils import normalize_email, only_digits
from database.extensions import db
from database.repositories import UserRepository
from models import ContaUsuario, Motorista, Passageiro, Pessoa


def authenticate(email: str, password: str, remember: bool = False) -> ContaUsuario:
    user = UserRepository.by_email(normalize_email(email))
    if not user or not check_password_hash(user.senha_hash, password):
        raise BusinessError("Email ou senha incorretos.")
    if not user.ativo:
        raise BusinessError("Esta conta está desativada.")
    login_user(user, remember=remember)
    return user


def register_user(form) -> None:
    email = normalize_email(form.email.data)
    cpf = only_digits(form.cpf.data)
    phone = only_digits(form.telefone.data)

    if UserRepository.email_exists(email):
        raise BusinessError("Já existe uma conta cadastrada com este email.")
    if UserRepository.cpf_exists(cpf):
        raise BusinessError("Já existe uma conta cadastrada com este CPF.")

    person = Pessoa(nome=form.nome.data.strip(), cpf=cpf, data_nascimento=None, genero=None)
    db.session.add(person)
    db.session.flush()

    account = ContaUsuario(
        id_pessoa=person.id_pessoa,
        email=email,
        telefone=phone,
        senha_hash=generate_password_hash(form.senha.data),
        tipo=form.tipo.data,
        ativo=True,
    )
    db.session.add(account)

    if form.tipo.data == "MOTORISTA":
        db.session.add(Motorista(id_motorista=person.id_pessoa, cnh=None, metodo_pagamento=None))
    else:
        db.session.add(Passageiro(id_passageiro=person.id_pessoa))

    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise BusinessError("Não foi possível concluir o cadastro. Verifique email e CPF.") from exc
