# Publicação do AgendaFlow Pro (preparação, não deploy automático)

Esta pasta fornece um exemplo para **VPS Linux com Docker, DNS e portas 80/443 liberadas**. O ChatGPT não publicou o projeto nem criou servidores ou contas externas.

1. Prepare a VPS, firewall, domínio com registro A/AAAA correto e backups com testes periódicos de restauração.
2. Copie os arquivos, crie um `.env` seguro via `scripts/setup.ps1` no Windows (ou a partir de `.env.example` no Linux) e defina `DOMAIN=agenda.seudominio.com` no `.env`.
3. Revise `BUSINESS_NAME`, `BUSINESS_TIMEZONE`, `CORS_ORIGINS`, políticas de privacidade e acesso administrativo.
4. Execute `docker compose -f docker-compose.yml -f deploy/compose.production.yml up --build -d`.
5. Verifique o HTTPS do Caddy, rotas públicas, autenticação e saúde do backend. Faça backup antes de cada alteração de esquema.

O proxy HTTPS é provido pelo Caddy com renovação automática de certificado quando o DNS, domínio e acesso externo estão corretamente configurados. A porta 3000 e a 8000 existentes no Compose base continuam acessíveis **somente em loopback do servidor**.

**IMPORTANTE:** esta estrutura é um ponto de partida de implantação, não uma garantia de prontidão para produção. Antes de dados reais/clientes pagantes, adicionar rate limiting anti-spam e anti-brute-force, WAF opcional, auditoria de acessos, revisão LGPD (consentimento, retenção, exclusão), gestão segura de segredos, testes de backup/restauração, monitoramento de indisponibilidade, migrações versionadas (Alembic), CI/CD e observabilidade.

Mensagens de WhatsApp exigem aprovação dos modelos na Cloud API oficial e podem ter custo. E-mail requer SMTP real. Sem isso, as notificações ficam registradas como não configuradas.
