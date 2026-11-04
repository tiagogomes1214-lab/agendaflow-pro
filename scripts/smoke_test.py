"""Validação simples da API em execução, sem criar dados."""
import json
from urllib.request import urlopen

base='http://localhost:8000'
for path in ['/health','/public/info','/public/services','/public/staff']:
    with urlopen(base+path,timeout=6) as response:
        payload=json.loads(response.read())
        assert response.status==200
        print(f'OK {path}:',len(payload) if isinstance(payload,list) else 'respondeu')
print('Testes de leitura da API passaram. Verifique o navegador e faça uma reserva de teste.')
