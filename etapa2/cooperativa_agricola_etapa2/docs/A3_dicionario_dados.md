# A3 — Dicionário de Dados

**Projeto:** Cooperativa Agrícola — Projeto Final  
**Disciplina:** Laboratório de Banco de Dados — GPE17M40053  
**SGBD:** MySQL 8.0  
**Equipe:** Artur Gabriel Queiroz de Morais; Arthur Gonçalves Silva; Arthur Marques Cipriano; Arthur Mélo Mesquita Mitrovich; Fabrício Nogueira de Brito

> Documento gerado a partir do catálogo do próprio banco (`information_schema`) por `experimentos/gera_dicionario.py`, no formato do Anexo A do enunciado. Gerar em vez de digitar garante que o dicionário não divirja do esquema real.

Atende à devolutiva da Etapa 1, critério C5: *"complete o dicionário de dados no formato do Anexo A (tipos, restrições)"*.

## associado

Pessoa, fisica ou juridica, associada a cooperativa.

| Atributo | Descrição | Domínio | Obrig. | Restrições | Observação |
|---|---|---|---|---|---|
| `id_associado` | Chave primaria substituta | int unsigned (auto_increment) | Sim | PK | — |
| `matricula` | nao pode repetir | varchar(20) | Sim | UNIQUE (uq_associado_matricula) | RN01 |
| `nome` | Razao social ou nome civil do associado | varchar(120) | Sim | - | — |
| `tipo_pessoa` | define qual especializacao se aplica | char(2) | Sim | CHECK ck_associado_tipo | RN02 |
| `status` | situacao cadastral vigente | varchar(20) | Sim | CHECK ck_associado_status | RN02 |
| `id_associado_indicador` | opcional; nao pode apontar para o proprio associado | int unsigned | Não | FK -> associado.id_associado (fk_associado_indicador) | RN03 |

## associado_cultura

Quais culturas cada associado produz e em que area.

| Atributo | Descrição | Domínio | Obrig. | Restrições | Observação |
|---|---|---|---|---|---|
| `id_associado` | Parte da chave composta | int unsigned | Sim | PK; FK -> associado.id_associado (fk_associado_cultura_associado) | — |
| `id_cultura` | Parte da chave composta | int unsigned | Sim | PK; FK -> cultura.id_cultura (fk_associado_cultura_cultura) | — |
| `area_hectares` | atributo proprio do N:N, positivo | decimal(10,2) | Sim | CHECK ck_associado_cultura_area | RN11 |
| `data_inicio` | Quando o associado passou a produzir a cultura | date | Sim | - | — |

## associado_pf

Especializacao do associado pessoa fisica.

| Atributo | Descrição | Domínio | Obrig. | Restrições | Observação |
|---|---|---|---|---|---|
| `id_associado` | Chave primaria e estrangeira (especializacao) | int unsigned | Sim | PK; FK -> associado.id_associado (fk_associado_pf_associado) | — |
| `cpf` | 11 digitos, nao pode repetir. Dado pessoal | char(11) | Sim | UNIQUE (uq_associado_pf_cpf) | RN04 |
| `data_nascimento` | nao pode ser anterior a 1900. Dado pessoal | date | Sim | CHECK ck_associado_pf_nascimento | RN04 |

## associado_pj

Especializacao do associado pessoa juridica.

| Atributo | Descrição | Domínio | Obrig. | Restrições | Observação |
|---|---|---|---|---|---|
| `id_associado` | Chave primaria e estrangeira (especializacao) | int unsigned | Sim | PK; FK -> associado.id_associado (fk_associado_pj_associado) | — |
| `cnpj` | 14 digitos, nao pode repetir. Dado da empresa | char(14) | Sim | UNIQUE (uq_associado_pj_cnpj) | RN05 |
| `razao_social` | obrigatoria para PJ | varchar(150) | Sim | - | RN05 |

## auditoria

Trilha de alteracoes gravada pelos gatilhos (Etapa 2).

| Atributo | Descrição | Domínio | Obrig. | Restrições | Observação |
|---|---|---|---|---|---|
| `id_auditoria` | Chave primaria substituta (Etapa 2) | bigint unsigned (auto_increment) | Sim | PK | — |
| `tabela` | Tabela auditada | varchar(64) | Sim | - | — |
| `operacao` | INSERT, UPDATE ou DELETE | varchar(10) | Sim | CHECK ck_auditoria_operacao | — |
| `chave_registro` | Identificacao da linha alterada | varchar(80) | Sim | - | — |
| `campo` | Coluna alterada; uma linha por campo | varchar(64) | Sim | - | — |
| `valor_anterior` | Conteudo antes da alteracao | varchar(255) | Não | - | — |
| `valor_novo` | Conteudo depois da alteracao | varchar(255) | Não | - | — |
| `usuario` | quem se conectou | varchar(128) | Sim | - | — |
| `data_hora` | Momento da alteracao | datetime (DEFAULT_GENERATED) | Sim | - | — |

## cultura

Catalogo de culturas trabalhadas pela cooperativa.

