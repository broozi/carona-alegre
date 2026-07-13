"""Atualização de perfil e senha."""
from __future__ import annotations

from werkzeug.security import check_password_hash, generate_password_hash

from controllers.exceptions import BusinessError
from controllers.utils import normalize_email, only_digits
from database.extensions import db
from database.repositories import UserRepository, VehicleRepository


def update_profile(user, form) -> None:
    email = normalize_email(form.email.data)
    if UserRepository.email_exists(email, exclude_person_id=user.id_pessoa):
        raise BusinessError("Este email já está sendo utilizado por outra conta.")

    user.pessoa.nome = form.nome.data.strip()
    user.email = email
    user.telefone = only_digits(form.telefone.data)
    db.session.commit()


def change_password(user, form) -> None:
    if not check_password_hash(user.senha_hash, form.senha_atual.data):
        raise BusinessError("A senha atual está incorreta.")
    if check_password_hash(user.senha_hash, form.nova_senha.data):
        raise BusinessError("A nova senha deve ser diferente da senha atual.")
    user.senha_hash = generate_password_hash(form.nova_senha.data)
    db.session.commit()


def profile_vehicles(user):
    if not user.is_motorista:
        return []
    return VehicleRepository.list_by_driver(user.id_pessoa)
