# Projeto 1 (SI 26.2) — Registro verificável do uso de IA

Aplicação web (API em Python + interface em React) para o aluno registrar suas interações com IA, verificar as fontes que a IA citou, ligar cada fonte verificada a um trecho do próprio texto e entregar um relatório ao professor.

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

**Tutoriais:** todas as telas têm um botão pequeno **? Tutorial** (perto das ações) que explica para que a tela serve e como usá-la. Os textos ficam em `frontend/src/tutoriais.json`.

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
| Interface (front-end) | React 18 + TypeScript, compilado com Vite |
| API (back-end) | Python 3.11+ com FastAPI (`api/`), servida pelo Uvicorn |
| Regras de negócio | Python puro (`services/`) |
| Banco de dados | Firebase (Cloud Firestore, online) |
| Acesso ao banco | `google-cloud-firestore` (biblioteca oficial do Google) |
| Senhas | `hashlib.scrypt` (biblioteca padrão) |
| Configuração | arquivo `.env` (python-dotenv) |
| Testes | pytest (regras, API e armazenamento) |

### Arquitetura em camadas

O back-end é um monolito dividido em camadas. **Cada camada só chama a que está abaixo dela**, nunca a de cima. O front-end é um aplicativo separado que só conversa com a API por HTTP/JSON.

```
frontend/     telas em React (navegador)
   ↓  HTTP/JSON
api/          rotas FastAPI: só traduzem HTTP para chamadas de service
   ↓
services/     regras de negócio
   ↓
repository/   classes de dados e acesso ao banco
   ↓
Firebase (Cloud Firestore, na internet)
```

- **frontend:** mostra as telas, lê o que o usuário digita e chama a API. Não tem regra de negócio: as mensagens de erro vêm prontas do servidor.
- **api:** cada rota autentica o usuário (token), chama **um** service e devolve JSON. Não decide nada sozinha.
- **services:** aplicam as regras (validações, permissões, hash de senha, quem pode ver o quê). Não conhecem HTTP nem interface.
- **repository:** lê e grava no banco. Não conhece regra de negócio.

### Estrutura de pastas

```
.
├── main.py                  # abre o programa (servidor + navegador)
├── api/
│   ├── main.py              # todas as rotas (/api/...); também serve o front compilado
│   ├── sessoes.py           # token de login e o usuário de cada requisição
│   └── serializadores.py    # objetos dos services -> JSON
├── frontend/
│   ├── package.json, vite.config.ts, index.html
│   └── src/
│       ├── main.tsx, App.tsx      # rotas das telas e proteção por perfil
│       ├── api.ts, tipos.ts       # chamadas à API e tipos
│       ├── ui.tsx                 # menu lateral, botões, selos, diálogos, avisos
│       ├── auth.tsx               # sessão do usuário no navegador
│       ├── estilo.css             # visual (cores, tipografia, tema claro/escuro)
│       ├── tutoriais.json         # textos dos botões "Tutorial"
│       └── paginas/               # Acesso, AlunoTurmas, AlunoTurma, AlunoPesquisa, AlunoInteracao,
│                                  # ProfTurmas, ProfTurma, ProfPesquisas, ProfRevisao,
│                                  # ProfInteracao, Relatorio (+ fonte.tsx e linhas.tsx compartilhados)
├── services/                # usuario, turma, grupo, pesquisa, interacao, fonte, relatorio, revisao
│   ├── erros.py             # RegraViolada
│   ├── sessao.py            # quem está logado
│   └── seguranca.py         # hash de senha
├── repository/
│   ├── models/              # uma classe por coleção (Usuario, Turma, Pesquisa...)
│   ├── armazenamento.py     # FirestoreStore (nuvem) e MemoryStore (testes/demo); lotes e unicidade
│   ├── carga.py             # monta objetos com o que a tela precisa (no lugar dos JOINs)
│   ├── cascata.py           # exclusão em cascata (turma, pesquisa, interação...)
│   └── *_repository.py      # consultas de cada entidade
├── scripts/
│   ├── verificar_firebase.py  # confere a conexão com o Firebase
│   ├── popular_exemplo.py     # dados de exemplo no Firebase
│   └── demo.py                # modo demonstração: sem Firebase, dados só na memória
├── firestore.rules          # regras do Firestore (bloqueiam acesso direto de fora)
├── firebase.json            # configuração do Firebase CLI / emulador (opcional)
├── tests/                   # testes automatizados (services, API e armazenamento)
├── pytest.ini
└── requirements.txt
```

