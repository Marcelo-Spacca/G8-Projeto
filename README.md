# Projeto 1 (SI 26.2) — Registro verificável do uso de IA

Aplicação desktop em Python para registrar interações com IA, verificar as fontes citadas e gerar um relatório para o professor.

---

## 1. Estrutura do código e lógica de funcionamento

### Tecnologias

| Parte | Tecnologia |
|---|---|
| Linguagem | Python |
| Banco de dados | PostgreSQL |
| Acesso ao banco | SQLAlchemy + psycopg |
| Senhas | hash com `hashlib.scrypt` (biblioteca padrão) |
| Configuração | arquivo `.env` (python-dotenv) |
| Testes | pytest |
| Interface | menu de console (por enquanto); PySide6 planejado |

### Arquitetura em camadas

O código é um monolito dividido em camadas. **Cada camada só chama a que está abaixo dela**, nunca a de cima.

```
ui/           interface com o usuário (menu de console)
   ↓
services/     regras de negócio
   ↓
repository/   modelos e acesso ao banco (SQLAlchemy)
   ↓
PostgreSQL
```

- **ui:** mostra o menu, lê o que o usuário digita e chama os services. Não tem regra de negócio nem acesso ao banco.
- **services:** aplicam as regras do projeto (validações, permissões, hash de senha). Não conhecem a interface.
- **repository:** lê e grava no banco. Não conhece regra de negócio.

### Estrutura de pastas

```
.
├── main.py            # abre o programa
├── ui/                # menu_console.py
├── services/          # regras de negócio
├── repository/
│   ├── models/        # uma classe SQLAlchemy por tabela
│   └── *_repository.py  # consultas de cada entidade
├── scripts/           # utilitários (criar_tabelas.py)
├── tests/             # testes automatizados
├── pytest.ini
└── requirements.txt
```

### Como uma ação percorre as camadas

Exemplo, o cadastro de um usuário:

1. O **menu** lê nome, e-mail, senha e tipo, e chama `UsuarioService.cadastrar(...)`.
2. O **service** valida os campos, confere se o e-mail já existe, gera o hash da senha e monta o objeto `Usuario`.
3. O **repository** (`UsuarioRepository`) grava no PostgreSQL e devolve o usuário salvo.
4. Se alguma regra for violada, o service levanta `RegraViolada` e o menu mostra a mensagem, sem encerrar o programa.

### Modelo de dados

| Entidade | Relação |
|---|---|
| Usuário (aluno / professor) | — |
| Turma | pertence a um professor |
| Pesquisa | pertence a um aluno; gera 1 relatório |
| Interação | pertence a uma pesquisa |
| Fonte | pertence a uma interação |
| Trecho | pertence a uma fonte |
| Relatório | 1:1 com a pesquisa |

Apagar uma pesquisa apaga em cascata suas interações, fontes, trechos e relatório.

### Funcionalidades implementadas

Cadastro e login (com senha em hash), criação e listagem de pesquisas do aluno, registro e listagem de interações de uma pesquisa.

| RF | O que faz | Onde |
|---|---|---|
| RF13 | Aluno edita ferramenta, pergunta e resposta de uma interação; as fontes ligadas continuam as mesmas | `InteracaoService.editar` / menu da interação, opção 1 |
| RF14 | Aluno exclui uma interação depois de confirmar (s/n); fontes e trechos dela saem junto | `InteracaoService.excluir` / opção 2 |
| RF26 | Ao verificar uma fonte como válida, o aluno pode informar o trecho do seu texto (e onde ele está); dá para ligar outros trechos depois | `FonteService.verificar` e `vincular_trecho` / opções 4 e 5 |
| RF27 | A tela da interação mostra cada fonte com os trechos ligados logo abaixo | `mostrar_interacao` |
| RF18 | Na verificação, o aluno escreve uma anotação sobre o que encontrou; ela fica na fonte e aparece no relatório | `FonteService.verificar` |
| RF20 | O relatório é montado sozinho com interações, fontes, status, anotações e trechos | `RelatorioService.gerar` / professor: opção 2; aluno: dentro da pesquisa |
| RF22 | Cada pesquisa tem um único relatório, criado junto com ela | `PesquisaService.criar` |

