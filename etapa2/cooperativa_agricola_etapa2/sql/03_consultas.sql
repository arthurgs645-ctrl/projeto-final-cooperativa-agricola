-- Projeto Final - Laboratório de Banco de Dados 2026/2
-- A8 - 15 consultas de verificação
USE cooperativa_agricola;

-- ============================================================
-- CONSULTAS BÁSICAS (1 a 5)
-- ============================================================

-- 1. Pergunta de negócio: quais associados estão ativos e qual sua matrícula?
SELECT id_associado, matricula, nome
FROM associado
WHERE status = 'ATIVO'
ORDER BY nome;

-- 2. Pergunta de negócio: quais propriedades pertencem a municípios cujo nome contém "Bras"?
SELECT id_propriedade, nome, municipio, area_hectares
FROM propriedade
WHERE municipio LIKE '%Bras%'
ORDER BY area_hectares DESC;

-- 3. Pergunta de negócio: quais propriedades possuem área entre 150 e 300 hectares?
SELECT id_propriedade, nome, area_hectares, municipio
FROM propriedade
WHERE area_hectares BETWEEN 150 AND 300
ORDER BY area_hectares;

-- 4. Pergunta de negócio: quais culturas pertencem às categorias de grãos ou fibra?
SELECT id_cultura, nome, categoria, unidade_medida
FROM cultura
WHERE categoria IN ('Grão', 'Fibra')
ORDER BY nome;

-- 5. Pergunta de negócio: quais associados não possuem indicador cadastrado?
SELECT id_associado, matricula, nome
FROM associado
WHERE id_associado_indicador IS NULL
ORDER BY id_associado;

-- ============================================================
-- JUNÇÕES E AGREGAÇÃO (6 a 10)
-- ============================================================

-- 6. Pergunta de negócio: quanto foi planejado em lotes por associado?
-- Usa quatro tabelas: associado, propriedade, lote e safra.
SELECT a.id_associado,
       a.nome AS associado,
       SUM(l.quantidade_planejada) AS quantidade_planejada
FROM associado a
JOIN propriedade p ON p.id_associado = a.id_associado
JOIN lote l ON l.id_propriedade = p.id_propriedade
JOIN safra s ON s.id_safra = l.id_safra
GROUP BY a.id_associado, a.nome
ORDER BY quantidade_planejada DESC;

-- 7. Pergunta de negócio: quais associados ainda não possuem propriedade cadastrada?
-- LEFT JOIN permite localizar ausência de relacionamento.
SELECT a.id_associado, a.nome, p.id_propriedade, p.nome AS propriedade
FROM associado a
LEFT JOIN propriedade p ON p.id_associado = a.id_associado
ORDER BY a.nome;

-- 8. Pergunta de negócio: quais culturas receberam mais de 500 kg em entregas?
SELECT c.id_cultura,
       c.nome,
       SUM(e.quantidade) AS quantidade_entregue,
       COUNT(e.id_entrega) AS qtd_entregas
FROM cultura c
JOIN lote l ON l.id_cultura = c.id_cultura
JOIN entrega e ON e.id_safra = l.id_safra AND e.numero_lote = l.numero_lote
WHERE e.status = 'RECEBIDA'
GROUP BY c.id_cultura, c.nome
HAVING SUM(e.quantidade) > 500
ORDER BY quantidade_entregue DESC;

-- 9. Pergunta de negócio: qual a meta de cada cultura nas safras em andamento?
SELECT s.descricao AS safra,
       c.nome AS cultura,
       sc.meta_kg,
       sc.preco_base_kg
FROM safra s
JOIN safra_cultura sc ON sc.id_safra = s.id_safra
JOIN cultura c ON c.id_cultura = sc.id_cultura
WHERE s.status = 'EM_ANDAMENTO'
ORDER BY s.descricao, c.nome;

-- 10. Pergunta de negócio: qual é o saldo financeiro consolidado por prestação de contas?
SELECT pc.id_prestacao,
       a.nome AS associado,
       s.descricao AS safra,
       SUM(CASE WHEN mf.tipo = 'CREDITO' THEN mf.valor ELSE 0 END) AS creditos,
       SUM(CASE WHEN mf.tipo = 'DEBITO' THEN mf.valor ELSE 0 END) AS debitos,
       SUM(CASE WHEN mf.tipo = 'CREDITO' THEN mf.valor ELSE -mf.valor END) AS saldo_movimentado
