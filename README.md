# Projeto 1 (SI 26.2) — Registro verificável do uso de IA

Aplicação desktop em Python (interface gráfica PySide6) para o aluno registrar suas interações com IA, verificar as fontes que a IA citou, ligar cada fonte verificada a um trecho do próprio texto e entregar um relatório ao professor.

---

## 1. O que o programa faz

**Aluno**
1. Entra em uma **turma** digitando o **código de entrada** que o professor gerou. A tela inicial, *Minhas turmas*, lista as turmas dele e tem o botão para digitar o código. Pode estar em várias turmas.
2. Dentro da turma (a "cadeira"), cria **pesquisas individuais** (título e objetivo) e pode editá-las ou excluí-las enquanto estiverem com ele (em andamento). A turma tem duas abas: **Individuais | Grupos**.
3. Se o professor habilitou grupos na turma, cria **grupos** (só na aba *Grupos*) e **convida** colegas da turma. Quando o primeiro convidado aceita, nasce a **pesquisa do grupo**: uma só pesquisa, que pertence ao grupo e na qual todos os integrantes registram interações e fontes. Os convites recebidos ficam no botão **Convites** da turma. Sem grupos na turma, a aba *Grupos* e o botão *Convites* ficam cinza.
4. Registra as **interações** com a IA: ferramenta usada, pergunta e resposta.
5. Cadastra as **fontes** que a IA citou (referência e link) e pode **editar** a referência e o link depois. Toda fonte nasce como *não verificada*; se uma fonte já conferida for editada, ela volta a *não verificada* (e perde os trechos), para ser conferida de novo.
6. **Verifica** cada fonte: *verificada*, *incorreta/inventada* ou *não verificada*, com anotação. Uma fonte verificada pode ser ligada a um **trecho** do texto do aluno.
7. Vê a prévia do relatório (e salva em PDF) e usa **Entregar para o professor** (qualquer integrante entrega a pesquisa do grupo). O aluno não conclui a pesquisa: quem conclui é o professor.
8. Se o professor **devolver**, a pesquisa volta a *em andamento* com a mensagem dele, visível no alto da tela. Os **comentários** do professor aparecem nas interações (só leitura).
9. Interação **confirmada** pelo professor fica fechada: para ajustar algo nela, o aluno cria uma nova interação.

**Professor**
1. **Cria turmas** (nome e se permite grupos); cada turma recebe um **código de entrada**. Pode copiar o código e **excluir** turmas (apaga tudo o que há nelas, com confirmação). A tela inicial, *Minhas turmas*, mostra alunos, pesquisas e quantas aguardam revisão.
2. Dentro da turma vê a **lista de alunos, cada um com as próprias pesquisas** (e os grupos de que participa), em vez de uma lista solta. A aba **Grupos** mostra cada grupo com os integrantes e a pesquisa; o professor pode **remover** alunos de um grupo (o último integrante não sai) e **atribuir** outros alunos da turma.
3. A **lista de pesquisas** das turmas dele tem um filtro por turma e separa em *Aguardando sua revisão*, *Em andamento* e *Concluídas*. Cada pesquisa mostra um "cheque" de entrega, a data e o botão **Relatório**, que só habilita depois da entrega.
4. Pesquisa em andamento: só acompanha (lê as interações e fontes, sem alterar nada).
5. Pesquisa entregue: **julga as fontes** de cada interação, escreve um **comentário** na interação e **confirma** a interação.
6. Ao terminar, **aceita** a pesquisa (fica *concluída* e tudo é fechado) ou **devolve** ao aluno com uma mensagem obrigatória explicando o motivo.

**Regras de grupo:** um aluno pode estar em vários grupos da mesma turma; pesquisa de grupo não é excluída pelos alunos; com a pesquisa do grupo *entregue* ou *concluída*, os integrantes não mudam (convidar, aceitar, atribuir e remover ficam bloqueados) até o professor devolvê-la. O professor só enxerga turmas e pesquisas que são dele.