| Atributo | Descrição | Domínio | Obrig. | Restrições | Observação |
|---|---|---|---|---|---|
| `id_cultura` | Chave primaria substituta | int unsigned (auto_increment) | Sim | PK | — |
| `nome` | nao pode repetir | varchar(80) | Sim | UNIQUE (uq_cultura_nome) | RN09 |
| `categoria` | Agrupamento comercial da cultura | varchar(50) | Sim | - | — |
| `unidade_medida` | unidade em que a producao e medida | varchar(20) | Sim | - | RN09 |

## entrega

Evento de entrega de producao de um lote.

| Atributo | Descrição | Domínio | Obrig. | Restrições | Observação |
|---|---|---|---|---|---|
| `id_entrega` | Chave primaria substituta | int unsigned (auto_increment) | Sim | PK | — |
| `id_safra` | parte da referencia ao lote de origem | int unsigned | Sim | FK -> lote.id_safra (fk_entrega_lote) | RN16 |
| `numero_lote` | parte da referencia ao lote de origem | smallint unsigned | Sim | FK -> lote.numero_lote (fk_entrega_lote) | RN16 |
| `data_entrega` | precisa cair dentro do periodo da safra | date | Sim | - | RN20 |
| `quantidade` | precisa ser positiva | decimal(12,2) | Sim | CHECK ck_entrega_quantidade | RN16 |
| `qualidade` | classificacao A, B ou C | char(1) | Sim | CHECK ck_entrega_qualidade | RN17 |
| `preco_unitario_kg` | Preco pactuado, positivo | decimal(10,2) | Sim | CHECK ck_entrega_preco | — |
| `status` | estorno e feito por CANCELADA, nunca por DELETE | varchar(20) | Sim | CHECK ck_entrega_status | RN17 |

## historico_associado

Linha do tempo da situacao cadastral do associado.

| Atributo | Descrição | Domínio | Obrig. | Restrições | Observação |
|---|---|---|---|---|---|
| `id_historico` | Chave primaria substituta | int unsigned (auto_increment) | Sim | PK | — |
| `id_associado` | A quem o periodo se refere | int unsigned | Sim | UNIQUE (uq_historico_associado_inicio); FK -> associado.id_associado (fk_historico_associado) | — |
| `data_inicio` | nao repete para o mesmo associado; periodos nao se sobrepoem | date | Sim | UNIQUE (uq_historico_associado_inicio); CHECK ck_historico_periodo | RN15 |
| `data_fim` | nulo indica periodo vigente; so um aberto por associado | date | Não | CHECK ck_historico_periodo | RN15 |
| `situacao` | situacao vigente no periodo | varchar(30) | Sim | CHECK ck_historico_situacao | RN17 |
| `motivo` | Justificativa da mudanca de situacao | varchar(255) | Sim | - | — |

## lote

Entidade fraca: porcao de producao identificada dentro da safra.

| Atributo | Descrição | Domínio | Obrig. | Restrições | Observação |
|---|---|---|---|---|---|
| `id_safra` | parte da chave da entidade fraca | int unsigned | Sim | PK; FK -> safra.id_safra (fk_lote_safra) | RN13 |
| `numero_lote` | unico dentro da safra, positivo | smallint unsigned | Sim | PK; CHECK ck_lote_numero | RN13 |
| `id_propriedade` | onde o lote e produzido | int unsigned | Sim | FK -> propriedade.id_propriedade (fk_lote_propriedade) | RN14 |
| `id_cultura` | o que o lote produz | int unsigned | Sim | FK -> cultura.id_cultura (fk_lote_cultura) | RN14 |
| `quantidade_planejada` | Precisa ser positiva | decimal(12,2) | Sim | CHECK ck_lote_quantidade | — |
| `status` | Estagio do lote no ciclo produtivo | varchar(30) | Sim | CHECK ck_lote_status | — |

## movimento_financeiro

Lancamento de credito ou debito de uma prestacao.

| Atributo | Descrição | Domínio | Obrig. | Restrições | Observação |
|---|---|---|---|---|---|
| `id_movimento` | Chave primaria substituta | int unsigned (auto_increment) | Sim | PK | — |
| `id_prestacao` | a qual fechamento pertence | int unsigned | Sim | FK -> prestacao_contas.id_prestacao (fk_movimento_prestacao) | RN19 |
| `data_movimento` | Data do lancamento | date | Sim | - | — |
| `valor` | precisa ser positivo | decimal(14,2) | Sim | CHECK ck_movimento_valor | RN19 |
| `tipo` | CREDITO ou DEBITO | varchar(20) | Sim | CHECK ck_movimento_tipo | RN19 |
| `status` | Situacao da liquidacao | varchar(20) | Sim | CHECK ck_movimento_status | — |
| `referencia` | Identificador externo, nao repete | varchar(40) | Sim | UNIQUE (uq_movimento_referencia) | — |

## prestacao_contas

Fechamento financeiro de um associado em uma safra.

