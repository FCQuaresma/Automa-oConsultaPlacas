# Automação de Consulta de Placas (FIPE)

Automação em Python que consulta o valor de mercado (tabela FIPE) e o modelo de caminhões a partir da placa, para uso em massa a partir de uma planilha Excel.

## Problema real resolvido

Este projeto foi desenvolvido para o **Santander**. O banco precisava avaliar o valor de mercado atual de caminhões dados como garantia em operações de crédito e leasing, e esse levantamento era feito manualmente, placa por placa, em diferentes sites de consulta.

A automação eliminou esse trabalho manual: basta preencher a planilha com as placas e o próprio script consulta, extrai e organiza os dados, liberando a equipe para focar na análise em vez da coleta.

> **Nota sobre dados:** a planilha `Placas.xlsx` usada com o cliente contém placas e valores reais e **não está neste repositório** (veja `.gitignore`). Apenas a estrutura/formato esperado é documentada abaixo.

## Como funciona

1. Lê a lista de placas de uma planilha Excel (`Placas.xlsx`), a partir da linha configurada em `config.py`.
2. Para cada placa, consulta três fontes públicas de tabela FIPE:
   - TabelaFipeBrasil
   - FipePelaPlaca
   - KePlaca
3. Extrai marca/modelo e valor FIPE de cada resultado.
4. Grava o resultado de volta na planilha, em colunas separadas por site.
5. Ao final, imprime um resumo: quantas consultas deram certo, quantas não encontraram o veículo e quantas deram erro.

### Formato esperado da planilha

| Coluna | Conteúdo |
|---|---|
| A | Placa |
| B / C | Modelo / Valor — TabelaFipeBrasil |
| D / E | Modelo / Valor — FipePelaPlaca |
| F / G | Modelo / Valor — KePlaca |

Cabeçalho na linha 2, dados a partir da linha 3 (configurável em `config.py`).

## Recursos de robustez

- **Retomada de progresso**: linhas já preenchidas são puladas, permitindo interromper e continuar depois sem refazer trabalho.
- **Novas tentativas com backoff progressivo**: diante de bloqueios ou instabilidade dos sites, o script tenta novamente aumentando o tempo de espera, e desiste de forma controlada em vez de travar.
- **Delays aleatórios entre requisições**: reduz o risco de bloqueio por excesso de requisições.
- **Tratamento de arquivo em uso**: se a planilha estiver aberta no Excel no momento de salvar, o script avisa e aguarda o usuário fechar o arquivo em vez de perder o progresso.

## Como rodar

1. Execute `instalar.bat` para instalar as dependências (Python precisa estar instalado e no PATH).
2. Coloque a planilha `Placas.xlsx` na mesma pasta do projeto, seguindo o formato acima.
3. Execute `run.bat` para iniciar as consultas.

## Stack

- Python
- [requests](https://pypi.org/project/requests/)
- [BeautifulSoup4](https://pypi.org/project/beautifulsoup4/)
- [openpyxl](https://pypi.org/project/openpyxl/)
