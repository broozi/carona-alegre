-- CARONA ALEGRE - AJUSTES MÍNIMOS PARA O POSTGRESQL EXISTENTE
-- Este script NÃO cria outro banco e NÃO recria as tabelas já fornecidas.
-- Execute conectado ao banco carona_alegre já existente.
-- Os identificadores abaixo consideram a normalização padrão do PostgreSQL
-- (Pessoa/idPessoa tornam-se pessoa/idpessoa quando não estão entre aspas).

BEGIN;

-- O cadastro solicitado não informa estes campos presentes como NOT NULL no DDL original.
ALTER TABLE pessoa ALTER COLUMN datanascimento DROP NOT NULL;
ALTER TABLE motorista ALTER COLUMN cnh DROP NOT NULL;
ALTER TABLE motorista ALTER COLUMN metodopagamento DROP NOT NULL;

-- Dados de autenticação e contato, ausentes no esquema original.
CREATE TABLE IF NOT EXISTS conta_usuario (
    idpessoa INTEGER PRIMARY KEY REFERENCES pessoa(idpessoa) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    telefone VARCHAR(11) NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_conta_usuario_tipo CHECK (tipo IN ('MOTORISTA', 'PASSAGEIRO'))
);
CREATE INDEX IF NOT EXISTS ix_conta_usuario_email ON conta_usuario (LOWER(email));

-- Campos exigidos no cadastro de veículos e exclusão lógica para preservar histórico.
ALTER TABLE veiculo ADD COLUMN IF NOT EXISTS marca VARCHAR(50);
ALTER TABLE veiculo ADD COLUMN IF NOT EXISTS cor VARCHAR(30);
ALTER TABLE veiculo ADD COLUMN IF NOT EXISTS ano INTEGER;
ALTER TABLE veiculo ADD COLUMN IF NOT EXISTS ativo BOOLEAN NOT NULL DEFAULT TRUE;

UPDATE veiculo SET marca = 'Não informado' WHERE marca IS NULL;
UPDATE veiculo SET cor = 'Não informada' WHERE cor IS NULL;
UPDATE veiculo SET ano = EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER WHERE ano IS NULL;

ALTER TABLE veiculo ALTER COLUMN marca SET NOT NULL;
ALTER TABLE veiculo ALTER COLUMN cor SET NOT NULL;
ALTER TABLE veiculo ALTER COLUMN ano SET NOT NULL;

-- Quantidade de vagas ofertadas e situação operacional da carona.
ALTER TABLE carona ADD COLUMN IF NOT EXISTS numerovagas INTEGER;
ALTER TABLE carona ADD COLUMN IF NOT EXISTS status VARCHAR(20);

UPDATE carona c
SET numerovagas = GREATEST(v.capacidade, 1)
FROM veiculo v
WHERE c.idveiculo = v.idveiculo AND c.numerovagas IS NULL;
UPDATE carona SET status = 'DISPONIVEL' WHERE status IS NULL;

ALTER TABLE carona ALTER COLUMN numerovagas SET NOT NULL;
ALTER TABLE carona ALTER COLUMN status SET NOT NULL;
ALTER TABLE carona ALTER COLUMN status SET DEFAULT 'DISPONIVEL';

-- Restrições necessárias para impedir duplicidades e estados inválidos.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_reserva_carona_passageiro') THEN
        ALTER TABLE reserva ADD CONSTRAINT uq_reserva_carona_passageiro UNIQUE (idcarona, idpassageiro);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_trecho_origem_destino') THEN
        ALTER TABLE trecho ADD CONSTRAINT uq_trecho_origem_destino UNIQUE (idlocalorigem, idlocaldestino);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_veiculo_capacidade') THEN
        ALTER TABLE veiculo ADD CONSTRAINT ck_veiculo_capacidade CHECK (capacidade > 0);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_carona_numero_vagas') THEN
        ALTER TABLE carona ADD CONSTRAINT ck_carona_numero_vagas CHECK (numerovagas > 0);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_carona_status') THEN
        ALTER TABLE carona ADD CONSTRAINT ck_carona_status
            CHECK (status IN ('DISPONIVEL', 'LOTADA', 'CANCELADA', 'ENCERRADA'));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_reserva_status') THEN
        ALTER TABLE reserva ADD CONSTRAINT ck_reserva_status
            CHECK (status IN ('PENDENTE', 'CONFIRMADO', 'RECUSADO', 'CANCELADO'));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_carona_busca
    ON carona (status, datasaida, horariosaida, idtrecho);
CREATE INDEX IF NOT EXISTS ix_reserva_carona_status
    ON reserva (idcarona, status);
CREATE INDEX IF NOT EXISTS ix_veiculo_motorista_ativo
    ON veiculo (idmotorista, ativo);

COMMIT;
