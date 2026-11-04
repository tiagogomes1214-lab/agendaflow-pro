# AgendaFlow Pro — roteiro para aprender o código

## Lição 1: como os dados percorrem o sistema

Imagine que um cliente escolhe o serviço "Corte", a profissional "Mariana" e o horário 10:00.

1. `frontend/app/page.tsx` controla os estados de serviço, profissional, dia e horário (`useState`).
2. A função `request()` em `frontend/lib/api.ts` envia um GET para `/api/public/slots`.
3. O arquivo `frontend/app/api/[...path]/route.ts` funciona como **proxy**: encaminha a requisição para o backend.
4. Em `backend/app/main.py`, `get_slots()` chama `slots_for_day()`.
5. `backend/app/scheduling.py` lê os expedientes, intervalos, bloqueios e compromissos no banco.
6. A API devolve uma lista JSON com datas e horas ISO. A tela converte para o fuso de São Paulo.
7. Quando o cliente confirma, `make_appointment()` grava a reserva no PostgreSQL e cria um token secreto de acesso.

### Exercício

Abra `frontend/app/page.tsx`. Encontre `setServiceId` e explique por que ele altera a disponibilidade dos horários. Em seguida, encontre `slots_for_day()` e localize a checagem de conflitos entre compromissos.

## Lição 2: banco de dados relacional

Arquivo: `backend/app/models.py`.

- `Service`: serviço oferecido, duração, preço, cor e status.
- `Staff`: profissional.
- `Appointment`: cliente, serviço, profissional, início, fim, status e preço registrado.
- `WorkHour`: expediente semanal individual ou global.
- `TimeBlock`: folgas, férias ou feriados.
- `ClientAccess`: vínculo entre agendamento e hash de um link secreto.
- `Notification`: mensagens previstas e resultado de cada tentativa.
- `Admin`: login e hash de senha.

### Exercício

Crie um novo serviço pelo painel e depois consulte `GET /admin/services` na documentação da API. Encontre no JSON o nome, preço em centavos e a cor.

## Lição 3: rotas e métodos HTTP

Arquivo: `backend/app/main.py`.

- `GET` consulta.
- `POST` cria.
- `PUT` substitui as propriedades editáveis.
- `PATCH` atualiza só parte de um objeto.
- `DELETE` arquiva serviços/profissionais ou exclui bloqueios.

Na área administrativa, quase todas as rotas usam `Depends(require_admin)` e exigem um JWT válido.

### Exercício

Encontre `create_service` e `update_service`. Explique a diferença entre criar um serviço novo e editar um existente.

## Lição 4: calendário em React

Arquivo: `frontend/app/admin/page.tsx`.

O calendário foi implementado com CSS e React, sem depender de bibliotecas pagas. As três visualizações são `day`, `week` e `month`. Os agendamentos aparecem como cartões posicionados proporcionalmente ao horário. Cores são controladas por cada serviço.

### Exercício

Encontre `drawCalendar()` e `drawEvent()`. Altere o tamanho das linhas de hora no CSS (`76px`) e observe como isso afeta a posição dos agendamentos. Para alteração real, os cálculos TSX e CSS precisam usar o mesmo tamanho.

## Lição 5: validação e integridade

- `backend/app/schemas.py` valida o corpo das requisições com Pydantic.
- `backend/app/scheduling.py` impede horário fora do expediente, intervalo ou bloqueio.
- `backend/app/main.py` trata conflitos com erro HTTP `409`.
- No PostgreSQL, uma constraint `EXCLUDE USING gist` impede que duas reservas ativas do mesmo profissional se sobreponham mesmo com cliques simultâneos.

### Exercício

Reserve às 10h, tente reservar o mesmo horário com o mesmo profissional e observe o erro. Agora reserve o mesmo horário com outro profissional para entender o conceito de disponibilidade por recurso.

## Lição 6: notificações e trabalho assíncrono

`backend/app/worker.py` é outro processo que verifica mensagens pendentes no banco. Ele pode enviar e-mail via SMTP ou template pelo WhatsApp Cloud API se houver credenciais configuradas. O worker nunca guarda segredos dentro do código.

### Exercício

Faça uma reserva e abra **Admin → Notificações**. Veja os tipos de mensagens e os estados `queued`, `skipped` ou `sent`.

## Lição 7: Docker, deploy e proteção de dados

`docker-compose.yml` sobe quatro serviços separados: banco, API, worker e interface. A pasta `deploy` contém uma configuração inicial para uma VPS com proxy HTTPS. Nunca publique dados reais de clientes sem tratar LGPD, segurança, backup e políticas de retenção.

### Próximos desafios

1. Implementar paginação e busca de clientes.
2. Criar um fluxo de convite de acesso com verificação de e-mail.
3. Implementar permissões separadas (gestor, recepção e profissional).
4. Adicionar testes Playwright de ponta a ponta.
5. Versionar migrações com Alembic, usando backups.
6. Criar tema e identidade visual configuráveis para cada empresa.
7. Testar backup, restauração e monitoramento em um ambiente de homologação.
