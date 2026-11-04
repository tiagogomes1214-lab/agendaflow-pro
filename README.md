# AgendaFlow Pro 2.0 — Full Stack de agendamentos

**Sistema web personalizável** com Next.js 16, TypeScript, FastAPI, SQLAlchemy, PostgreSQL 16, fila de notificações e Docker Compose. O tema foi redesenhado para um estilo SaaS minimalista, com painel escuro, agenda limpa e interface responsiva.

## Estado atual do projeto no GitHub

Este repositório apresenta um **projeto de portfólio em evolução**, não um SaaS pronto para uso comercial.
As páginas e rotas do calendário, do painel, da agenda pública e da área do cliente estão implementadas.
Os testes automatizados atuais cobrem cinco cenários de backend; ainda faltam testes end-to-end em navegador e revisão de segurança.
A integração de notificações exige credenciais externas e o deploy na VPS é apenas um exemplo de configuração.

Um workflow do GitHub Actions executa os testes Python, a checagem TypeScript e o build do frontend após cada push.
A presença do workflow **não significa** que o build já foi aprovado; verifique o resultado na aba *Actions* do repositório.

**Não envie** `.env`, senhas, tokens, backups PostgreSQL ou dados pessoais reais ao GitHub.
O `.gitignore` contém exclusões para esses arquivos, mas sempre revise `git status` antes do push.

## Atualizar o AgendaFlow que já funciona no Windows 11

**Não apague a pasta anterior, nem o volume PostgreSQL. Faça backup antes de atualizar.**

### Passo 1 — Backup da versão antiga

Na pasta antiga, abra PowerShell e execute:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\backup.ps1
```

A versão antiga não possui esse script. Se você não colocou o `backup.ps1` novo na pasta antiga, use manualmente:

```powershell
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/agendaflow.backup'
docker compose cp db:/tmp/agendaflow.backup .\agendaflow-antes-v2.backup
```

Se não houver uma cópia de backup válida, **não prossiga com uma atualização de dados importantes**.

### Passo 2 — Atualizar os arquivos mantendo o banco

1. Extraia o novo ZIP. A pasta chama-se `agendaflow_pro`.
2. **Copie o `.env` da pasta antiga para a raiz de `agendaflow_pro`**. É um arquivo oculto; não o envie ao GitHub nem a outras pessoas. Isso conserva as mesmas senhas e configuração do banco.
3. Se já abriu a pasta antiga no Docker Compose, há duas situações:
   - **Forma recomendada:** mantenha o projeto antigo no mesmo diretório e substitua somente os arquivos dele pelos arquivos do ZIP, sem excluir o `.env`. Dessa forma o nome do projeto Docker e o volume continuam iguais.
   - **Se quiser usar uma pasta nova:** use `docker compose -p NOME_DO_PROJETO_ANTIGO ...`, identificando antes o nome exato em `docker compose ls`. Não adivinhe o nome, pois um nome diferente cria outro volume vazio.
4. Na raiz da pasta atualizada:

```powershell
docker compose up --build -d
```

5. Depois:

```powershell
docker compose ps
docker compose logs --tail=100 backend
docker compose logs --tail=100 frontend
```

O backend faz uma migração **aditiva** para incluir `color` em `services` e `price_cents` em `appointments`, cria novas tabelas e preserva a reserva antiga. **Não execute `docker compose down -v`** — `-v` remove o volume de dados.

> Se o Docker já estava rodando a versão anterior, pode ser necessário executar `docker compose down` **sem** `-v` antes do `up`; não exclua volumes.

## Primeira instalação (sem banco anterior)

Abra PowerShell na raiz do projeto e execute:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
docker compose up --build -d
```

Salve a senha exibida no terminal. Usuário padrão: `admin@exemplo.com`.

## Endereços locais

- Site público: **http://localhost:3000**
- Administrador: **http://localhost:3000/admin**
- Minha reserva: **http://localhost:3000/minha-reserva** (somente pelo link secreto fornecido no ato da reserva)
- API FastAPI: **http://localhost:8000/docs**
- Saúde: **http://localhost:8000/health**

## Funcionalidades disponíveis

