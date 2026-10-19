# A4 — Modelo lógico relacional e decisões de mapeamento

## Esquema relacional

- **ASSOCIADO**(**id_associado**, matricula, nome, tipo_pessoa, status, id_associado_indicador → ASSOCIADO.id_associado)
- **ASSOCIADO_PF**(**id_associado** → ASSOCIADO.id_associado, cpf, data_nascimento)
- **ASSOCIADO_PJ**(**id_associado** → ASSOCIADO.id_associado, cnpj, razao_social)
- **PROPRIEDADE**(**id_propriedade**, id_associado → ASSOCIADO.id_associado, nome, registro_rural, municipio, area_hectares, status)
- **CULTURA**(**id_cultura**, nome, categoria, unidade_medida)
- **SAFRA**(**id_safra**, descricao, data_inicio, data_fim, status)
- **ASSOCIADO_CULTURA**(**id_associado** → ASSOCIADO.id_associado, **id_cultura** → CULTURA.id_cultura, area_hectares, data_inicio)
- **SAFRA_CULTURA**(**id_safra** → SAFRA.id_safra, **id_cultura** → CULTURA.id_cultura, meta_kg, preco_base_kg)
- **LOTE**(**id_safra** → SAFRA.id_safra, **numero_lote**, id_propriedade → PROPRIEDADE.id_propriedade, id_cultura → CULTURA.id_cultura, quantidade_planejada, status)
- **HISTORICO_ASSOCIADO**(**id_historico**, id_associado → ASSOCIADO.id_associado, data_inicio, data_fim, situacao, motivo)
- **ENTREGA**(**id_entrega**, id_safra, numero_lote → LOTE.(id_safra, numero_lote), data_entrega, quantidade, qualidade, preco_unitario_kg, status)
- **PRESTACAO_CONTAS**(**id_prestacao**, id_associado → ASSOCIADO.id_associado, id_safra → SAFRA.id_safra, total_bruto, total_descontos, saldo, status)
- **MOVIMENTO_FINANCEIRO**(**id_movimento**, id_prestacao → PRESTACAO_CONTAS.id_prestacao, data_movimento, valor, tipo, status, referencia)

## Decisões de mapeamento

### 1. Generalização/especialização ASSOCIADO → ASSOCIADO_PF / ASSOCIADO_PJ

Foi adotada a estratégia de **superclasse + uma tabela para cada subclasse**. A tabela `associado` concentra os atributos comuns e as tabelas `associado_pf` e `associado_pj` armazenam os atributos específicos.

A especialização é **total e disjunta** no modelo conceitual: todo associado deve ser classificado como PF ou PJ e um associado não pertence às duas subclasses. No banco, `tipo_pessoa` restringe o domínio a PF/PJ e a carga mantém a correspondência com a tabela de subclasse. A integridade de existência das subclasses é garantida pelas PKs/FKs; a verificação de completude é documentada como regra de carga.

### 2. Relacionamentos N:N

`ASSOCIADO_CULTURA` resolve o N:N entre associado e cultura e possui `area_hectares` e `data_inicio`, atributos próprios da associação.

`SAFRA_CULTURA` resolve o N:N entre safra e cultura e possui `meta_kg` e `preco_base_kg`, atributos próprios da associação.

### 3. Entidade fraca LOTE

`LOTE` depende de `SAFRA` para sua identificação. O número do lote pode se repetir em safras diferentes; portanto, a chave primária é composta por `(id_safra, numero_lote)`. Essa escolha representa no modelo lógico a identificação por dependência da entidade forte `SAFRA`.

### 4. Autorrelacionamento

`ASSOCIADO.id_associado_indicador` referencia a própria tabela `ASSOCIADO`. Isso representa a relação de indicação: um associado pode indicar outros associados e um associado pode ter, no máximo, um indicador direto.

### 5. Atributo temporal

`HISTORICO_ASSOCIADO` mantém a situação de um associado ao longo do tempo por meio de `data_inicio` e `data_fim`. A combinação `(id_associado, data_inicio)` é única para preservar a ordenação dos eventos históricos.

### 6. Chaves substitutas e naturais

Para entidades operacionais, foram usadas chaves substitutas inteiras (`id_*`) porque identificadores como nome, descrição e dados cadastrais podem sofrer alteração e não são adequados para FKs extensas. As chaves naturais relevantes continuam protegidas por `UNIQUE`, como matrícula, CPF, CNPJ, registro rural, nome de cultura e referência financeira.

Nas tabelas N:N foram mantidas chaves compostas formadas pelas FKs porque a combinação dos participantes identifica naturalmente uma ocorrência da associação. Em `LOTE`, a chave composta também é intencional: o número do lote só tem significado único dentro da safra.

### 7. Relacionamento ENTREGA–LOTE

`ENTREGA` usa a FK composta `(id_safra, numero_lote)` para apontar diretamente para o lote de origem. Isso preserva a rastreabilidade sem duplicar os dados do lote.

### 8. Prestação de contas

`PRESTACAO_CONTAS` possui uma restrição `UNIQUE(id_associado, id_safra)`, pois existe no máximo uma prestação consolidada por associado em cada safra. `MOVIMENTO_FINANCEIRO` depende dela e detalha seus créditos e débitos.
