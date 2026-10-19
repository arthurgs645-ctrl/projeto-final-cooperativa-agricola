-- Projeto Final - Laboratorio de Banco de Dados 2026/2
-- Tema: Cooperativa Agricola - Etapa 2
-- RESPOSTA A DEVOLUTIVA DA ETAPA 1, criterio C3
-- Autores: Artur Gabriel Queiroz de Morais; Arthur Goncalves Silva;
-- Arthur Marques Cipriano; Arthur Melo Mesquita Mitrovich; Fabricio Nogueira de Brito

-- ---------------------------------------------------------------------------
-- A DEVOLUTIVA DISSE:
--
--   "considere reforcar no banco o que hoje fica so em consulta
--    (autoindicacao, totalidade e disjuncao PF/PJ, cronologia do historico)"
--
-- Na Etapa 1, quatro regras de negocio foram documentadas mas verificadas
-- apenas por consulta, porque nenhuma delas cabe em CHECK: o CHECK do MySQL
-- nao pode consultar outra tabela nem comparar com outras linhas da mesma
-- tabela. A alternativa correta e o GATILHO, que executa dentro da mesma
-- transacao do comando e pode abortar a operacao com SIGNAL.
--
-- Este script implementa as quatro. A partir daqui, as regras valem para
-- qualquer caminho de escrita - aplicacao, script ou alguem digitando no
-- Workbench -, e nao apenas para quem lembrar de rodar a consulta de
-- verificacao.
-- ---------------------------------------------------------------------------

USE cooperativa_agricola;

-- ===========================================================================
-- REGRA 1 - AUTOINDICACAO (RN03)
-- "o indicador e opcional e nao pode formar uma autoindicacao"
--
-- PRIMEIRA TENTATIVA, QUE FALHOU - e vale registrar o motivo:
--
--   ALTER TABLE associado ADD CONSTRAINT ck_associado_sem_autoindicacao
--       CHECK (id_associado_indicador IS NULL
--              OR id_associado_indicador <> id_associado);
--
--   ERROR 3823 (HY000): Column 'id_associado_indicador' cannot be used in a
--   check constraint 'ck_associado_sem_autoindicacao': needed in a foreign key
--   constraint 'fk_associado_indicador' referential action.
--
-- A comparacao e entre duas colunas da MESMA linha, entao em principio caberia
-- num CHECK. O que o impede e outra coisa: a Etapa 1 declarou
-- fk_associado_indicador com ON DELETE SET NULL. Como essa acao referencial
-- pode alterar a coluna por iniciativa do proprio servidor, o MySQL recusa
-- qualquer CHECK sobre ela - do contrario, apagar um associado poderia deixar
-- uma linha violando o CHECK sem que ninguem tivesse escrito nela.
--
-- A licao, que vale para a resposta ao criterio C3 sobre justificar cada acao
-- referencial: a escolha de ON DELETE SET NULL nao e neutra. Ela comprou a
-- comodidade de nao perder o associado quando seu indicador sai do quadro, e
-- pagou com a impossibilidade de usar CHECK naquela coluna.
--
-- SOLUCAO ADOTADA: gatilho, que o servidor avalia apenas nas escritas feitas
-- por comando, e nao na propagacao da acao referencial.
-- ===========================================================================
DROP TRIGGER IF EXISTS trg_associado_autoindicacao_insert;
DELIMITER $$
CREATE TRIGGER trg_associado_autoindicacao_insert
BEFORE INSERT ON associado
FOR EACH ROW
BEGIN
    IF NEW.id_associado_indicador IS NOT NULL
       AND NEW.id_associado_indicador = NEW.id_associado THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT =
            'ck_associado_sem_autoindicacao: um associado nao pode indicar a si mesmo';
    END IF;
END$$
DELIMITER ;

