# Carona Alegre

Sistema web completo para oferta e solicitação de caronas, desenvolvido com Flask, SQLite, SQLAlchemy, Flask-Login, Flask-WTF, Bootstrap 5 e JavaScript.

## Observação importante sobre os arquivos de banco recebidos

Os arquivos `DDL.sql` e `DML.sql` fornecidos utilizam sintaxe de **MySQL**, não de PostgreSQL. Exemplos: `AUTO_INCREMENT`, `USE carona_alegre` e `CREATE DATABASE IF NOT EXISTS`.

Além disso, o DDL original não contém todos os dados necessários ao sistema solicitado. Faltam:

- uma tabela para email, telefone, senha hash, tipo e estado da conta;
- `marca`, `cor`, `ano` e estado ativo do veículo;
- número de vagas e status operacional da carona;
- restrição para impedir duas solicitações do mesmo passageiro na mesma carona;
- possibilidade de cadastrar uma pessoa sem data de nascimento e um motorista sem CNH/método de pagamento, pois esses campos não fazem parte do formulário solicitado.

Por isso, o arquivo `database/postgresql_required_patch.sql` preserva as tabelas existentes e aplica apenas os complementos indispensáveis. Ele **não cria outro banco** e não recria o esquema original.

O mapeamento considera o comportamento padrão do PostgreSQL: nomes não delimitados são convertidos para minúsculas. Assim, `Pessoa`, `idPessoa` e `dataNascimento` são tratados como `pessoa`, `idpessoa` e `datanascimento`. Caso o banco real tenha sido criado com identificadores entre aspas e CamelCase, ajuste os nomes físicos em `models/entities.py`.

## Funcionalidades implementadas

- Cadastro de passageiro ou motorista com validação de CPF, telefone, email único, CPF único e confirmação de senha.
- Senhas armazenadas somente como hash Werkzeug.
- Login, sessão, opção de manter conectado, logout por POST e Flask-Login.
- Redirecionamento automático para a Home correta de acordo com o tipo da conta.
- Navbar fixa, responsiva e específica para cada perfil.
- Perfil e alteração de senha.
- Cadastro, edição, exclusão ou desativação de veículos.
- Bloqueio da exclusão de veículo associado a carona futura.
- Criação de carona usando somente veículos ativos do motorista.
- Home do motorista com cards de todas as caronas.
- Tela de solicitações, aceite e recusa.
- Reserva transacional de vagas com bloqueio de linha no banco.
- Cancelamento automático das solicitações pendentes quando a última vaga é preenchida.
- Home do passageiro separada em caronas confirmadas e solicitações pendentes.
- Pesquisa por origem, destino e data.
- Exibição somente de caronas futuras, disponíveis e com vagas.
- Bloqueio de solicitação duplicada.
- Proteção CSRF, ORM contra SQL Injection e autorização por tipo de usuário.
- Páginas personalizadas de erro 403, 404 e 500.

## Estrutura

```text
carona-alegre/
├── app.py                         # Application factory e entrada do Flask
├── config.py                      # Variáveis de ambiente e conexão
├── requirements.txt               # Dependências de execução
├── requirements-dev.txt           # Testes e análise estática
├── .env.example                   # Modelo de configuração
├── controllers/
│   ├── auth_controller.py         # Cadastro e autenticação
│   ├── driver_controller.py       # Regras do motorista
│   ├── passenger_controller.py    # Regras do passageiro
│   ├── profile_controller.py      # Perfil e senha
│   ├── forms.py                   # Formulários WTForms
│   ├── security.py                # Decorador de permissão
│   ├── utils.py                   # CPF, normalizações e horário local
│   └── exceptions.py              # Erros de domínio
├── database/
│   ├── extensions.py              # SQLAlchemy, LoginManager e CSRF
│   ├── repositories.py            # Camada isolada de acesso aos dados
│   ├── healthcheck.py             # Comando `flask check-db`
│   ├── postgresql_required_patch.sql
│   ├── postgresql_optional_locations.sql
│   ├── DDL_original_recebido.sql
│   └── DML_original_recebido.sql
├── models/
│   └── entities.py                # Mapeamento ORM das tabelas
├── routes/
│   ├── main.py                    # Home e redirecionamento
│   ├── auth.py                    # Rotas públicas
│   ├── driver.py                  # Blueprint do motorista
│   ├── passenger.py               # Blueprint do passageiro
│   └── profile.py                 # Blueprint de perfil
├── templates/                     # Views Jinja2
├── static/
│   ├── css/style.css
│   ├── js/main.js
│   └── img/                       # Logo e ilustração local
└── tests/test_utils.py
```