Código: `repository/repositories.py` (consultas), `services/servicos.py` (regras), `ui/menu_console.py` (menu).

---

## 2. Como rodar o código e os testes

**Requisitos:** Python 3.11+ e PostgreSQL instalado e rodando.

### Rodar do zero

```bash
# 1. clonar e entrar na pasta
git clone <url-do-repositorio>
cd <pasta-do-projeto>

# 2. criar e ativar o ambiente virtual (Windows)
python -m venv .venv
.venv\Scripts\activate

# 3. instalar as dependências
pip install -r requirements.txt
```

No Linux/macOS, ative com `source .venv/bin/activate`.

### Configurar o banco

1. No PostgreSQL (pgAdmin ou `psql`), crie o banco: `CREATE DATABASE projeto1;`
2. Crie um arquivo `.env` na raiz do projeto com os dados do **seu** PostgreSQL:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=projeto1
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
```

> O `.env` contém credenciais e **nunca deve ser enviado ao GitHub** (já está no `.gitignore`).

### Criar as tabelas e abrir o programa

```bash
python -m scripts.criar_tabelas
python main.py
```

O SQLAlchemy só cria tabelas que ainda não existem. Se um modelo mudar, apague as tabelas e rode `criar_tabelas` de novo.

### Menu de console

`python main.py` abre um menu de texto: cadastrar, entrar, criar pesquisa, listar pesquisas, registrar e ver interações. Textos de várias linhas (pergunta e resposta da IA) terminam com uma linha contendo só `FIM`.

### Testes

```bash
pytest -v
```

- Os testes usam o PostgreSQL de verdade, mas em um **banco separado**, `projeto1_teste`, criado automaticamente (o usuário do `.env` precisa ter permissão para criar bancos). As tabelas são recriadas no início e esvaziadas antes de cada teste.
- O banco `projeto1` nunca é tocado pelos testes.
- Para mudar o nome do banco de teste, defina `DB_NAME_TESTE` no `.env`. O nome **precisa terminar com `_teste`**, senão os testes abortam por segurança.

Comandos úteis:

```bash
pytest tests/test_banco.py -v          # um arquivo
pytest -k "login" -v                   # testes cujo nome contém "login"
pytest -x                              # para no primeiro erro
pytest --collect-only -q               # lista os testes sem rodar
```

Se o comando `pytest` não for reconhecido, use `python -m pytest -v`.

---

## 3. Trabalhando com Git: pull, branch e push

Nunca trabalhe direto na `main`. Cada alteração vai em uma branch própria.

### 1. Atualizar a main local

```bash
git checkout main
git pull origin main
```

### 2. Criar uma branch e entrar nela

```bash
git checkout -b nome-da-branch
```

Use um nome curto que diga o que será feito, por exemplo `feature/cadastro-usuario` ou `fix/ordem-listagem`.

### 3. Fazer as alterações, salvar e enviar

```bash
git status                       # confere o que mudou
git add .                        # adiciona as alterações
git commit -m "descrição curta do que foi feito"
git push -u origin nome-da-branch
```

O `-u` só é necessário no primeiro push da branch; nos seguintes, basta `git push`.

### 4. Abrir o Pull Request

No GitHub, aparecerá o botão **Compare & pull request** para a branch enviada. Abra o PR para a `main`, descreva a mudança e peça revisão de outro integrante antes de fazer o merge.

### Boas práticas

- Rode `pytest` antes de dar push.
- Antes de começar algo novo, atualize a `main` (passo 1) e crie a branch a partir dela.
- Nunca faça commit do `.env`, do `.venv/` nem de senhas.
- Se a `main` avançou enquanto você trabalhava, traga as mudanças para a sua branch: `git checkout main`, `git pull origin main`, `git checkout nome-da-branch`, `git merge main`.
