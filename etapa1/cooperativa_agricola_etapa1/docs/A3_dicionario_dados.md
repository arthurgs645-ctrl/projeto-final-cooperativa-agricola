# A3 — Dicionário de dados conceitual

## Convenções
- **Obrig.** = Sim quando o atributo é obrigatório.
- **Domínio** = tipo/limites de valores.
- As observações relacionam o atributo a uma regra de negócio ou decisão de modelagem.

## ASSOCIADO

| Atributo | Descrição | Domínio | Obrig. | Observação |
|---|---|---|:---:|---|
|id_associado|Identificador interno do associado|Inteiro sequencial|Sim|PK substituta|
|matricula|Matrícula única na cooperativa|Texto até 20 caracteres|Sim|RN01; UNIQUE|
|nome|Nome ou razão de identificação do associado|Texto até 120 caracteres|Sim|Dado comum às subclasses|
|tipo_pessoa|Classificação da pessoa|PF ou PJ|Sim|RN02; especialização total/disjunta|
|status|Situação cadastral|ATIVO, SUSPENSO ou INATIVO|Sim|RN02|
|id_associado_indicador|Associado que realizou a indicação|Inteiro|Não|RN03; autorrelacionamento|

## ASSOCIADO_PF

| Atributo | Descrição | Domínio | Obrig. | Observação |
|---|---|---|:---:|---|
|id_associado|Identificador do associado PF|Inteiro|Sim|PK e FK para ASSOCIADO|
|cpf|Cadastro de pessoa física|11 dígitos|Sim|RN04; UNIQUE; dado sintético|
|data_nascimento|Data de nascimento|Data|Sim|RN04|

## ASSOCIADO_PJ

| Atributo | Descrição | Domínio | Obrig. | Observação |
|---|---|---|:---:|---|
|id_associado|Identificador do associado PJ|Inteiro|Sim|PK e FK para ASSOCIADO|
|cnpj|Cadastro nacional da pessoa jurídica|14 dígitos|Sim|RN05; UNIQUE; dado sintético|
|razao_social|Razão social|Texto até 150 caracteres|Sim|RN05|

## PROPRIEDADE

| Atributo | Descrição | Domínio | Obrig. | Observação |
|---|---|---|:---:|---|
|id_propriedade|Identificador interno da propriedade|Inteiro sequencial|Sim|PK substituta|
|id_associado|Proprietário associado|Inteiro|Sim|RN06; FK|
|nome|Nome da propriedade rural|Texto até 120|Sim||
|registro_rural|Registro rural|Texto até 30|Sim|RN07; UNIQUE|
|municipio|Município da propriedade|Texto até 80|Sim||
|area_hectares|Área total da propriedade|Decimal 10,2 > 0|Sim|RN08|
|status|Situação da propriedade|ATIVA, EM_REGULARIZACAO ou INATIVA|Sim||

## CULTURA

| Atributo | Descrição | Domínio | Obrig. | Observação |
|---|---|---|:---:|---|
|id_cultura|Identificador da cultura|Inteiro sequencial|Sim|PK substituta|
|nome|Nome da cultura|Texto até 80|Sim|RN09; UNIQUE|
|categoria|Categoria agrícola|Texto até 50|Sim||
|unidade_medida|Unidade padronizada da produção|Texto até 20|Sim|No projeto, kg|

## SAFRA

| Atributo | Descrição | Domínio | Obrig. | Observação |
|---|---|---|:---:|---|
|id_safra|Identificador da safra|Inteiro sequencial|Sim|PK substituta|
|descricao|Descrição única da safra|Texto até 100|Sim|UNIQUE|
|data_inicio|Início do ciclo|Data|Sim|RN10|
|data_fim|Fim do ciclo|Data|Sim|RN10|
|status|Situação da safra|PLANEJADA, EM_ANDAMENTO ou ENCERRADA|Sim|RN10|

## ASSOCIADO_CULTURA

| Atributo | Descrição | Domínio | Obrig. | Observação |
|---|---|---|:---:|---|
|id_associado|Associado participante|Inteiro|Sim|Parte da PK/FK|
|id_cultura|Cultura produzida|Inteiro|Sim|Parte da PK/FK|
|area_hectares|Área destinada à cultura|Decimal 10,2 > 0|Sim|RN11; atributo próprio do N:N|
|data_inicio|Início da produção da cultura pelo associado|Data|Sim|Atributo temporal da associação|

