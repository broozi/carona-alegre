"""Formulários e validações server-side com Flask-WTF."""
from __future__ import annotations

from datetime import date

from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    EmailField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TimeField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional, Regexp, ValidationError

from controllers.utils import is_valid_cpf, only_digits


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    senha = PasswordField("Senha", validators=[DataRequired(), Length(max=128)])
    lembrar = SelectField("Manter conectado", choices=[("0", "Não"), ("1", "Sim")], default="0")
    submit = SubmitField("Entrar")


class RegisterForm(FlaskForm):
    nome = StringField("Nome completo", validators=[DataRequired(), Length(min=3, max=100)])
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    cpf = StringField("CPF", validators=[DataRequired(), Length(max=14)])
    telefone = StringField("Telefone", validators=[DataRequired(), Length(max=16)])
    senha = PasswordField(
        "Senha",
        validators=[
            DataRequired(),
            Length(min=8, max=128),
            Regexp(r"^(?=.*[A-Za-z])(?=.*\d).+$", message="Use pelo menos uma letra e um número."),
        ],
    )
    confirmar_senha = PasswordField(
        "Confirmar senha", validators=[DataRequired(), EqualTo("senha", message="As senhas não coincidem.")]
    )
    tipo = SelectField(
        "Tipo de usuário",
        choices=[("PASSAGEIRO", "Passageiro"), ("MOTORISTA", "Motorista")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Criar conta")

    def validate_cpf(self, field):
        if not is_valid_cpf(field.data):
            raise ValidationError("Informe um CPF válido.")

    def validate_telefone(self, field):
        phone = only_digits(field.data)
        if len(phone) not in (10, 11):
            raise ValidationError("Informe um telefone com DDD.")


class RideForm(FlaskForm):
    origem = StringField("Origem", validators=[DataRequired(), Length(max=100)])
    destino = StringField("Destino", validators=[DataRequired(), Length(max=100)])
    data = DateField("Data", validators=[DataRequired()])
    horario = TimeField("Horário", validators=[DataRequired()])
    numero_vagas = IntegerField("Número de vagas", validators=[DataRequired(), NumberRange(min=1, max=99)])
    veiculo = SelectField("Veículo", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Salvar carona")

    def validate_destino(self, field):
        if self.origem.data == field.data:
            raise ValidationError("Origem e destino devem ser diferentes.")

    def validate_data(self, field):
        if field.data < date.today():
            raise ValidationError("A data não pode estar no passado.")


class VehicleForm(FlaskForm):
    modelo = StringField("Modelo", validators=[DataRequired(), Length(max=50)])
    marca = StringField("Marca", validators=[DataRequired(), Length(max=50)])
    cor = StringField("Cor", validators=[DataRequired(), Length(max=30)])
    placa = StringField(
        "Placa",
        validators=[DataRequired(), Regexp(r"^[A-Za-z]{3}-?(?:[0-9][A-Za-z][0-9]{2}|[0-9]{4})$", message="Placa inválida.")],
    )
    ano = IntegerField("Ano", validators=[DataRequired(), NumberRange(min=1900, max=date.today().year + 1)])
    capacidade = IntegerField("Quantidade de lugares", validators=[DataRequired(), NumberRange(min=1, max=50)])
    submit = SubmitField("Salvar veículo")


class SearchRideForm(FlaskForm):
    origem = SelectField("Origem", coerce=int, validators=[Optional()])
    destino = SelectField("Destino", coerce=int, validators=[Optional()])
    data = DateField("Data", validators=[Optional()])
    submit = SubmitField("Pesquisar")


class ProfileForm(FlaskForm):
    nome = StringField("Nome", validators=[DataRequired(), Length(min=3, max=100)])
    telefone = StringField("Telefone", validators=[DataRequired(), Length(max=16)])
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    submit = SubmitField("Salvar alterações")

    def validate_telefone(self, field):
        phone = only_digits(field.data)
        if len(phone) not in (10, 11):
            raise ValidationError("Informe um telefone com DDD.")


class PasswordChangeForm(FlaskForm):
    senha_atual = PasswordField("Senha atual", validators=[DataRequired(), Length(max=128)])
    nova_senha = PasswordField(
        "Nova senha",
        validators=[
            DataRequired(),
            Length(min=8, max=128),
            Regexp(r"^(?=.*[A-Za-z])(?=.*\d).+$", message="Use pelo menos uma letra e um número."),
        ],
    )
    confirmar_senha = PasswordField(
        "Confirmar nova senha",
        validators=[DataRequired(), EqualTo("nova_senha", message="As senhas não coincidem.")],
    )
    submit = SubmitField("Alterar senha")


class EmptyForm(FlaskForm):
    submit = SubmitField("Confirmar")
