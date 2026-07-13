USE carona_alegre;



INSERT INTO Local (nomeLocal, distrito) VALUES


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
('Centro de São João do Norte', 'São João do Norte');


INSERT INTO Trecho (idLocalOrigem, idLocalDestino)
SELECT
    l1.idLocal,
    l2.idLocal
FROM Local l1
JOIN Local l2
ON l1.idLocal <> l2.idLocal;