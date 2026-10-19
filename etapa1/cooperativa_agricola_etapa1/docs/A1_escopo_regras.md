# A1 — Escopo e Regras de Negócio

## Identificação

**Projeto:** Do modelo conceitual à aplicação: um banco de dados completo  
**Disciplina:** Laboratório de Banco de Dados — GPE17M40083  
**Tema:** Cooperativa Agrícola — safras, lotes rastreáveis, associados com histórico de entregas e prestação de contas  
**SGBD:** MySQL 8.0+  
**Equipe:** Artur Gabriel Queiroz de Morais; Arthur Gonçalves Silva; Arthur Marques Cipriano; Arthur Mélo Mesquita Mitrovich; Fabrício Nogueira de Brito

## Escopo do domínio

O sistema representa o núcleo operacional de uma cooperativa agrícola. O objetivo é registrar os associados, suas propriedades rurais, as culturas trabalhadas, as safras e os lotes produzidos. A partir desses cadastros, o banco mantém a rastreabilidade das entregas feitas pelos lotes, registra a situação histórica dos associados e consolida a prestação de contas financeira por associado e safra.

O domínio começa no cadastro do associado e de sua propriedade. Um associado pode atuar como pessoa física ou jurídica, pode ser indicado por outro associado e pode produzir várias culturas. As culturas são vinculadas às safras com uma meta de produção e um preço-base. Dentro de uma safra, a produção é dividida em lotes. O lote é uma entidade fraca porque sua identificação depende da safra e de um número de lote que só é único dentro daquela safra.

As entregas representam os eventos de movimentação da produção. Cada entrega aponta para o lote de origem e registra data, quantidade, qualidade, preço e situação. Assim, é possível consultar a trajetória de uma produção desde a propriedade e cultura até as entregas realizadas.

O componente financeiro consolida, por associado e safra, os valores brutos, descontos e saldo da prestação de contas. As movimentações financeiras detalham créditos e débitos relacionados a essa prestação. O histórico temporal registra mudanças de situação do associado em períodos datados, permitindo analisar a situação mais recente e sua evolução.

### Fora do escopo

Nesta etapa não são modelados detalhadamente: estoque físico de armazéns, logística de transporte, venda para clientes externos, emissão fiscal, folha de pagamento de funcionários da cooperativa e interface de usuário. A Etapa 1 concentra-se no projeto, implementação, povoamento e verificação do banco.

## Regras de negócio

| Regra | Afirmação verificável | Atendimento |
|---|---|---|
| **RN01** | Cada associado deve possuir uma matrícula única. | Restrição do banco (uq_associado_matricula). |
| **RN02** | O tipo de pessoa do associado deve ser PF ou PJ e seu status deve estar entre ATIVO, SUSPENSO ou INATIVO. | Restrição do banco (ck_associado_tipo/ck_associado_status). |
| **RN03** | Um associado pode ser indicado por outro associado; o indicador é opcional e não pode formar uma autoindicação. | FK fk_associado_indicador + validação por consulta/carga. |
| **RN04** | Associado do tipo PF deve possuir CPF único e data de nascimento válida. | Tabela associado_pf, uq_associado_pf_cpf e ck_associado_pf_nascimento; completude verificada na carga. |
| **RN05** | Associado do tipo PJ deve possuir CNPJ único e razão social. | Tabela associado_pj e uq_associado_pj_cnpj; completude verificada na carga. |
| **RN06** | Cada propriedade pertence a exatamente um associado. | FK fk_propriedade_associado NOT NULL. |
| **RN07** | O registro rural de uma propriedade não pode se repetir. | Restrição do banco (uq_propriedade_registro). |
| **RN08** | A área cadastrada de uma propriedade deve ser positiva. | Restrição do banco (ck_propriedade_area). |
| **RN09** | Cada cultura possui nome único e uma unidade de medida definida. | Restrição do banco (uq_cultura_nome) e atributos NOT NULL. |
| **RN10** | A data final de uma safra deve ser posterior à data inicial e sua situação deve ser válida. | Restrição do banco (ck_safra_periodo/ck_safra_status). |
| **RN11** | Um associado pode produzir várias culturas e, quando cadastrado, a área de produção da associação deve ser positiva. | Tabela associativa associado_cultura e ck_associado_cultura_area. |
| **RN12** | Uma safra pode contemplar várias culturas; para cada combinação são registradas meta de produção e preço-base positivos. | Tabela safra_cultura e checks correspondentes. |
| **RN13** | Um lote é identificado pela combinação da safra com seu número de lote; o número é exclusivo dentro da safra. | Chave composta pk_lote. |
| **RN14** | Todo lote deve estar vinculado a uma propriedade e a uma cultura existentes. | FKs fk_lote_propriedade e fk_lote_cultura. |
| **RN15** | O histórico de um associado deve ser registrado em períodos cronológicos, sem datas de início repetidas para o mesmo associado. | uq_historico_associado_inicio + consulta de verificação temporal. |
| **RN16** | Toda entrega deve referenciar um lote existente e possuir quantidade positiva. | FK fk_entrega_lote + ck_entrega_quantidade. |
| **RN17** | A qualidade de uma entrega deve ser A, B ou C, e seu status deve ser PENDENTE, RECEBIDA ou CANCELADA. | Checks ck_entrega_qualidade e ck_entrega_status. |
| **RN18** | Cada associado possui no máximo uma prestação de contas por safra, e o saldo deve ser igual ao bruto menos descontos. | uq_prestacao_associado_safra + ck_prestacao_saldo. |
| **RN19** | Toda movimentação financeira pertence a uma prestação, possui valor positivo e tipo CREDITO ou DEBITO. | FK fk_movimento_prestacao + checks financeiros. |
| **RN20** | A data de uma entrega deve estar dentro do período da safra à qual seu lote pertence. | Consulta de verificação temporal (03_consultas.sql) e regra de carga; não é implementada por CHECK por envolver outra tabela. |