### Como uma ação percorre as camadas

Exemplo, o professor devolve uma pesquisa:

1. O professor clica em **Devolver ao aluno**. A tela abre um formulário pedindo a mensagem.
2. O **front** envia `POST /api/professor/pesquisas/{id}/devolucao` e a **rota** chama `RevisaoService.devolver(...)`.
3. O **service** confere que quem está logado é professor, que a pesquisa está *entregue* e que a mensagem não está vazia.
4. O **repository** grava a mensagem e a data, muda o status para *em andamento* e limpa a data de entrega, numa só gravação no Firestore.
5. Se alguma regra for violada, o service levanta `RegraViolada`, a API responde com erro 400 e a mensagem, e o front a mostra dentro do formulário, sem fechar nada.

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

**Requisitos:** Python 3.11+, **Node.js 20+** (para compilar o front-end), internet e uma conta Google (para o Firebase).

### Ver funcionando em 2 minutos (sem Firebase)

O modo demonstração usa um banco só na memória, já com dados de exemplo. Nada é gravado e tudo some ao fechar.

```bash
# 1. dependências do servidor (Windows; no Linux/macOS use: source .venv/bin/activate)
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 2. compilar o front-end (uma vez, e de novo quando mudar algo em frontend/)
cd frontend
npm install
npm run build
cd ..

# 3. subir a demonstração e abrir http://127.0.0.1:8000
python -m scripts.demo
```

Entre com `ana@exemplo.com` (aluna) ou `marina@exemplo.com` (professora), senha `senha123`.

### Rodar do zero com o Firebase

```bash
# 1. clonar e entrar na pasta
git clone <url-do-repositorio>
cd <pasta-do-projeto>

# 2. ambiente virtual e dependências do servidor (Windows)
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 3. configurar o Firebase (seção abaixo): criar o projeto, o banco e baixar a chave JSON,
#    depois copiar .env.example para .env e preencher FIREBASE_CREDENCIAIS

# 4. conferir a conexão com o Firebase
python -m scripts.verificar_firebase

# 5. compilar o front-end (uma vez)
cd frontend
npm install
npm run build
cd ..

# 6. abrir o programa (sobe o servidor e abre o navegador em http://127.0.0.1:8000)
python main.py
```

No Linux/macOS, ative o ambiente com `source .venv/bin/activate`.

### Desenvolvendo o front-end (recarga automática)

Use dois terminais:

```bash
# terminal 1: o servidor Python (porta 8000); para dados de teste sem Firebase use: python -m scripts.demo
python -m uvicorn api.main:app --reload --port 8000

# terminal 2: o front com recarga automática (http://localhost:5173)
cd frontend
npm run dev
```

O Vite repassa tudo que começa com `/api` para o servidor Python. A documentação interativa da API fica em <http://127.0.0.1:8000/docs>.

### Firebase: criar o banco (uma vez por projeto)

Basta **uma pessoa do grupo** fazer os passos 1 a 6; todos os integrantes usam o mesmo banco (por isso todos enxergam os mesmos dados).