**Estados de uma pesquisa:** `em_andamento` (com o aluno, inclusive a devolvida) → `entregue` (com o professor) → `concluida` (aceita). Devolver faz `entregue` voltar a `em_andamento`.

**Tutoriais:** todas as telas têm um botão pequeno **? Tutorial** (perto das ações) que explica para que a tela serve e como usá-la. Os textos ficam em `ui/tutoriais.py`.

**Acesso:** aluno e professor têm telas separadas. Um perfil não abre as telas do outro, nem por endereço/número direto. Um aluno só enxerga as próprias pesquisas e as do seu grupo; um professor só as das suas turmas.

### Requisitos (RF) implementados

| RF | O que é |
|---|---|
| 01, 02 | Cadastro e login (senha com hash) |
| 03 | Acesso separado por perfil (aluno x professor) |
| 04, 05 | Turmas com código de entrada; o aluno entra pelo código e cria pesquisas dentro da turma; grupos e convites |
| 06, 07, 08, 09 | Criar, listar, editar e excluir pesquisa (excluir só se não concluída) |
| 10 | Aluno entrega ao professor; o professor aceita (conclui e gera o relatório) ou devolve com mensagem |
| 11, 12, 13, 14 | Registrar, listar, editar e excluir interações |
| 15 | Uma interação aceita várias fontes; cada fonte guarda referência e link, editáveis pelo aluno |
| 16 | Fonte nova entra como "não verificada" |
| 17, 18 | Status da fonte (não verificada, verificada, incorreta) e anotação de correção |
| 19 | Lista mostra cada fonte com seu status atual |
| 20, 21, 22 | Relatório 1:1 com a pesquisa, completo e legível |
| 23 | Professor lista as pesquisas dos alunos e abre o relatório das entregues |
| 26, 27, 28 | Ligar fonte verificada a um trecho; trecho aparece no relatório junto da fonte |

**Ainda em aberto** (para quem quiser contribuir): RF24 (filtros do professor por aluno e status; já existe o filtro por turma) e RF25 (painel agregado).

---

## 2. Estrutura do código

### Tecnologias

| Parte | Tecnologia |
|---|---|
| Linguagem | Python 3.11+ |
| Interface | PySide6 (Qt) |
| Banco de dados | Firebase (Cloud Firestore, online) |
| Acesso ao banco | `google-cloud-firestore` (biblioteca oficial do Google) |
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
repository/   classes de dados e acesso ao banco
   ↓