FROM prestacao_contas pc
JOIN associado a ON a.id_associado = pc.id_associado
JOIN safra s ON s.id_safra = pc.id_safra
LEFT JOIN movimento_financeiro mf ON mf.id_prestacao = pc.id_prestacao
GROUP BY pc.id_prestacao, a.nome, s.descricao
ORDER BY saldo_movimentado DESC;

-- ============================================================
-- CONSULTAS AVANÇADAS (11 a 15)
-- ============================================================

-- 11. Pergunta de negócio: quais lotes foram planejados acima da média
-- dos lotes da mesma cultura?
SELECT l.id_safra,
       l.numero_lote,
       c.nome AS cultura,
       l.quantidade_planejada
FROM lote l
JOIN cultura c ON c.id_cultura = l.id_cultura
WHERE l.quantidade_planejada >
      (SELECT AVG(l2.quantidade_planejada)
       FROM lote l2
       WHERE l2.id_cultura = l.id_cultura)
ORDER BY l.quantidade_planejada DESC;

-- 12. Pergunta de negócio: quais associados possuem pelo menos uma
-- entrega recebida em alguma safra em andamento?
SELECT a.id_associado, a.nome
FROM associado a
WHERE EXISTS (
    SELECT 1
    FROM propriedade p
    JOIN lote l ON l.id_propriedade = p.id_propriedade
    JOIN entrega e ON e.id_safra = l.id_safra AND e.numero_lote = l.numero_lote
    JOIN safra s ON s.id_safra = l.id_safra
    WHERE p.id_associado = a.id_associado
      AND e.status = 'RECEBIDA'
      AND s.status = 'EM_ANDAMENTO'
)
ORDER BY a.nome;

-- 13. Pergunta de negócio não trivial: quais lotes já entregaram menos
-- de 50% da quantidade planejada, considerando somente lotes com entrega?
SELECT l.id_safra,
       l.numero_lote,
       c.nome AS cultura,
       l.quantidade_planejada,
       COALESCE(SUM(e.quantidade),0) AS quantidade_entregue,
       ROUND(COALESCE(SUM(e.quantidade),0) / l.quantidade_planejada * 100, 2) AS percentual_entregue,
       SUM(CASE WHEN e.data_entrega < s.data_inicio OR e.data_entrega > s.data_fim THEN 1 ELSE 0 END) AS entregas_fora_periodo
FROM lote l
JOIN safra s ON s.id_safra = l.id_safra
JOIN cultura c ON c.id_cultura = l.id_cultura
LEFT JOIN entrega e
  ON e.id_safra = l.id_safra
 AND e.numero_lote = l.numero_lote
 AND e.status = 'RECEBIDA'
GROUP BY l.id_safra, l.numero_lote, c.nome, l.quantidade_planejada
HAVING COALESCE(SUM(e.quantidade),0) > 0
   AND COALESCE(SUM(e.quantidade),0) < l.quantidade_planejada * 0.50
ORDER BY percentual_entregue;

-- 14. Pergunta de negócio: qual é a situação mais recente registrada
-- no histórico de cada associado?
SELECT a.id_associado,
       a.nome,
       h.situacao,
       h.data_inicio
FROM associado a
JOIN historico_associado h ON h.id_associado = a.id_associado
WHERE h.data_inicio = (
    SELECT MAX(h2.data_inicio)
    FROM historico_associado h2
    WHERE h2.id_associado = h.id_associado
)
ORDER BY a.nome;

-- 15. Pergunta de negócio não trivial: para cada cultura de safra em
-- andamento, compare a quantidade entregue com a meta cadastrada.
WITH entregas AS (
    SELECT l.id_safra,
           l.id_cultura,
           SUM(e.quantidade) AS quantidade_entregue
    FROM lote l
    JOIN entrega e
      ON e.id_safra = l.id_safra
     AND e.numero_lote = l.numero_lote
    WHERE e.status = 'RECEBIDA'
    GROUP BY l.id_safra, l.id_cultura
)
SELECT s.descricao AS safra,
       c.nome AS cultura,
       sc.meta_kg,
       COALESCE(en.quantidade_entregue,0) AS quantidade_entregue,
       ROUND(COALESCE(en.quantidade_entregue,0) / sc.meta_kg * 100, 2) AS percentual_da_meta
FROM safra s
JOIN safra_cultura sc ON sc.id_safra = s.id_safra
JOIN cultura c ON c.id_cultura = sc.id_cultura
LEFT JOIN entregas en
       ON en.id_safra = sc.id_safra
      AND en.id_cultura = sc.id_cultura
WHERE s.status = 'EM_ANDAMENTO'
ORDER BY percentual_da_meta DESC;
