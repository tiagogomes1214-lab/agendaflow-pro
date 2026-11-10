# AgendaFlow - deploy da API na Discloud

Selecione o repositório `tiagogomes1214-lab/agendaflow-pro` e a branch **discloud-api** na integração GitHub da Discloud.
O `discloud.config` está na raiz e executa `python main.py` na porta 8080.

No painel da **aplicação** configure secretamente:
- DB_HOST: host do **Session pooler** do Supabase, sem esquema nem usuário
- DB_PORT: 5432
- DB_NAME: postgres
- DB_USER: usuário completo retornado pelo Supabase (postgres.ID_DO_PROJETO)
- DB_PASSWORD: senha original do banco
- ADMIN_EMAIL: e-mail administrativo válido
- ADMIN_PASSWORD: senha forte com pelo menos 12 caracteres
- JWT_SECRET: chave aleatória com pelo menos 32 caracteres
- CORS_ORIGINS: URL HTTPS do frontend (quando disponível)
- BUSINESS_NAME: AgendaFlow
- BUSINESS_TIMEZONE: America/Sao_Paulo

Não armazene segredos no GitHub ou no `discloud.config`.
Verifique os logs e teste `https://agendaflow.discloud.dev/health`.
Esta branch mantém a correção IPv4 do Session Pooler no arquivo `backend/app/database.py`.