1. **Criar o projeto.** Acesse <https://console.firebase.google.com>, entre com uma conta Google e clique em **Criar um projeto** (ou *Adicionar projeto*). Dê um nome (por exemplo `projeto1-ia`), pode **desativar o Google Analytics** (não é usado) e conclua.
2. **Criar o banco Firestore.** No menu lateral, **Criação** (*Build*) → **Firestore Database** → **Criar banco de dados**.
   - *ID do banco:* deixe `(default)`.
   - *Local:* escolha uma região perto de você, por exemplo `southamerica-east1` (São Paulo). **Não dá para mudar depois.**
   - *Regras de segurança:* escolha **Iniciar no modo de produção** (bloqueia todo acesso direto, que é o que queremos; o programa entra pela conta de serviço, que não é barrada por essas regras).
   - Clique em **Criar** e espere o banco aparecer. O plano gratuito (Spark) é suficiente para o projeto; as cotas diárias aparecem na aba **Uso** do Firestore.
3. **Conferir as regras (opcional, recomendado).** Na aba **Regras** do Firestore, o conteúdo deve ser igual ao do arquivo `firestore.rules` deste repositório (nega todo acesso direto). Se for diferente, cole o conteúdo do arquivo e clique em **Publicar**.
4. **Gerar a chave de acesso do programa.** Clique na engrenagem ⚙ ao lado de *Visão geral do projeto* → **Configurações do projeto** → aba **Contas de serviço** → **Gerar nova chave privada** → **Gerar chave**. O navegador baixa um arquivo `.json`.
5. **Guardar a chave com cuidado.** Mova o arquivo para uma pasta **fora do repositório**, por exemplo `C:\Users\seu_usuario\firebase\projeto1-chave.json`. Quem tem esse arquivo tem **acesso total ao banco**: não coloque no git, no zip do projeto nem em grupo de mensagens. (O `.gitignore` já ignora nomes comuns, mas não confie só nele.)
6. **Dar permissão à conta de serviço.** A chave gerada no passo 4 pertence a uma conta de serviço (o e-mail dela está no campo `client_email` do `.json`, algo como `firebase-adminsdk-fbsvc@SEU-PROJETO.iam.gserviceaccount.com`). Se ela não tiver o papel de acesso ao Firestore, o programa recebe `PermissionDenied: 403 Missing or insufficient permissions`. Para dar o papel:
   1. Abra <https://console.cloud.google.com/iam-admin/iam> e escolha o seu projeto no seletor do topo.
   2. Clique em **Permitir acesso** (*Conceder acesso*), cole o e-mail da conta de serviço em **Novos principais**, escolha o papel **Cloud Datastore User** (*Usuário do Cloud Datastore*) e **Salvar**.
   3. A conta de serviço só aparece na lista do IAM se a caixa **Incluir concessões de papel fornecidas pelo Google** estiver marcada. Se ela já tiver o papel, este passo não é necessário.
   4. Espere 1 ou 2 minutos para a permissão valer.
7. **Configurar o `.env`.** Copie `.env.example` para `.env` na raiz do projeto e preencha o caminho da chave:

   ```
   FIREBASE_CREDENCIAIS=C:/Users/seu_usuario/firebase/projeto1-chave.json
   ```

   `FIREBASE_PROJETO` é opcional (o id do projeto é lido de dentro do JSON). O `.env` nunca deve ir para o GitHub (já está no `.gitignore`).
8. **Instalar as dependências e conferir a conexão** (com o ambiente virtual ativo):

   ```bash
   pip install -r requirements.txt
   python -m scripts.verificar_firebase
   ```

   Ele grava, lê e apaga um documento de teste. Se aparecer "Tudo certo", está funcionando.

   **Erros comuns:**

   | Mensagem | Causa e solução |
   |---|---|
   | `ModuleNotFoundError: No module named 'google'` | As dependências não foram instaladas no ambiente virtual ativo. Rode `pip install -r requirements.txt` (ou `python -m pip install -r requirements.txt`). |
   | "Não encontrei o arquivo de credenciais..." | O caminho em `FIREBASE_CREDENCIAIS` está errado, ou o `.env` **não foi salvo** depois de editar (o caminho mostrado na mensagem é o que o programa leu). Confira também se há uma variável de ambiente com o mesmo nome, que tem prioridade sobre o `.env`. |
   | "O Firebase não está configurado" | `FIREBASE_CREDENCIAIS` está vazio no `.env`, ou o arquivo `.env` não existe (só existe o `.env.example`). |
   | `PermissionDenied: 403 Missing or insufficient permissions` | A conta de serviço não tem o papel do passo 6 (**Cloud Datastore User**), ou a chave é de outro projeto (confira `project_id` no `.json` e `FIREBASE_PROJETO` no `.env`). |
   | *"Cloud Firestore API has not been used"* ou *"database (default) does not exist"* | O passo 2 não foi feito, o banco não tem o ID `(default)` ou ainda está sendo criado (espere um minuto). |