| Atributo | Descrição | Domínio | Obrig. | Restrições | Observação |
|---|---|---|---|---|---|
| `id_prestacao` | Chave primaria substituta | int unsigned (auto_increment) | Sim | PK | — |
| `id_associado` | uma prestacao por associado e safra | int unsigned | Sim | UNIQUE (uq_prestacao_associado_safra); FK -> associado.id_associado (fk_prestacao_associado) | RN18 |
| `id_safra` | uma prestacao por associado e safra | int unsigned | Sim | UNIQUE (uq_prestacao_associado_safra); FK -> safra.id_safra (fk_prestacao_safra) | RN18 |
| `total_bruto` | Soma das entregas recebidas, nao negativa | decimal(14,2) | Sim | CHECK ck_prestacao_bruto; CHECK ck_prestacao_descontos; CHECK ck_prestacao_saldo | — |
| `total_descontos` | nao pode superar o bruto | decimal(14,2) | Sim | CHECK ck_prestacao_descontos; CHECK ck_prestacao_saldo | RN18 |
| `saldo` | descontos | decimal(14,2) | Sim | CHECK ck_prestacao_saldo | RN18 |
| `status` | Estagio do fechamento financeiro | varchar(30) | Sim | CHECK ck_prestacao_status | — |

## propriedade

Area rural pertencente a um associado.

| Atributo | Descrição | Domínio | Obrig. | Restrições | Observação |
|---|---|---|---|---|---|
| `id_propriedade` | Chave primaria substituta | int unsigned (auto_increment) | Sim | PK | — |
| `id_associado` | cada propriedade tem exatamente um dono | int unsigned | Sim | FK -> associado.id_associado (fk_propriedade_associado) | RN06 |
| `nome` | Nome pelo qual a propriedade e conhecida | varchar(120) | Sim | - | — |
| `registro_rural` | nao pode repetir | varchar(30) | Sim | UNIQUE (uq_propriedade_registro) | RN07 |
| `municipio` | Municipio onde fica a area | varchar(80) | Sim | - | — |
| `area_hectares` | precisa ser positiva | decimal(10,2) | Sim | CHECK ck_propriedade_area | RN08 |
| `status` | Situacao da regularizacao fundiaria | varchar(30) | Sim | CHECK ck_propriedade_status | — |

## safra

Ciclo produtivo com periodo definido.

| Atributo | Descrição | Domínio | Obrig. | Restrições | Observação |
|---|---|---|---|---|---|
| `id_safra` | Chave primaria substituta | int unsigned (auto_increment) | Sim | PK | — |
| `descricao` | identificacao da safra, nao pode repetir | varchar(100) | Sim | UNIQUE (uq_safra_descricao) | RN10 |
| `data_inicio` | Abertura do periodo produtivo | date | Sim | CHECK ck_safra_periodo | — |
| `data_fim` | precisa ser posterior a data_inicio | date | Sim | CHECK ck_safra_periodo | RN10 |
| `status` | estagio do ciclo da safra | varchar(30) | Sim | CHECK ck_safra_status | RN10 |

## safra_cultura

Meta de producao e preco-base por cultura em cada safra.

| Atributo | Descrição | Domínio | Obrig. | Restrições | Observação |
|---|---|---|---|---|---|
| `id_safra` | Parte da chave composta | int unsigned | Sim | PK; FK -> safra.id_safra (fk_safra_cultura_safra) | — |
| `id_cultura` | Parte da chave composta | int unsigned | Sim | PK; FK -> cultura.id_cultura (fk_safra_cultura_cultura) | — |
| `meta_kg` | atributo proprio do N:N, positivo | decimal(12,2) | Sim | CHECK ck_safra_cultura_meta | RN12 |
| `preco_base_kg` | preco de referencia, positivo | decimal(10,2) | Sim | CHECK ck_safra_cultura_preco | RN12 |

## usuario_app

Usuarios da aplicacao e seus perfis de acesso (Etapa 2).

| Atributo | Descrição | Domínio | Obrig. | Restrições | Observação |
|---|---|---|---|---|---|
| `id_usuario` | Chave primaria substituta (Etapa 2) | int unsigned (auto_increment) | Sim | PK | — |
| `login` | Identificador de acesso, nao repete | varchar(40) | Sim | UNIQUE (uq_usuario_app_login) | — |
| `nome` | Nome exibido na interface | varchar(120) | Sim | - | — |
| `perfil` | LEITURA, OPERACIONAL ou FINANCEIRO | varchar(20) | Sim | CHECK ck_usuario_app_perfil | — |
| `senha_hash` | PBKDF2-HMAC-SHA256; nunca a senha em claro | varchar(255) | Sim | - | — |
| `senha_sal` | Sal aleatorio de 16 bytes, unico por usuario | varchar(64) | Sim | - | — |
| `algoritmo` | Algoritmo e custo usados, para migracao futura | varchar(40) | Sim | - | — |
| `ativo` | Permite desativar acesso sem apagar o usuario | tinyint(1) | Sim | - | — |
| `criado_em` | Data de criacao do acesso | datetime (DEFAULT_GENERATED) | Sim | - | — |