| Módulo | O que já foi implementado |
|---|---|
| Reservas | Serviços, profissionais, preços, escolha de data/horário e bloqueio contra duplicidade |
| Calendário | Visualizações dia/semana/mês, filtragem por profissional/status, cards por serviço e drawer de detalhes |
| Administração | Login, novos agendamentos, concluir/cancelar, criar/editar/arquivar serviços e profissionais |
| Expediente | Horários globais e individuais, dia fechado, intervalos para almoço |
| Bloqueios | Folgas/feriados de toda a empresa ou de um profissional sem sobrepor reservas existentes |
| Área do cliente | Link único pós-reserva, consulta, cancelamento e reagendamento até 2h antes |
| Notificações | Fila de confirmação, lembrete e alteração; envio via SMTP e Meta WhatsApp Cloud API **somente se configurados** |
| Relatórios | Agendamentos, cancelamentos, serviços mais realizados e estimativa de receita dos serviços concluídos |
| Deploy | Exemplo de proxy HTTPS na VPS com Caddy em `deploy/`, requer configuração e servidor externo |

### Regras e limitações importantes

- Valores exibidos como receita são **estimativas baseadas em serviços concluídos**, não pagamentos confirmados.
- Agendamentos anteriores mantêm histórico, inclusive quando serviço/profissional é arquivado. Arquivar não cancela reservas existentes.
- Bloqueios novos são recusados se atingirem horários já confirmados. Alterar expediente não cancela reservas existentes.
- Os links pessoais são exibidos apenas quando a reserva é criada; guarde ou copie o link. Nunca compartilhe o token com terceiros.
- Fuso do calendário: **America/Sao_Paulo**. O frontend usa São Paulo como padrão nesta versão.
- O dashboard carrega até **2000 agendamentos recentes** para visualização. Para alto volume, implementar paginação e consultas agregadas.
- O backend utiliza migração aditiva para os dois campos novos. Para mudanças futuras em produção, migrar para Alembic com scripts versionados.
- Sem SMTP/WhatsApp configurados, o worker marca notificações como `skipped` (`Não configurado`). Não existe envio real.

## Configurar as notificações (opcional)

No seu `.env`, adicione:

```env
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=
WA_TOKEN=
WA_PHONE_NUMBER_ID=
WA_API_VERSION=v26.0
WA_TEMPLATE_CONFIRMATION=
WA_TEMPLATE_REMINDER=
WA_TEMPLATE_RESCHEDULE=
WA_TEMPLATE_CANCELLATION=
```

**Importante:** para WhatsApp Business, é preciso conta empresarial apta, token válido, número habilitado e templates de mensagens aprovados com três parâmetros em sequência (nome, serviço, dia/hora). Há custos e condições do provedor. Não envie mensagens sem consentimento dos destinatários. Para notificações por e-mail é necessário SMTP com TLS ou SSL.

Depois execute `docker compose up -d --force-recreate backend worker` para carregar novas variáveis. O worker verifica a fila aproximadamente a cada 30 segundos.

## Testes

Dentro do Docker:

```powershell
docker compose exec backend pytest -q
```

Sem Docker (Python com dependências instaladas):

```powershell
cd backend
$env:DATABASE_URL = 'sqlite+pysqlite:///:memory:'
pytest -q
```

## Estrutura

```text
agendaflow_pro/
├── docker-compose.yml
├── .env.example
├── scripts/
│   ├── setup.ps1
│   └── backup.ps1
├── backend/app/
│   ├── main.py       # rotas, autenticação, regras
│   ├── models.py     # tabelas do banco
│   ├── schemas.py    # validações
│   ├── scheduling.py # algoritmo de horários
│   ├── worker.py     # fila de notificação SMTP/WhatsApp
│   ├── database.py
│   └── security.py
├── frontend/
│   ├── app/page.tsx               # reserva pública
│   ├── app/admin/page.tsx         # painel administrativo e calendário
│   ├── app/minha-reserva/page.tsx # gestão pelo cliente
│   ├── app/globals.css            # identidade visual
│   └── lib/api.ts                 # tipos, data/hora, cliente HTTP
├── deploy/                        # exemplo VPS/HTTPS
└── GUIA_DE_ESTUDOS.md             # plano para aprender cada módulo
```

## Segurança e produção

**Este projeto é uma versão avançada de portfólio, NÃO deve ser publicado para clientes reais sem validação e endurecimento de segurança.** Ainda faltam limitação de tentativas de login, anti-spam/rate limiting, políticas de privacidade/LGPD, logs de auditoria, teste de restauração de backup, migrações versionadas, testes end-to-end em navegador e gestão robusta de usuários e permissões. A tela de administrador usa JWT em `sessionStorage` (adequado para protótipo controlado, mas requer avaliação de riscos de XSS em produção).

Nunca envie `.env`, tokens ou cópia do banco com dados pessoais ao GitHub. Consulte `deploy/README.md` antes de disponibilizar o sistema publicamente.