## 1. Banco de dados SQLite padrão

Este projeto usa SQLite por padrão, com criação automática do arquivo `carona_alegre.db` na primeira execução.

Os arquivos em `database/postgresql_required_patch.sql` e `database/postgresql_optional_locations.sql` são scripts de auxilio para adaptações em PostgreSQL legadas, mas não são necessários para a execução com SQLite.

Se você quiser manter um banco existente diferente, defina `DATABASE_URL` em `.env` para a URL SQLAlchemy apropriada.

### Tabela nova necessária

```text
conta_usuario
```

Ela é ligada em relação 1:1 a `pessoa` por `idpessoa` e armazena apenas dados de autenticação e contato.

### Colunas novas necessárias

```text
veiculo.marca
veiculo.cor
veiculo.ano
veiculo.ativo
carona.numerovagas
carona.status
```

O patch também torna opcionais `pessoa.datanascimento`, `motorista.cnh` e `motorista.metodopagamento`, pois o formulário definido no requisito não coleta esses dados.

## 2. Criar o ambiente Python

Recomendado: Python 3.11 ou superior.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

## 3. Configurar `.env`

Exemplo:

```dotenv
FLASK_ENV=development
SECRET_KEY=gere-uma-chave-grande-e-aleatoria
DATABASE_URL=sqlite:///carona_alegre.db
APP_TIMEZONE=America/Sao_Paulo
SESSION_COOKIE_SECURE=false
```

Para gerar uma chave segura:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Em produção, com HTTPS, use:

```dotenv
SESSION_COOKIE_SECURE=true
```

## 4. Validar a conexão e o esquema

```bash
flask --app app check-db
```

O comando informa precisamente qualquer tabela ou coluna ausente. No modo SQLite padrão, o aplicativo cria o arquivo de banco automaticamente na primeira execução, mas não recria nem substitui um banco existente com dados.

## 5. Executar

Desenvolvimento:

```bash
flask --app app run --debug
```

Acesse:

```text
http://127.0.0.1:5000
```

Produção Linux com Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
```

## Fluxo inicial

1. Aplique o patch SQL.
2. Abra `/auth/cadastro`.
3. Cadastre um motorista.
4. Faça login e cadastre um veículo.
5. Crie uma carona.
6. Cadastre um passageiro em outra sessão/navegador.
7. Pesquise e solicite a carona.
8. Volte à conta do motorista e aceite a solicitação.
9. A vaga aparecerá como confirmada na Home do passageiro.

## Regras de vagas

Cada solicitação representa uma vaga. O motorista pode aceitar solicitações até preencher `carona.numerovagas`. Quando a última vaga é confirmada:

- `carona.status` passa para `LOTADA`;
- a carona deixa de aparecer na pesquisa;
- todas as outras solicitações ainda pendentes são alteradas para `CANCELADO`.

Isso preserva a possibilidade de aceitar mais de um passageiro quando a carona possui várias vagas.

## Segurança aplicada

- Werkzeug `generate_password_hash` e `check_password_hash`.
- Queries parametrizadas pelo SQLAlchemy.
- Proteção CSRF em todos os formulários e ações POST.
- Cookies `HttpOnly` e `SameSite=Lax`.
- Rotas protegidas por login e papel.
- Normalização de email, CPF, telefone e placa.
- Restrição única de solicitação por passageiro/carona no banco.
- Transações e `SELECT ... FOR UPDATE` nas operações concorrentes de vaga.

## Testes

Instale as dependências de desenvolvimento:

```bash
pip install -r requirements-dev.txt
pytest
```

O fluxo funcional completo foi validado em banco temporário: cadastro de motorista, veículo, carona, cadastro de passageiro, pesquisa, solicitação, aceite e confirmação.