**Para os outros integrantes do grupo:** peça ao dono do projeto em **Configurações do projeto → Usuários e permissões → Adicionar membro** (papel *Editor*) e cada um gera a **própria chave** no passo 4, ou o dono compartilha a mesma chave por um meio seguro. Depois é só preencher o próprio `.env`.

**Não há tabelas para criar nem migração:** o Firestore cria as coleções sozinho na primeira gravação. Para ver os dados, abra **Firestore Database → Dados** no console. Os dados que estavam no PostgreSQL **não** são levados para o Firebase (o banco começa vazio).

### Abrir o programa

```bash
python main.py
```

(É preciso ter compilado o front antes: `cd frontend && npm install && npm run build`.) Na primeira vez, clique em **Criar conta** e cadastre um aluno e um professor para ver as duas áreas. Para testar o fluxo completo: com o professor, crie uma turma e copie o código; com o aluno, entre na turma pelo código, crie uma pesquisa, registre uma interação com fontes e use **Entregar para o professor**; depois saia, entre como professor e revise.

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

- Cobrem as regras (services e repositórios) e a **API** (`tests/test_api.py` faz o mesmo fluxo que o front: cadastro, login, turma, pesquisa, interação, fontes, entrega, revisão, grupos e convites, incluindo permissões por perfil).
- **Não usam o Firebase:** cada teste roda sobre um banco em memória (`MemoryStore`) novo. Não precisam de internet nem de chave, e **nunca tocam nos dados reais**.
- `tests/test_armazenamento_contrato.py` roda as mesmas verificações no `MemoryStore` e no `FirestoreStore` (este contra um cliente Firestore falso que imita os limites reais: 500 operações por lote, 30 valores no filtro `in`, erros de "já existe"). Se você tiver Java e o `firebase-tools`, dá para rodar também contra o **emulador oficial** do Firestore: `firebase emulators:start --only firestore` em um terminal e, em outro, `FIRESTORE_EMULATOR_HOST=localhost:8080 pytest tests/test_armazenamento_contrato.py`.

Comandos úteis:

```bash
pytest tests/test_api.py -v            # só a API
pytest -k "fonte" -v                   # testes cujo nome contém "fonte"
pytest -x                              # para no primeiro erro
pytest --collect-only -q               # lista os testes sem rodar
```

Se o comando `pytest` não for reconhecido, use `python -m pytest -v`.

### Publicar para a turma usar (opcional)

O servidor é um programa Python comum: em qualquer máquina com Python, `python main.py` (ou `python -m uvicorn api.main:app --host 0.0.0.0 --port 8000`) serve o front compilado e a API juntos. Os logins ficam guardados na memória do servidor (valem 12 horas e somem se ele reiniciar). Se for expor na internet, coloque-o atrás de HTTPS.

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

No GitHub, aparecerá o botão **Compare & pull request** para a branch enviada. Abra o PR para a `main`, descreva a mudança e peça revisão de outro integrante antes de fazer o merge. Antes de abrir o PR, rode `pytest -v` e `cd frontend && npm run build` (o build confere os tipos do TypeScript).

### Convenções do código

- Mantenha a regra das camadas: o front só fala com a API; a API só chama `services`; os `services` só usam os `repository`.
- Regra de negócio violada vira `raise RegraViolada("mensagem para o usuário")` no service; a API devolve 400 com essa mensagem e o front só a mostra.
- Toda funcionalidade nova leva testes em `tests/`.