Firebase (Cloud Firestore, na internet)
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
│   ├── tela_turmas.py       # aluno: Minhas turmas e entrada por código
│   ├── tela_pesquisas.py    # aluno: uma turma (abas Individuais | Grupos, convites)
│   ├── tela_pesquisa.py     # detalhe da pesquisa e suas interações
│   ├── tela_interacao.py    # interação, fontes, verificação e trechos
│   ├── tela_relatorio.py    # relatório (prévia, entregue e PDF)
│   ├── tela_turmas_professor.py  # professor: Minhas turmas (criar, código, excluir)
│   ├── tela_turma_professor.py   # professor: alunos e suas pesquisas, grupos (remover/atribuir)
│   ├── tela_professor.py    # lista de pesquisas das turmas, com filtro por turma (professor)
│   ├── linhas.py            # linha de pesquisa das telas do professor
│   ├── tela_revisao.py      # pesquisa de um aluno: acompanhar, aceitar ou devolver (professor)
│   ├── tela_revisao_interacao.py  # julgar fontes, comentar e confirmar (professor)
│   ├── cartao_fonte.py      # cartão de fonte usado pelas telas do aluno e do professor
│   ├── dialogos.py          # formulários, verificação de fonte e tutorial
│   ├── tutoriais.py         # textos dos botões "? Tutorial"
│   ├── componentes.py       # peças reutilizáveis (botões, selos, listas, recados)
│   ├── estilo.py            # cores, fontes e folha de estilo (QSS)
│   └── relatorio_html.py    # monta o HTML do relatório
├── services/                # usuario, turma, grupo, pesquisa, interacao, fonte, relatorio, revisao
│   ├── erros.py             # RegraViolada
│   ├── sessao.py            # quem está logado
│   └── seguranca.py         # hash de senha
├── repository/
│   ├── models/              # uma classe por coleção (Usuario, Turma, Pesquisa...)
│   ├── armazenamento.py     # FirestoreStore (nuvem) e MemoryStore (testes); lotes e unicidade
│   ├── carga.py             # monta objetos com o que a tela precisa (no lugar dos JOINs)
│   ├── cascata.py           # exclusão em cascata (turma, pesquisa, interação...)
│   └── *_repository.py      # consultas de cada entidade
├── scripts/
│   ├── verificar_firebase.py  # confere a conexão com o Firebase
│   └── popular_exemplo.py     # dados de exemplo
├── firestore.rules          # regras do Firestore (bloqueiam acesso direto de fora)
├── firebase.json            # configuração do Firebase CLI / emulador (opcional)
├── tests/                   # testes automatizados (serviços, telas e armazenamento)
├── pytest.ini
└── requirements.txt
```

### Como uma ação percorre as camadas

Exemplo, o professor devolve uma pesquisa:

1. O professor clica em **Devolver ao aluno**. A tela abre um formulário pedindo a mensagem.
2. A **tela** chama `RevisaoService.devolver(...)`.
3. O **service** confere que quem está logado é professor, que a pesquisa está *entregue* e que a mensagem não está vazia.
4. O **repository** grava a mensagem e a data, muda o status para *em andamento* e limpa a data de entrega, numa só gravação no Firestore.
5. Se alguma regra for violada, o service levanta `RegraViolada` e a tela mostra a mensagem dentro do formulário, sem fechar o programa.

### Modelo de dados

| Entidade | Relação |
|---|---|
| Usuário (aluno / professor) | — |
| Turma (nome, código de entrada, permite grupos) | pertence a um professor |
| Matrícula | liga um aluno a uma turma (um aluno pode ter várias) |
| Grupo (nome, título e objetivo da pesquisa) | pertence a uma turma; tem integrantes (`grupo_aluno`) e convites (`convite_grupo`); tem 1 pesquisa depois do 1º aceite |
| Pesquisa (status, datas de entrega e conclusão, mensagem de devolução) | pertence a uma turma e a **um aluno ou a um grupo** (nunca aos dois); tem 1 relatório |
| Interação (comentário do professor, confirmada) | pertence a uma pesquisa |
| Fonte (referência, link, status, julgada pelo professor) | pertence a uma interação |
| Trecho | pertence a uma fonte |
| Relatório | 1:1 com a pesquisa |

Cada linha da tabela é uma **coleção** do Firestore (`usuarios`, `turmas`, `matriculas`, `grupos`, `grupo_alunos`, `convites`, `pesquisas`, `interacoes`, `fontes`, `trechos`, `relatorios`) e cada registro é um **documento**. O Firestore não tem chave estrangeira, UNIQUE nem JOIN, então:

- **Unicidade:** e-mail e código de turma têm um documento-guardião na coleção `unicos`; matrícula, integrante e convite usam o id `"A_B"`; a pesquisa do grupo usa o id `"grupo-<id>"`; o relatório usa o id da pesquisa. Criar de novo um que já existe falha (`Duplicado`).
- **Cascata:** apagar uma pesquisa apaga suas interações, fontes, trechos e relatório; apagar uma turma apaga também matrículas, grupos, convites e todas as pesquisas dela. Isso é feito em `repository/cascata.py`, num lote (até 500 operações por lote do Firestore; passando disso a exclusão é gravada em pedaços).
- **Atomicidade:** ações que mexem em vários documentos (aceitar a pesquisa, aceitar convite e criar a pesquisa do grupo, verificar fonte com trecho...) usam um *lote*, que o Firestore grava tudo ou nada.
- **Ordem e filtros:** só consultas por igualdade são feitas no Firestore e a ordenação é feita no programa, então **não é preciso criar índices**.

---

## 3. Como rodar o código e os testes

**Requisitos:** Python 3.11+, internet e uma conta Google (para o Firebase).

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

# 4. configurar o Firebase (seção abaixo): criar o projeto, o banco e baixar a chave JSON,
#    depois copiar .env.example para .env e preencher FIREBASE_CREDENCIAIS

# 5. conferir a conexão e abrir o programa
python -m scripts.verificar_firebase
python main.py
```

