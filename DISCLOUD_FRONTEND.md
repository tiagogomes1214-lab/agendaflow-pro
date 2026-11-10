# AgendaFlow - deploy do frontend na Discloud

Conecte o repositório `tiagogomes1214-lab/agendaflow-pro` na Discloud e selecione a branch **discloud-frontend**.
O arquivo `discloud.config` na raiz executa:
- BUILD=npm run build (instala dependências e gera Next.js standalone em dist/)
- START=npm run start (usa o servidor compilado e escuta porta 8080)

Na página **Variáveis da aplicação** da Discloud configure:
`API_INTERNAL_URL=https://agendaflow.discloud.dev`

O valor é lido **no servidor Next.js**, pela rota `frontend/app/api/[...path]/route.ts`.
A variável não contém senha.

Use `agendaflow-tiago` como subdomínio e, se o DNS `.app` falhar, teste `https://agendaflow-tiago.discloud.dev`.
Na sua conta Platinum há dois serviços de 512 MB (API e site) mais o Forno Studio de 1 GB: isso consome 2 GB no total.

Se a compilação falhar, leia os **logs do BUILD** e não somente os logs de inicialização. Não use ZIPs antigos.
