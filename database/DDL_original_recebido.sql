CREATE DATABASE IF NOT EXISTS carona_alegre;
USE carona_alegre;

CREATE TABLE IF NOT EXISTS Pessoa (
    idPessoa INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    cpf VARCHAR(11) UNIQUE NOT NULL,
    dataNascimento DATE NOT NULL,
    genero VARCHAR(1)
);

CREATE TABLE IF NOT EXISTS Motorista (
    idMotorista INT PRIMARY KEY,
    cnh VARCHAR(9) NOT NULL UNIQUE,
    metodoPagamento VARCHAR(50) NOT NULL,

    FOREIGN KEY (idMotorista)
        REFERENCES Pessoa(idPessoa)
);

CREATE TABLE IF NOT EXISTS Passageiro (
    idPassageiro INT PRIMARY KEY,

    FOREIGN KEY (idPassageiro)
        REFERENCES Pessoa(idPessoa)
);

CREATE TABLE IF NOT EXISTS Veiculo (
    idVeiculo INT AUTO_INCREMENT PRIMARY KEY,
    placa VARCHAR(7) NOT NULL UNIQUE,
    modelo VARCHAR(50) NOT NULL,
    capacidade INT NOT NULL,
    idMotorista INT NOT NULL,

    FOREIGN KEY (idMotorista)
        REFERENCES Motorista(idMotorista)
);

CREATE TABLE IF NOT EXISTS Local (
    idLocal INT AUTO_INCREMENT PRIMARY KEY,
    nomeLocal VARCHAR(100) NOT NULL,
    distrito VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS Trecho (
    idTrecho INT AUTO_INCREMENT PRIMARY KEY,
    idLocalOrigem INT NOT NULL,
    idLocalDestino INT NOT NULL,

    FOREIGN KEY (idLocalOrigem)
        REFERENCES Local(idLocal),

    FOREIGN KEY (idLocalDestino)
        REFERENCES Local(idLocal)
);

CREATE TABLE IF NOT EXISTS Carona (
    idCarona INT AUTO_INCREMENT PRIMARY KEY,
    dataSaida DATE NOT NULL,
    horarioSaida TIME NOT NULL,
    valor DECIMAL(6,2),

    idMotorista INT NOT NULL,
    idVeiculo INT NOT NULL,
    idTrecho INT NOT NULL,

    FOREIGN KEY (idMotorista)
        REFERENCES Motorista(idMotorista),

    FOREIGN KEY (idVeiculo)
        REFERENCES Veiculo(idVeiculo),

    FOREIGN KEY (idTrecho)
        REFERENCES Trecho(idTrecho)
);

CREATE TABLE IF NOT EXISTS Reserva (
    idReserva INT AUTO_INCREMENT PRIMARY KEY,
    dataReserva TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL,
    idCarona INT NOT NULL,
    idPassageiro INT NOT NULL,

    FOREIGN KEY (idCarona)
        REFERENCES Carona(idCarona),

    FOREIGN KEY (idPassageiro)
        REFERENCES Passageiro(idPassageiro)
);

CREATE TABLE IF NOT EXISTS Avaliacao (
    idAvaliacao INT AUTO_INCREMENT PRIMARY KEY,
    nota INT NOT NULL,
    comentario VARCHAR(500),

    idCarona INT NOT NULL,
    idAvaliador INT NOT NULL,
    idAvaliado INT NOT NULL,

    FOREIGN KEY (idCarona)
        REFERENCES Carona(idCarona),

    FOREIGN KEY (idAvaliador)
        REFERENCES Pessoa(idPessoa),

    FOREIGN KEY (idAvaliado)
        REFERENCES Pessoa(idPessoa)
);
