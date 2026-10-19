# A5 — Verificação de normalização

## Objetivo

O esquema foi analisado até a Terceira Forma Normal (3FN). A análise considera dependências funcionais, chaves candidatas e separação de atributos que representam fatos de entidades diferentes.

## Relações e dependências funcionais principais

| Relação | Dependências funcionais relevantes |
|---|---|
| ASSOCIADO | `id_associado → matricula, nome, tipo_pessoa, status, id_associado_indicador`; `matricula → id_associado, nome, tipo_pessoa, status, id_associado_indicador` |
| ASSOCIADO_PF | `id_associado → cpf, data_nascimento`; `cpf → id_associado, data_nascimento` |
| ASSOCIADO_PJ | `id_associado → cnpj, razao_social`; `cnpj → id_associado, razao_social` |
| PROPRIEDADE | `id_propriedade → id_associado, nome, registro_rural, municipio, area_hectares, status`; `registro_rural → id_propriedade, id_associado, nome, municipio, area_hectares, status` |
| CULTURA | `id_cultura → nome, categoria, unidade_medida`; `nome → id_cultura, categoria, unidade_medida` |
| SAFRA | `id_safra → descricao, data_inicio, data_fim, status`; `descricao → id_safra, data_inicio, data_fim, status` |
| ASSOCIADO_CULTURA | `(id_associado, id_cultura) → area_hectares, data_inicio` |
| SAFRA_CULTURA | `(id_safra, id_cultura) → meta_kg, preco_base_kg` |
| LOTE | `(id_safra, numero_lote) → id_propriedade, id_cultura, quantidade_planejada, status` |
| HISTORICO_ASSOCIADO | `id_historico → id_associado, data_inicio, data_fim, situacao, motivo` |
| ENTREGA | `id_entrega → id_safra, numero_lote, data_entrega, quantidade, qualidade, preco_unitario_kg, status` |
| PRESTACAO_CONTAS | `id_prestacao → id_associado, id_safra, total_bruto, total_descontos, saldo, status`; `(id_associado,id_safra) → id_prestacao, total_bruto, total_descontos, saldo, status` |
| MOVIMENTO_FINANCEIRO | `id_movimento → id_prestacao, data_movimento, valor, tipo, status, referencia`; `referencia → id_movimento, id_prestacao, data_movimento, valor, tipo, status` |

## Primeira Forma Normal

Todas as relações possuem atributos atômicos. Não há listas ou grupos repetitivos dentro de uma coluna. Relações N:N foram decompostas em tabelas associativas, evitando atributos multivalorados.

## Segunda Forma Normal

As relações com chave simples não apresentam dependência parcial porque todos os atributos não-chave dependem da chave inteira. Nas relações com chave composta (`ASSOCIADO_CULTURA`, `SAFRA_CULTURA` e `LOTE`), os atributos descritivos dependem da combinação completa da chave. Por exemplo, `area_hectares` em `ASSOCIADO_CULTURA` depende de `(id_associado,id_cultura)`, e não apenas de uma das partes.

## Terceira Forma Normal

Não foram mantidos atributos não-chave que dependam transitivamente de outro atributo não-chave. Dados de pessoa física/jurídica foram separados da superclasse. Dados de cultura não são repetidos em lote; dados da safra não são repetidos em entrega; dados do associado não são repetidos em propriedade ou prestação de contas.

O atributo `saldo` em `PRESTACAO_CONTAS` é tratado como um valor de fechamento da prestação e é protegido pelo `CHECK` `saldo = total_bruto - total_descontos`. Ele não representa uma dependência transitiva entre atributos não-chave.

## BCNF

As relações principais também atendem à Forma Normal de Boyce-Codd quando consideradas suas chaves candidatas declaradas. Em particular, as restrições `UNIQUE` fazem com que matrícula, CPF, CNPJ, registro rural, nome de cultura, descrição da safra e referência financeira sejam identificadores alternativos válidos.

## Desnormalização

Nenhuma relação foi deliberadamente desnormalizada nesta Etapa 1. Índices foram criados para acesso e não alteram a estrutura lógica normalizada.
