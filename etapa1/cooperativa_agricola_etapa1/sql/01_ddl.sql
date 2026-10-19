-- Projeto Final - Laboratório de Banco de Dados 2026/2
-- Tema: Cooperativa Agrícola
-- SGBD: MySQL 8.0+
-- A6 - Script físico (DDL)
-- Autores: Artur Gabriel Queiroz de Morais; Arthur Gonçalves Silva;
-- Arthur Marques Cipriano; Arthur Mélo Mesquita Mitrovich; Fabrício Nogueira de Brito

DROP DATABASE IF EXISTS cooperativa_agricola;
CREATE DATABASE cooperativa_agricola
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;
USE cooperativa_agricola;

-- RN01-RN05: cadastro, identificação e especialização de associados.
CREATE TABLE associado (
    id_associado INT UNSIGNED NOT NULL AUTO_INCREMENT,
    matricula VARCHAR(20) NOT NULL,
    nome VARCHAR(120) NOT NULL,
    tipo_pessoa CHAR(2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ATIVO',
    id_associado_indicador INT UNSIGNED NULL,
    CONSTRAINT pk_associado PRIMARY KEY (id_associado),
    CONSTRAINT uq_associado_matricula UNIQUE (matricula),
    CONSTRAINT ck_associado_tipo CHECK (tipo_pessoa IN ('PF','PJ')),
    CONSTRAINT ck_associado_status CHECK (status IN ('ATIVO','SUSPENSO','INATIVO')),
    CONSTRAINT fk_associado_indicador
        FOREIGN KEY (id_associado_indicador)
        REFERENCES associado(id_associado)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- RN04: cada associado PF possui dados próprios da pessoa física.
CREATE TABLE associado_pf (
    id_associado INT UNSIGNED NOT NULL,
    cpf CHAR(11) NOT NULL,
    data_nascimento DATE NOT NULL,
    CONSTRAINT pk_associado_pf PRIMARY KEY (id_associado),
    CONSTRAINT uq_associado_pf_cpf UNIQUE (cpf),
    CONSTRAINT fk_associado_pf_associado
        FOREIGN KEY (id_associado)
        REFERENCES associado(id_associado)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT ck_associado_pf_nascimento CHECK (data_nascimento >= '1900-01-01')
);

-- RN05: cada associado PJ possui CNPJ e razão social próprios.
CREATE TABLE associado_pj (
    id_associado INT UNSIGNED NOT NULL,
    cnpj CHAR(14) NOT NULL,
    razao_social VARCHAR(150) NOT NULL,
    CONSTRAINT pk_associado_pj PRIMARY KEY (id_associado),
    CONSTRAINT uq_associado_pj_cnpj UNIQUE (cnpj),
    CONSTRAINT fk_associado_pj_associado
        FOREIGN KEY (id_associado)
        REFERENCES associado(id_associado)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- RN06-RN08: propriedades pertencem a um associado e possuem área positiva.
CREATE TABLE propriedade (
    id_propriedade INT UNSIGNED NOT NULL AUTO_INCREMENT,
    id_associado INT UNSIGNED NOT NULL,
    nome VARCHAR(120) NOT NULL,
    registro_rural VARCHAR(30) NOT NULL,
    municipio VARCHAR(80) NOT NULL,
    area_hectares DECIMAL(10,2) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'ATIVA',
    CONSTRAINT pk_propriedade PRIMARY KEY (id_propriedade),
    CONSTRAINT uq_propriedade_registro UNIQUE (registro_rural),
    CONSTRAINT ck_propriedade_area CHECK (area_hectares > 0),
    CONSTRAINT ck_propriedade_status CHECK (status IN ('ATIVA','EM_REGULARIZACAO','INATIVA')),
    CONSTRAINT fk_propriedade_associado
        FOREIGN KEY (id_associado)
        REFERENCES associado(id_associado)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

-- RN09-RN10: catálogo de culturas.
CREATE TABLE cultura (
    id_cultura INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nome VARCHAR(80) NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    unidade_medida VARCHAR(20) NOT NULL,
    CONSTRAINT pk_cultura PRIMARY KEY (id_cultura),
    CONSTRAINT uq_cultura_nome UNIQUE (nome)
);

-- RN11-RN12: cada safra possui período e situação.
CREATE TABLE safra (
    id_safra INT UNSIGNED NOT NULL AUTO_INCREMENT,
    descricao VARCHAR(100) NOT NULL,
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,
    status VARCHAR(30) NOT NULL,
    CONSTRAINT pk_safra PRIMARY KEY (id_safra),
    CONSTRAINT uq_safra_descricao UNIQUE (descricao),
    CONSTRAINT ck_safra_periodo CHECK (data_fim > data_inicio),
    CONSTRAINT ck_safra_status CHECK (status IN ('PLANEJADA','EM_ANDAMENTO','ENCERRADA'))
);

-- RN13: um associado pode produzir várias culturas e a relação registra a área plantada.
CREATE TABLE associado_cultura (
    id_associado INT UNSIGNED NOT NULL,
    id_cultura INT UNSIGNED NOT NULL,
    area_hectares DECIMAL(10,2) NOT NULL,
    data_inicio DATE NOT NULL,
    CONSTRAINT pk_associado_cultura PRIMARY KEY (id_associado, id_cultura),
    CONSTRAINT ck_associado_cultura_area CHECK (area_hectares > 0),
    CONSTRAINT fk_associado_cultura_associado
        FOREIGN KEY (id_associado)
        REFERENCES associado(id_associado)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_associado_cultura_cultura
        FOREIGN KEY (id_cultura)
        REFERENCES cultura(id_cultura)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

-- RN14: uma safra pode contemplar várias culturas e a relação guarda meta e preço-base.
CREATE TABLE safra_cultura (
    id_safra INT UNSIGNED NOT NULL,
    id_cultura INT UNSIGNED NOT NULL,
    meta_kg DECIMAL(12,2) NOT NULL,
    preco_base_kg DECIMAL(10,2) NOT NULL,
    CONSTRAINT pk_safra_cultura PRIMARY KEY (id_safra, id_cultura),
    CONSTRAINT ck_safra_cultura_meta CHECK (meta_kg > 0),
    CONSTRAINT ck_safra_cultura_preco CHECK (preco_base_kg > 0),
    CONSTRAINT fk_safra_cultura_safra
        FOREIGN KEY (id_safra)
        REFERENCES safra(id_safra)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_safra_cultura_cultura
        FOREIGN KEY (id_cultura)
        REFERENCES cultura(id_cultura)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

-- RN15-RN16: LOTE é entidade fraca, identificada por (safra, número do lote).
CREATE TABLE lote (
    id_safra INT UNSIGNED NOT NULL,
    numero_lote SMALLINT UNSIGNED NOT NULL,
    id_propriedade INT UNSIGNED NOT NULL,
    id_cultura INT UNSIGNED NOT NULL,
    quantidade_planejada DECIMAL(12,2) NOT NULL,
    status VARCHAR(30) NOT NULL,
    CONSTRAINT pk_lote PRIMARY KEY (id_safra, numero_lote),
    CONSTRAINT ck_lote_numero CHECK (numero_lote > 0),
    CONSTRAINT ck_lote_quantidade CHECK (quantidade_planejada > 0),
    CONSTRAINT ck_lote_status CHECK (status IN ('PLANEJADO','EM_PRODUCAO','PRONTO_ENTREGA','ENCERRADO')),
    CONSTRAINT fk_lote_safra
        FOREIGN KEY (id_safra)
        REFERENCES safra(id_safra)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_lote_propriedade
        FOREIGN KEY (id_propriedade)
        REFERENCES propriedade(id_propriedade)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_lote_cultura
        FOREIGN KEY (id_cultura)
        REFERENCES cultura(id_cultura)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

-- RN17: histórico temporal da situação do associado.
CREATE TABLE historico_associado (
    id_historico INT UNSIGNED NOT NULL AUTO_INCREMENT,
    id_associado INT UNSIGNED NOT NULL,
    data_inicio DATE NOT NULL,
    data_fim DATE NULL,
    situacao VARCHAR(30) NOT NULL,
    motivo VARCHAR(255) NOT NULL,
    CONSTRAINT pk_historico_associado PRIMARY KEY (id_historico),
    CONSTRAINT uq_historico_associado_inicio UNIQUE (id_associado, data_inicio),
    CONSTRAINT ck_historico_periodo CHECK (data_fim IS NULL OR data_fim >= data_inicio),
    CONSTRAINT ck_historico_situacao CHECK (situacao IN ('ATIVO','ADIMPLENTE','PENDENTE','SUSPENSO','INATIVO')),
    CONSTRAINT fk_historico_associado
        FOREIGN KEY (id_associado)
        REFERENCES associado(id_associado)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- RN18: entrega rastreia lote, data, quantidade, qualidade e preço.
CREATE TABLE entrega (
    id_entrega INT UNSIGNED NOT NULL AUTO_INCREMENT,
    id_safra INT UNSIGNED NOT NULL,
    numero_lote SMALLINT UNSIGNED NOT NULL,
    data_entrega DATE NOT NULL,
    quantidade DECIMAL(12,2) NOT NULL,
    qualidade CHAR(1) NOT NULL,
    preco_unitario_kg DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) NOT NULL,
    CONSTRAINT pk_entrega PRIMARY KEY (id_entrega),
    CONSTRAINT ck_entrega_quantidade CHECK (quantidade > 0),
    CONSTRAINT ck_entrega_qualidade CHECK (qualidade IN ('A','B','C')),
    CONSTRAINT ck_entrega_preco CHECK (preco_unitario_kg > 0),
    CONSTRAINT ck_entrega_status CHECK (status IN ('PENDENTE','RECEBIDA','CANCELADA')),
    CONSTRAINT fk_entrega_lote
        FOREIGN KEY (id_safra, numero_lote)
        REFERENCES lote(id_safra, numero_lote)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

-- RN19: uma prestação de contas consolida os valores de um associado em uma safra.
CREATE TABLE prestacao_contas (
    id_prestacao INT UNSIGNED NOT NULL AUTO_INCREMENT,
    id_associado INT UNSIGNED NOT NULL,
    id_safra INT UNSIGNED NOT NULL,
    total_bruto DECIMAL(14,2) NOT NULL,
    total_descontos DECIMAL(14,2) NOT NULL,
    saldo DECIMAL(14,2) NOT NULL,
    status VARCHAR(30) NOT NULL,
    CONSTRAINT pk_prestacao_contas PRIMARY KEY (id_prestacao),
    CONSTRAINT uq_prestacao_associado_safra UNIQUE (id_associado, id_safra),
    CONSTRAINT ck_prestacao_bruto CHECK (total_bruto >= 0),
    CONSTRAINT ck_prestacao_descontos CHECK (total_descontos >= 0 AND total_descontos <= total_bruto),
    CONSTRAINT ck_prestacao_saldo CHECK (saldo = total_bruto - total_descontos),
    CONSTRAINT ck_prestacao_status CHECK (status IN ('ABERTA','EM_CONFERENCIA','FECHADA')),
    CONSTRAINT fk_prestacao_associado
        FOREIGN KEY (id_associado)
        REFERENCES associado(id_associado)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_prestacao_safra
        FOREIGN KEY (id_safra)
        REFERENCES safra(id_safra)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

-- RN20: movimentações financeiras pertencem a uma prestação de contas.
CREATE TABLE movimento_financeiro (
    id_movimento INT UNSIGNED NOT NULL AUTO_INCREMENT,
    id_prestacao INT UNSIGNED NOT NULL,
    data_movimento DATE NOT NULL,
    valor DECIMAL(14,2) NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    referencia VARCHAR(40) NOT NULL,
    CONSTRAINT pk_movimento_financeiro PRIMARY KEY (id_movimento),
    CONSTRAINT uq_movimento_referencia UNIQUE (referencia),
    CONSTRAINT ck_movimento_valor CHECK (valor > 0),
    CONSTRAINT ck_movimento_tipo CHECK (tipo IN ('CREDITO','DEBITO')),
    CONSTRAINT ck_movimento_status CHECK (status IN ('PENDENTE','LIQUIDADO','CANCELADO')),
    CONSTRAINT fk_movimento_prestacao
        FOREIGN KEY (id_prestacao)
        REFERENCES prestacao_contas(id_prestacao)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- Índices auxiliares para as consultas da Etapa 1.
CREATE INDEX idx_associado_status ON associado(status);
CREATE INDEX idx_propriedade_associado ON propriedade(id_associado);
CREATE INDEX idx_safra_status ON safra(status);
CREATE INDEX idx_lote_propriedade ON lote(id_propriedade);
CREATE INDEX idx_lote_cultura ON lote(id_cultura);
CREATE INDEX idx_entrega_data ON entrega(data_entrega);
CREATE INDEX idx_entrega_lote ON entrega(id_safra, numero_lote);
CREATE INDEX idx_historico_associado_data ON historico_associado(id_associado, data_inicio);
CREATE INDEX idx_prestacao_safra ON prestacao_contas(id_safra);
CREATE INDEX idx_movimento_data ON movimento_financeiro(data_movimento);