## SAFRA_CULTURA

| Atributo | Descrição | Domínio | Obrig. | Observação |
|---|---|---|:---:|---|
|id_safra|Safra participante|Inteiro|Sim|Parte da PK/FK|
|id_cultura|Cultura participante|Inteiro|Sim|Parte da PK/FK|
|meta_kg|Meta de produção da cultura na safra|Decimal 12,2 > 0|Sim|RN12; atributo próprio do N:N|
|preco_base_kg|Preço-base por kg|Decimal 10,2 > 0|Sim|RN12|

## LOTE

| Atributo | Descrição | Domínio | Obrig. | Observação |
|---|---|---|:---:|---|
|id_safra|Safra identificadora|Inteiro|Sim|Parte da PK/FK; entidade fraca|
|numero_lote|Número local do lote|Inteiro positivo|Sim|Parte da PK; só é único dentro da safra|
|id_propriedade|Propriedade de origem|Inteiro|Sim|RN14; FK|
|id_cultura|Cultura do lote|Inteiro|Sim|RN14; FK|
|quantidade_planejada|Produção planejada do lote|Decimal 12,2 > 0|Sim||
|status|Situação produtiva|PLANEJADO, EM_PRODUCAO, PRONTO_ENTREGA ou ENCERRADO|Sim||

## HISTORICO_ASSOCIADO

| Atributo | Descrição | Domínio | Obrig. | Observação |
|---|---|---|:---:|---|
|id_historico|Identificador do evento histórico|Inteiro sequencial|Sim|PK substituta|
|id_associado|Associado ao qual pertence o evento|Inteiro|Sim|FK|
|data_inicio|Início da situação registrada|Data|Sim|RN15|
|data_fim|Fim da situação registrada|Data|Não|RN15; pode ser NULL para situação aberta|
|situacao|Situação registrada|ATIVO, ADIMPLENTE, PENDENTE, SUSPENSO ou INATIVO|Sim|RN15|
|motivo|Motivo ou descrição da mudança|Texto até 255|Sim||

## ENTREGA

| Atributo | Descrição | Domínio | Obrig. | Observação |
|---|---|---|:---:|---|
|id_entrega|Identificador da entrega|Inteiro sequencial|Sim|PK substituta|
|id_safra|Safra do lote|Inteiro|Sim|Parte da FK composta|
|numero_lote|Lote de origem|Inteiro|Sim|Parte da FK composta|
|data_entrega|Data em que a produção foi entregue|Data|Sim|RN16 e RN20|
|quantidade|Quantidade entregue|Decimal 12,2 > 0|Sim|RN16; kg|
|qualidade|Classificação da qualidade|A, B ou C|Sim|RN17|
|preco_unitario_kg|Preço por kg no recebimento|Decimal 10,2 > 0|Sim||
|status|Situação da entrega|PENDENTE, RECEBIDA ou CANCELADA|Sim|RN17|

## PRESTACAO_CONTAS

| Atributo | Descrição | Domínio | Obrig. | Observação |
|---|---|---|:---:|---|
|id_prestacao|Identificador da prestação|Inteiro sequencial|Sim|PK substituta|
|id_associado|Associado da prestação|Inteiro|Sim|FK|
|id_safra|Safra da prestação|Inteiro|Sim|FK|
|total_bruto|Total bruto apurado|Decimal 14,2 >= 0|Sim|RN18|
|total_descontos|Total de descontos|Decimal 14,2 >= 0|Sim|RN18|
|saldo|Saldo final|Decimal 14,2|Sim|RN18; saldo = bruto - descontos|
|status|Situação da prestação|ABERTA, EM_CONFERENCIA ou FECHADA|Sim||

## MOVIMENTO_FINANCEIRO

| Atributo | Descrição | Domínio | Obrig. | Observação |
|---|---|---|:---:|---|
|id_movimento|Identificador da movimentação|Inteiro sequencial|Sim|PK substituta|
|id_prestacao|Prestação relacionada|Inteiro|Sim|FK|
|data_movimento|Data do lançamento|Data|Sim||
|valor|Valor da movimentação|Decimal 14,2 > 0|Sim|RN19|
|tipo|Natureza do lançamento|CREDITO ou DEBITO|Sim|RN19|
|status|Situação do lançamento|PENDENTE, LIQUIDADO ou CANCELADO|Sim||
|referencia|Código de referência do lançamento|Texto até 40|Sim|RN19; UNIQUE|