-- ===========================================================================
-- REGRA 2 - DISJUNCAO E TOTALIDADE DA ESPECIALIZACAO (RN04/RN05)
-- "todo associado PF tem linha em associado_pf e nenhuma em associado_pj,
--  e vice-versa"
--
-- Por que gatilho e nao CHECK: a regra relaciona tres tabelas. O CHECK nao
-- enxerga associado_pf a partir de associado_pj.
--
-- DISJUNCAO: garantida nos dois gatilhos abaixo, que recusam a insercao de uma
-- especializacao incompativel com o tipo_pessoa declarado no supertipo.
--
-- TOTALIDADE: nao e imposta por gatilho de proposito. Exigir a linha filha no
-- momento do INSERT do pai tornaria impossivel inserir o associado, ja que a
-- filha depende da chave do pai que ainda nao existe. Em vez disso, a
-- totalidade e verificavel a qualquer momento pela visao vw_especializacao_
-- irregular, criada ao final deste script, que lista associados sem a linha
-- correspondente. Esta e uma limitacao real do modelo relacional sem
-- ASSERTION, e preferimos registra-la a fingir que esta resolvida.
-- ===========================================================================
DROP TRIGGER IF EXISTS trg_associado_pf_disjuncao;
DELIMITER $$
CREATE TRIGGER trg_associado_pf_disjuncao
BEFORE INSERT ON associado_pf
FOR EACH ROW
BEGIN
    DECLARE v_tipo CHAR(2);
    SELECT tipo_pessoa INTO v_tipo
      FROM associado WHERE id_associado = NEW.id_associado;

    IF v_tipo <> 'PF' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT =
            'ck_especializacao: associado declarado PJ nao pode ter dados de PF';
    END IF;

    IF EXISTS (SELECT 1 FROM associado_pj
                WHERE id_associado = NEW.id_associado) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT =
            'ck_especializacao: associado ja possui dados de PJ (disjuncao)';
    END IF;
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trg_associado_pj_disjuncao;
DELIMITER $$
CREATE TRIGGER trg_associado_pj_disjuncao
BEFORE INSERT ON associado_pj
FOR EACH ROW
BEGIN
    DECLARE v_tipo CHAR(2);
    SELECT tipo_pessoa INTO v_tipo
      FROM associado WHERE id_associado = NEW.id_associado;

    IF v_tipo <> 'PJ' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT =
            'ck_especializacao: associado declarado PF nao pode ter dados de PJ';
    END IF;

    IF EXISTS (SELECT 1 FROM associado_pf
                WHERE id_associado = NEW.id_associado) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT =
            'ck_especializacao: associado ja possui dados de PF (disjuncao)';
    END IF;
END$$
DELIMITER ;

-- Impede tambem a troca de tipo_pessoa em um associado que ja tem
-- especializacao gravada: mudar PF para PJ deixaria a linha filha orfa da
-- regra.
DROP TRIGGER IF EXISTS trg_associado_troca_tipo;
DELIMITER $$
CREATE TRIGGER trg_associado_troca_tipo
BEFORE UPDATE ON associado
FOR EACH ROW
BEGIN
    -- autoindicacao tambem na alteracao (ver REGRA 1)
    IF NEW.id_associado_indicador IS NOT NULL
       AND NEW.id_associado_indicador = NEW.id_associado THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT =
            'ck_associado_sem_autoindicacao: um associado nao pode indicar a si mesmo';
    END IF;

    IF NEW.tipo_pessoa <> OLD.tipo_pessoa THEN
        IF OLD.tipo_pessoa = 'PF'
           AND EXISTS (SELECT 1 FROM associado_pf
                        WHERE id_associado = OLD.id_associado) THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT =
                'ck_especializacao: remova os dados de PF antes de mudar o tipo';
        END IF;
        IF OLD.tipo_pessoa = 'PJ'
           AND EXISTS (SELECT 1 FROM associado_pj
                        WHERE id_associado = OLD.id_associado) THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT =
                'ck_especializacao: remova os dados de PJ antes de mudar o tipo';
        END IF;
    END IF;
END$$
DELIMITER ;

