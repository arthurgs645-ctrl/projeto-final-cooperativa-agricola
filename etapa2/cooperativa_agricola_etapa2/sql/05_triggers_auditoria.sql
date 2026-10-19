-- Projeto Final - Laboratorio de Banco de Dados 2026/2
-- Tema: Cooperativa Agricola - Etapa 2
-- B6 - Gatilhos e auditoria
-- Autores: Artur Gabriel Queiroz de Morais; Arthur Goncalves Silva;
-- Arthur Marques Cipriano; Arthur Melo Mesquita Mitrovich; Fabricio Nogueira de Brito

USE cooperativa_agricola;

-- ---------------------------------------------------------------------------
-- Tabela de auditoria
--
-- Guardamos uma linha por CAMPO alterado, e nao uma linha por UPDATE. Isso
-- custa mais linhas, mas responde diretamente a pergunta que a cooperativa faz
-- numa conferencia: "quem mudou o preco desta entrega, de quanto para quanto?".
-- Com um unico registro por operacao seria preciso comparar dois blocos de
-- valores para descobrir qual campo mudou.
--
-- usuario: gravamos SESSION_USER() porque os gatilhos sao executados no
-- contexto do usuario conectado pela aplicacao. Ver a discussao em
-- docs/B5_seguranca.md sobre SESSION_USER vs CURRENT_USER.
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS auditoria;
CREATE TABLE auditoria (
    id_auditoria   BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    tabela         VARCHAR(64)  NOT NULL,
    operacao       VARCHAR(10)  NOT NULL,
    chave_registro VARCHAR(80)  NOT NULL,
    campo          VARCHAR(64)  NOT NULL,
    valor_anterior VARCHAR(255) NULL,
    valor_novo     VARCHAR(255) NULL,
    usuario        VARCHAR(128) NOT NULL,
    data_hora      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_auditoria PRIMARY KEY (id_auditoria),
    CONSTRAINT ck_auditoria_operacao CHECK (operacao IN ('INSERT','UPDATE','DELETE'))
);

CREATE INDEX idx_auditoria_tabela_data ON auditoria(tabela, data_hora);
CREATE INDEX idx_auditoria_chave       ON auditoria(tabela, chave_registro);

-- ---------------------------------------------------------------------------
-- GATILHO 1 - entrega (AFTER UPDATE)
--
-- Por que auditar entrega: a entrega e o documento que converte producao em
-- dinheiro. Quantidade, preco e status definem quanto o associado recebe na
-- prestacao de contas. Uma alteracao silenciosa em qualquer um dos tres muda o
-- valor a pagar sem deixar rastro no modelo original. As demais colunas
-- (data, qualidade) sao auditadas tambem porque reclassificar a qualidade de
-- uma entrega e justamente a forma mais discreta de alterar o preco pactuado.
-- ---------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_entrega_auditoria_update;
DELIMITER $$
CREATE TRIGGER trg_entrega_auditoria_update
AFTER UPDATE ON entrega
FOR EACH ROW
BEGIN
    DECLARE v_chave VARCHAR(80);
    SET v_chave = CONCAT('id_entrega=', OLD.id_entrega);

    IF NOT (NEW.quantidade <=> OLD.quantidade) THEN
        INSERT INTO auditoria (tabela, operacao, chave_registro, campo,
                               valor_anterior, valor_novo, usuario)
        VALUES ('entrega','UPDATE',v_chave,'quantidade',
                OLD.quantidade, NEW.quantidade, SESSION_USER());
    END IF;

    IF NOT (NEW.preco_unitario_kg <=> OLD.preco_unitario_kg) THEN
        INSERT INTO auditoria (tabela, operacao, chave_registro, campo,
                               valor_anterior, valor_novo, usuario)
        VALUES ('entrega','UPDATE',v_chave,'preco_unitario_kg',
                OLD.preco_unitario_kg, NEW.preco_unitario_kg, SESSION_USER());
    END IF;

    IF NOT (NEW.status <=> OLD.status) THEN
        INSERT INTO auditoria (tabela, operacao, chave_registro, campo,
                               valor_anterior, valor_novo, usuario)
        VALUES ('entrega','UPDATE',v_chave,'status',
                OLD.status, NEW.status, SESSION_USER());
    END IF;

    IF NOT (NEW.qualidade <=> OLD.qualidade) THEN
        INSERT INTO auditoria (tabela, operacao, chave_registro, campo,
                               valor_anterior, valor_novo, usuario)
        VALUES ('entrega','UPDATE',v_chave,'qualidade',
                OLD.qualidade, NEW.qualidade, SESSION_USER());
    END IF;

    IF NOT (NEW.data_entrega <=> OLD.data_entrega) THEN
        INSERT INTO auditoria (tabela, operacao, chave_registro, campo,
                               valor_anterior, valor_novo, usuario)
        VALUES ('entrega','UPDATE',v_chave,'data_entrega',
                OLD.data_entrega, NEW.data_entrega, SESSION_USER());
    END IF;
END$$
DELIMITER ;

-- ---------------------------------------------------------------------------
-- GATILHO 2 - prestacao_contas (AFTER UPDATE)
--
-- Por que auditar prestacao_contas: e o fechamento financeiro por associado e
-- safra, o numero que o associado recebe. O CHECK ck_prestacao_saldo garante a
-- coerencia aritmetica (saldo = bruto - descontos), mas nao impede que alguem
-- aumente desconto e reduza saldo de forma coerente e silenciosa. O gatilho
-- cobre exatamente essa lacuna: a restricao protege a consistencia, a auditoria
-- protege a rastreabilidade.
-- ---------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_prestacao_auditoria_update;
DELIMITER $$
CREATE TRIGGER trg_prestacao_auditoria_update
AFTER UPDATE ON prestacao_contas
FOR EACH ROW
BEGIN
    DECLARE v_chave VARCHAR(80);
    SET v_chave = CONCAT('id_prestacao=', OLD.id_prestacao);

    IF NOT (NEW.total_bruto <=> OLD.total_bruto) THEN
        INSERT INTO auditoria (tabela, operacao, chave_registro, campo,
                               valor_anterior, valor_novo, usuario)
        VALUES ('prestacao_contas','UPDATE',v_chave,'total_bruto',
                OLD.total_bruto, NEW.total_bruto, SESSION_USER());
    END IF;

    IF NOT (NEW.total_descontos <=> OLD.total_descontos) THEN
        INSERT INTO auditoria (tabela, operacao, chave_registro, campo,
                               valor_anterior, valor_novo, usuario)
        VALUES ('prestacao_contas','UPDATE',v_chave,'total_descontos',
                OLD.total_descontos, NEW.total_descontos, SESSION_USER());
    END IF;

    IF NOT (NEW.saldo <=> OLD.saldo) THEN
        INSERT INTO auditoria (tabela, operacao, chave_registro, campo,
                               valor_anterior, valor_novo, usuario)
        VALUES ('prestacao_contas','UPDATE',v_chave,'saldo',
                OLD.saldo, NEW.saldo, SESSION_USER());
    END IF;

    IF NOT (NEW.status <=> OLD.status) THEN
        INSERT INTO auditoria (tabela, operacao, chave_registro, campo,
                               valor_anterior, valor_novo, usuario)
        VALUES ('prestacao_contas','UPDATE',v_chave,'status',
                OLD.status, NEW.status, SESSION_USER());
    END IF;
END$$
DELIMITER ;