No Linux/macOS, ative com `source .venv/bin/activate`.

### Firebase: criar o banco (uma vez por projeto)

Basta **uma pessoa do grupo** fazer os passos 1 a 5; todos os integrantes usam o mesmo banco (por isso todos enxergam os mesmos dados).

1. **Criar o projeto.** Acesse <https://console.firebase.google.com>, entre com uma conta Google e clique em **Criar um projeto** (ou *Adicionar projeto*). Dê um nome (por exemplo `projeto1-ia`), pode **desativar o Google Analytics** (não é usado) e conclua.
2. **Criar o banco Firestore.** No menu lateral, **Criação** (*Build*) → **Firestore Database** → **Criar banco de dados**.
   - *ID do banco:* deixe `(default)`.
   - *Local:* escolha uma região perto de você, por exemplo `southamerica-east1` (São Paulo). **Não dá para mudar depois.**
   - *Regras de segurança:* escolha **Iniciar no modo de produção** (bloqueia todo acesso direto, que é o que queremos; o programa entra pela conta de serviço, que não é barrada por essas regras).
   - Clique em **Criar** e espere o banco aparecer. O plano gratuito (Spark) é suficiente para o projeto; as cotas diárias aparecem na aba **Uso** do Firestore.
3. **Conferir as regras (opcional, recomendado).** Na aba **Regras** do Firestore, o conteúdo deve ser igual ao do arquivo `firestore.rules` deste repositório (nega todo acesso direto). Se for diferente, cole o conteúdo do arquivo e clique em **Publicar**.
4. **Gerar a chave de acesso do programa.** Clique na engrenagem ⚙ ao lado de *Visão geral do projeto* → **Configurações do projeto** → aba **Contas de serviço** → **Gerar nova chave privada** → **Gerar chave**. O navegador baixa um arquivo `.json`.
5. **Guardar a chave com cuidado.** Mova o arquivo para uma pasta **fora do repositório**, por exemplo `C:\Users\seu_usuario\firebase\projeto1-chave.json`. Quem tem esse arquivo tem **acesso total ao banco**: não coloque no git, no zip do projeto nem em grupo de mensagens. (O `.gitignore` já ignora nomes comuns, mas não confie só nele.)
6. **Configurar o `.env`.** Copie `.env.example` para `.env` na raiz do projeto e preencha o caminho da chave:

   ```
   FIREBASE_CREDENCIAIS=C:/Users/seu_usuario/firebase/projeto1-chave.json
   ```

   `FIREBASE_PROJETO` é opcional (o id do projeto é lido de dentro do JSON). O `.env` nunca deve ir para o GitHub (já está no `.gitignore`).
7. **Conferir a conexão:**

   ```bash
   python -m scripts.verificar_firebase
   ```

   Ele grava, lê e apaga um documento de teste. Se aparecer "Tudo certo", está funcionando. Erros comuns: `FIREBASE_CREDENCIAIS` com caminho errado (a mensagem diz isso), *"Cloud Firestore API has not been used"* ou *"database (default) does not exist"* (o passo 2 não foi feito ou ainda está terminando, espere um minuto), *"Permission denied"* (a chave é de outro projeto).

