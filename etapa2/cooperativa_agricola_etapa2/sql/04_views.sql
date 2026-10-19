-- Projeto Final - Laboratorio de Banco de Dados 2026/2
-- Tema: Cooperativa Agricola - Etapa 2
-- B1/B5 - Visoes: relatorio consolidado e restricao de colunas por perfil
-- Autores: Artur Gabriel Queiroz de Morais; Arthur Goncalves Silva;
-- Arthur Marques Cipriano; Arthur Melo Mesquita Mitrovich; Fabricio Nogueira de Brito

USE cooperativa_agricola;

-- ---------------------------------------------------------------------------
-- B1: visao que alimenta a tela de relatorio consolidado da aplicacao.
-- Consolida, por associado e safra, o que foi entregue e o que foi apurado
-- financeiramente. A tela nao monta esse SQL: ela so faz SELECT na visao.
-- ---------------------------------------------------------------------------
DROP VIEW IF EXISTS vw_relatorio_safra_associado;
CREATE VIEW vw_relatorio_safra_associado AS
SELECT
    s.id_safra,
    s.descricao                                   AS safra,
    s.status                                      AS status_safra,
    a.id_associado,
    a.matricula,
    a.nome                                        AS associado,
    a.tipo_pessoa,
    COUNT(DISTINCT l.numero_lote)                 AS lotes,
    COUNT(e.id_entrega)                           AS entregas,
    COALESCE(SUM(CASE WHEN e.status = 'RECEBIDA'
                      THEN e.quantidade END), 0)  AS kg_recebidos,
    COALESCE(SUM(CASE WHEN e.status = 'RECEBIDA'
                      THEN e.quantidade * e.preco_unitario_kg END), 0) AS valor_entregue,
    pc.total_bruto,
    pc.total_descontos,
    pc.saldo,
    pc.status                                     AS status_prestacao
FROM safra s
JOIN lote l              ON l.id_safra = s.id_safra
JOIN propriedade p       ON p.id_propriedade = l.id_propriedade
JOIN associado a         ON a.id_associado = p.id_associado
LEFT JOIN entrega e      ON e.id_safra = l.id_safra
                        AND e.numero_lote = l.numero_lote
LEFT JOIN prestacao_contas pc ON pc.id_associado = a.id_associado
                             AND pc.id_safra = s.id_safra
GROUP BY s.id_safra, s.descricao, s.status,
         a.id_associado, a.matricula, a.nome, a.tipo_pessoa,
         pc.total_bruto, pc.total_descontos, pc.saldo, pc.status;

-- ---------------------------------------------------------------------------
-- B5: visao de restricao de colunas.
-- O perfil de leitura nao enxerga CPF nem CNPJ. Em vez de conceder SELECT na
-- tabela associado_pf/associado_pj, concedemos SELECT apenas nesta visao, que
-- expoe o documento mascarado. Isso implementa menor privilegio no nivel de
-- coluna sem depender de GRANT por coluna em varias tabelas.
-- ---------------------------------------------------------------------------
DROP VIEW IF EXISTS vw_associado_publico;
CREATE VIEW vw_associado_publico AS
SELECT
    a.id_associado,
    a.matricula,
    a.nome,
    a.tipo_pessoa,
    a.status,
    CASE
        WHEN a.tipo_pessoa = 'PF'
            THEN CONCAT('***.***.', SUBSTRING(pf.cpf, 7, 3), '-**')
        ELSE CONCAT('**.***.', SUBSTRING(pj.cnpj, 6, 3), '/****-**')
    END AS documento_mascarado,
    pj.razao_social
FROM associado a
LEFT JOIN associado_pf pf ON pf.id_associado = a.id_associado
LEFT JOIN associado_pj pj ON pj.id_associado = a.id_associado;

-- ---------------------------------------------------------------------------
-- B5: visao de restricao de linhas.
-- O perfil operacional so precisa enxergar o que esta em andamento. Safras
-- encerradas e lotes encerrados ficam fora.
-- ---------------------------------------------------------------------------
DROP VIEW IF EXISTS vw_lote_em_operacao;
CREATE VIEW vw_lote_em_operacao AS
SELECT
    l.id_safra,
    l.numero_lote,
    s.descricao        AS safra,
    p.nome             AS propriedade,
    c.nome             AS cultura,
    l.quantidade_planejada,
    l.status
FROM lote l
JOIN safra s       ON s.id_safra = l.id_safra
JOIN propriedade p ON p.id_propriedade = l.id_propriedade
JOIN cultura c     ON c.id_cultura = l.id_cultura
WHERE s.status <> 'ENCERRADA'
  AND l.status <> 'ENCERRADO';