-- ===========================================================================
-- REGRA 3 - CRONOLOGIA DO HISTORICO (RN15/RN17)
-- "o historico deve ser registrado em periodos cronologicos"
--
-- A Etapa 1 garantia por uq_historico_associado_inicio que nao ha duas linhas
-- com a mesma data de inicio para o mesmo associado, e por ck_historico_periodo
-- que data_fim >= data_inicio. Faltava o essencial: periodos do mesmo
-- associado NAO PODEM SE SOBREPOR, e so o ultimo periodo pode estar aberto
-- (data_fim NULL). Nenhuma das duas cabe em CHECK, porque dependem das OUTRAS
-- LINHAS da tabela.
-- ===========================================================================
DROP TRIGGER IF EXISTS trg_historico_cronologia_insert;
DELIMITER $$
CREATE TRIGGER trg_historico_cronologia_insert
BEFORE INSERT ON historico_associado
FOR EACH ROW
BEGIN
    -- sobreposicao: existe periodo do mesmo associado que cruza o novo?
    -- Dois intervalos [a1,a2] e [b1,b2] se sobrepoem quando a1 <= b2 e b1 <= a2.
    -- Periodo aberto (data_fim NULL) e tratado como indo ate o infinito.
    IF EXISTS (
        SELECT 1 FROM historico_associado h
         WHERE h.id_associado = NEW.id_associado
           AND NEW.data_inicio <= COALESCE(h.data_fim, '9999-12-31')
           AND h.data_inicio   <= COALESCE(NEW.data_fim, '9999-12-31')
    ) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT =
            'ck_historico_cronologia: o periodo informado se sobrepoe a outro ja registrado';
    END IF;

    -- so um periodo em aberto por associado
    IF NEW.data_fim IS NULL
       AND EXISTS (SELECT 1 FROM historico_associado h
                    WHERE h.id_associado = NEW.id_associado
                      AND h.data_fim IS NULL) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT =
            'ck_historico_cronologia: ja existe um periodo em aberto para este associado';
    END IF;
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS trg_historico_cronologia_update;
DELIMITER $$
CREATE TRIGGER trg_historico_cronologia_update
BEFORE UPDATE ON historico_associado
FOR EACH ROW
BEGIN
    IF EXISTS (
        SELECT 1 FROM historico_associado h
         WHERE h.id_associado = NEW.id_associado
           AND h.id_historico <> NEW.id_historico
           AND NEW.data_inicio <= COALESCE(h.data_fim, '9999-12-31')
           AND h.data_inicio   <= COALESCE(NEW.data_fim, '9999-12-31')
    ) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT =
            'ck_historico_cronologia: a alteracao faria o periodo se sobrepor a outro';
    END IF;
END$$
DELIMITER ;

-- ===========================================================================
-- REGRA 4 - ENTREGA DENTRO DO PERIODO DA SAFRA (RN20)
-- A Etapa 1 registrou explicitamente que esta regra "nao e implementada por
-- CHECK por envolver outra tabela". Com gatilho, ela passa a valer.
-- ===========================================================================
DROP TRIGGER IF EXISTS trg_entrega_periodo_safra;
DELIMITER $$
CREATE TRIGGER trg_entrega_periodo_safra
BEFORE INSERT ON entrega
FOR EACH ROW
BEGIN
    DECLARE v_inicio DATE;
    DECLARE v_fim DATE;

    SELECT s.data_inicio, s.data_fim INTO v_inicio, v_fim
      FROM safra s WHERE s.id_safra = NEW.id_safra;

    IF NEW.data_entrega < v_inicio OR NEW.data_entrega > v_fim THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT =
            'ck_entrega_periodo: a data da entrega esta fora do periodo da safra';
    END IF;
END$$
DELIMITER ;

-- ===========================================================================
-- VERIFICACAO DE TOTALIDADE
-- Lista associados cujo tipo declarado nao tem a especializacao correspondente.
-- Em um banco integro, esta visao devolve zero linhas.
-- ===========================================================================
DROP VIEW IF EXISTS vw_especializacao_irregular;
CREATE VIEW vw_especializacao_irregular AS
SELECT a.id_associado, a.matricula, a.nome, a.tipo_pessoa,
       CASE
           WHEN a.tipo_pessoa = 'PF' AND pf.id_associado IS NULL
               THEN 'declarado PF, sem linha em associado_pf'
           WHEN a.tipo_pessoa = 'PJ' AND pj.id_associado IS NULL
               THEN 'declarado PJ, sem linha em associado_pj'
           WHEN pf.id_associado IS NOT NULL AND pj.id_associado IS NOT NULL
               THEN 'possui as duas especializacoes (viola disjuncao)'
       END AS irregularidade
  FROM associado a
  LEFT JOIN associado_pf pf ON pf.id_associado = a.id_associado
  LEFT JOIN associado_pj pj ON pj.id_associado = a.id_associado
 WHERE (a.tipo_pessoa = 'PF' AND pf.id_associado IS NULL)
    OR (a.tipo_pessoa = 'PJ' AND pj.id_associado IS NULL)
    OR (pf.id_associado IS NOT NULL AND pj.id_associado IS NOT NULL);