**Para os outros integrantes do grupo:** peça ao dono do projeto em **Configurações do projeto → Usuários e permissões → Adicionar membro** (papel *Editor*) e cada um gera a **própria chave** no passo 4, ou o dono compartilha a mesma chave por um meio seguro. Depois é só preencher o próprio `.env`.

**Não há tabelas para criar nem migração:** o Firestore cria as coleções sozinho na primeira gravação. Para ver os dados, abra **Firestore Database → Dados** no console. Os dados que estavam no PostgreSQL **não** são levados para o Firebase (o banco começa vazio).

### Abrir o programa

```bash
python main.py
```

Na primeira vez, clique em **Criar conta** e cadastre um aluno e um professor para ver as duas áreas. Para testar o fluxo completo: com o professor, crie uma turma e copie o código; com o aluno, entre na turma pelo código, crie uma pesquisa, registre uma interação com fontes e use **Entregar para o professor**; depois saia, entre como professor e revise.

### Dados de exemplo (para testar sem cadastrar tudo)

```bash
python -m scripts.popular_exemplo             # cria professores, alunos, turmas, grupos, convites e pesquisas
python -m scripts.popular_exemplo --recriar   # apaga os dados de exemplo e cria de novo
python -m scripts.popular_exemplo --limpar    # só apaga os dados de exemplo
```

Todos os e-mails são `@exemplo.com` e a senha é `senha123` (por exemplo `marina@exemplo.com`, professora, e `ana@exemplo.com`, aluna). O script mostra no final quem tem o quê: pesquisa em andamento, entregue, concluída, devolvida, grupo com convite pendente etc. A aluna `fabi@exemplo.com` fica sem turma para testar a entrada pelo código `PROJ01`. Só os usuários `@exemplo.com` são apagados; o que você cadastrou não é tocado. Como o banco é compartilhado, rode `--recriar` só combinando com o grupo.

### Testes

```bash
pytest -v
```

- Cobrem as regras (services e repositórios) e as telas (a janela é aberta de verdade, sem aparecer no monitor, e os testes clicam e digitam nela).
- **Não usam o Firebase:** cada teste roda sobre um banco em memória (`MemoryStore`) novo. Não precisam de internet nem de chave, e **nunca tocam nos dados reais**.
- `tests/test_armazenamento_contrato.py` roda as mesmas verificações no `MemoryStore` e no `FirestoreStore` (este contra um cliente Firestore falso que imita os limites reais: 500 operações por lote, 30 valores no filtro `in`, erros de "já existe"). Se você tiver Java e o `firebase-tools`, dá para rodar também contra o **emulador oficial** do Firestore: `firebase emulators:start --only firestore` em um terminal e, em outro, `FIRESTORE_EMULATOR_HOST=localhost:8080 pytest tests/test_armazenamento_contrato.py`.

Comandos úteis:

```bash
pytest tests/test_ui.py -v             # só as telas
pytest -k "fonte" -v                   # testes cujo nome contém "fonte"
pytest -x                              # para no primeiro erro
pytest --collect-only -q               # lista os testes sem rodar
```

Se o comando `pytest` não for reconhecido, use `python -m pytest -v`.

### Gerar o executável (opcional)

```bash
pyinstaller --noconsole --name RegistroIA main.py
```

O programa continua lendo o `.env` (coloque-o ao lado do executável) e precisa do arquivo JSON da chave do Firebase no caminho indicado nele. Não inclua a chave dentro da pasta distribuída para outras pessoas.

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

### Convenções do código

- Mantenha a regra das camadas: a `ui` nunca acessa o banco; só chama os `services`.
- Regra de negócio violada vira `raise RegraViolada("mensagem para o usuário")` no service; a tela só mostra a mensagem.
- Toda funcionalidade nova leva testes em `tests/`.
