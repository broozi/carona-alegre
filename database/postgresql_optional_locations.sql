-- Opcional: use somente se as localidades do DML recebido ainda não estiverem no banco.
BEGIN;

WITH dados(nomelocal, distrito) AS (
    VALUES
    ('Centro de Alegre', 'Alegre'),
    ('UFES - Campus Alegre', 'Alegre'),
    ('IFES - Campus de Alegre', 'Rive'),
    ('Rodoviária de Alegre', 'Alegre'),
    ('Parque de Exposições', 'Alegre'),
    ('Praça Seis de Janeiro', 'Alegre'),
    ('Prefeitura Municipal', 'Alegre'),
    ('Correios', 'Alegre'),
    ('Igreja Matriz', 'Alegre'),
    ('Centro de Celina', 'Celina'),
    ('Centro de Rive', 'Rive'),
    ('Centro de Anutiba', 'Anutiba'),
    ('Centro de Café', 'Café'),
    ('Centro de Araraí', 'Araraí'),
    ('Centro de São João do Norte', 'São João do Norte')
)
INSERT INTO local (nomelocal, distrito)
SELECT d.nomelocal, d.distrito
FROM dados d
WHERE NOT EXISTS (
    SELECT 1 FROM local l WHERE l.nomelocal = d.nomelocal AND l.distrito = d.distrito
);

INSERT INTO trecho (idlocalorigem, idlocaldestino)
SELECT origem.idlocal, destino.idlocal
FROM local origem
CROSS JOIN local destino
WHERE origem.idlocal <> destino.idlocal
  AND NOT EXISTS (
      SELECT 1 FROM trecho t
      WHERE t.idlocalorigem = origem.idlocal
        AND t.idlocaldestino = destino.idlocal
  );

COMMIT;
