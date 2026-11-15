# Projeto 1 (SI 26.2) — Registro verificável do uso de IA

Aplicação desktop em Python (interface gráfica PySide6) para o aluno registrar suas interações com IA, verificar as fontes que a IA citou, ligar cada fonte verificada a um trecho do próprio texto e entregar um relatório ao professor.

---

## 1. O que o programa faz

**Aluno**
1. Cria uma **pesquisa** (título e objetivo) e pode editá-la ou excluí-la enquanto estiver em andamento.
2. Registra as **interações** com a IA: ferramenta usada, pergunta e resposta.
3. Cadastra as **fontes** que a IA citou (referência e link). Toda fonte nasce como *não verificada*.
4. **Verifica** cada fonte: *verificada*, *incorreta/inventada* ou *não verificada*, com anotação. Uma fonte verificada pode ser ligada a um **trecho** do texto do aluno.
5. **Conclui** a pesquisa: ela deixa de poder ser alterada e o **relatório** é gerado e entregue ao professor. Antes disso, o aluno vê uma prévia e pode salvar o relatório em PDF.

**Professor**
- Vê a lista de relatórios das pesquisas **concluídas** (com a contagem de fontes verificadas, incorretas e pendentes) e abre o detalhe de cada uma.

**Acesso:** aluno e professor têm telas separadas. Um perfil não abre as telas do outro, nem por endereço/número direto, e um aluno nunca enxerga a pesquisa de outro aluno.

## 2. Estrutura do código

### Tecnologias

| Parte | Tecnologia |
|---|---|
| Linguagem | Python 3.11+ |
| Interface | PySide6 (Qt) |
| Banco de dados | PostgreSQL |
| Acesso ao banco | SQLAlchemy 2.x + psycopg |
| Senhas | `hashlib.scrypt` (biblioteca padrão) |
| Configuração | arquivo `.env` (python-dotenv) |
| Testes | pytest |
| Empacotamento | PyInstaller |

### Arquitetura em camadas

O código é um monolito dividido em camadas. **Cada camada só chama a que está abaixo dela**, nunca a de cima.

```
ui/           telas (PySide6)
   ↓
services/     regras de negócio
   ↓
repository/   modelos e acesso ao banco (SQLAlchemy)
   ↓
PostgreSQL
```

- **ui:** mostra as telas, lê o que o usuário digita e chama os services. Não tem regra de negócio nem acesso ao banco.
- **services:** aplicam as regras (validações, permissões, hash de senha, quem pode ver o quê). Não conhecem a interface.
- **repository:** lê e grava no banco. Não conhece regra de negócio.

### Estrutura de pastas

```
.
├── main.py                  # abre o programa
├── ui/
│   ├── app.py               # cria a aplicação e a janela
│   ├── janela_principal.py  # barra superior, troca de telas e guarda por perfil
│   ├── tela_acesso.py       # entrar / criar conta
│   ├── tela_pesquisas.py    # lista de pesquisas do aluno
│   ├── tela_pesquisa.py     # detalhe da pesquisa e suas interações
│   ├── tela_interacao.py    # interação, fontes, verificação e trechos
│   ├── tela_relatorio.py    # relatório (prévia, entregue e PDF)
│   ├── tela_professor.py    # relatórios entregues (professor)
│   ├── dialogos.py          # formulários e janela de verificação
│   ├── componentes.py       # peças reutilizáveis (botões, selos, listas)
│   ├── estilo.py            # cores, fontes e folha de estilo (QSS)
│   └── relatorio_html.py    # monta o HTML do relatório
├── services/                # usuario, pesquisa, interacao, fonte, relatorio
│   ├── erros.py             # RegraViolada
│   ├── sessao.py            # quem está logado
│   └── seguranca.py         # hash de senha
├── repository/
│   ├── models/              # uma classe SQLAlchemy por tabela
│   └── *_repository.py      # consultas de cada entidade
├── scripts/criar_tabelas.py # cria e atualiza as tabelas
├── tests/                   # testes automatizados (serviços e telas)
├── pytest.ini
└── requirements.txt
```

### Modelo de dados

| Entidade | Relação |
|---|---|
| Usuário (aluno / professor) | — |
| Turma | pertence a um professor |
| Pesquisa | pertence a um aluno; tem 1 relatório |
| Interação | pertence a uma pesquisa |
| Fonte (referência, link, status) | pertence a uma interação |
| Trecho | pertence a uma fonte |
| Relatório | 1:1 com a pesquisa |

Apagar uma pesquisa apaga em cascata suas interações, fontes, trechos e relatório.

---

## 3. Como rodar o código e os testes

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
2. Copie `.env.example` para `.env` na raiz e preencha com os dados do **seu** PostgreSQL:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=projeto1
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
```

### Criar as tabelas e abrir o programa

```bash
python -m scripts.criar_tabelas
python main.py
```

`criar_tabelas` cria as tabelas que faltam e aplica as colunas novas (por exemplo `fonte.link`), então **rode-o de novo sempre que atualizar o código**. Não há Alembic: se um modelo mudar de forma que o script não cubra, apague as tabelas e rode-o outra vez.

Na primeira vez, clique em **Criar conta** e cadastre um aluno e um professor para ver as duas áreas.

### Testes

```bash
pytest -v
```

- Cobrem as regras (services e banco) e as telas (a janela é aberta de verdade, sem aparecer no monitor, e os testes clicam e digitam nela).
- Usam o PostgreSQL de verdade, mas em um **banco separado**, `projeto1_teste`, criado automaticamente (o usuário do `.env` precisa ter permissão para criar bancos).
- O banco `projeto1` nunca é tocado pelos testes.
- Para mudar o nome do banco de teste, defina `DB_NAME_TESTE` no `.env`. O nome **precisa terminar com `_teste`**, senão os testes abortam por segurança.

### Gerar o executável (opcional)

```bash
pyinstaller --noconsole --name RegistroIA main.py
```

O programa continua lendo o `.env` (coloque-o ao lado do executável).

---

## 4. Trabalhando com Git: pull, branch e push

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

Use um nome curto que diga o que será feito, por exemplo `feature/filtros-professor` ou `fix/ordem-listagem`.

### 3. Fazer as alterações, salvar e enviar

```bash
git status                       # confere o que mudou
git add .                        # adiciona as alterações
git commit -m "descrição curta do que foi feito"
git push -u origin nome-da-branch
```

O `-u` só é necessário no primeiro push da branch; nos seguintes, basta `git push`.

### 4. Abrir o Pull Request

No GitHub, aparecerá o botão **Compare & pull request** para a branch enviada. Abra o PR para a `main`, descreva a mudança e peça revisão de outro integrante antes de fazer o merge. Antes de abrir o PR, rode `pytest -v`.
