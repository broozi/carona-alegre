"""Exceções de domínio convertidas em mensagens amigáveis pelas rotas."""


class BusinessError(Exception):
    """Erro previsto de regra de negócio."""


class NotFoundError(BusinessError):
    pass


class PermissionDeniedError(BusinessError):
    pass
