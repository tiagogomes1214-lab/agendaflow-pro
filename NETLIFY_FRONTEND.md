# AgendaFlow - Deploy do frontend no Netlify

Use o repositorio `tiagogomes1214-lab/agendaflow-pro` e a branch de producao `netlify-frontend`.
O arquivo `netlify.toml` na raiz ja configura:

- Base directory: `frontend`
- Build command: `npm run build`
- Publish directory: `.next` (relativo a `frontend`)
- Node.js: 22

O Next.js usa o adaptador oficial do Netlify (automatico).
A configuracao `output: "standalone"` foi removida **somente desta branch**.

Configure a variavel no painel Netlify em **Project configuration > Environment variables**:
`API_INTERNAL_URL=https://agendaflow.discloud.dev`
Habilite disponibilidade para **Functions** alem de Builds, se o painel oferecer escolha de scopes.
Depois execute **Trigger deploy > Deploy project**. Nao salve senhas no GitHub.

O backend FastAPI e PostgreSQL permanecem na Discloud/Supabase sem alteracoes.
Para testar a integracao acesse `https://SEU-SITE.netlify.app/api/health`; resposta esperada `{"status":"ok","version":"2.0.0"}`.

Caso exista um projeto Netlify anterior apontando para a branch `main`, altere sua Production branch para `netlify-frontend`, ou conecte um novo projeto com esta branch. Nao utilize os scripts standalone da branch Discloud.
