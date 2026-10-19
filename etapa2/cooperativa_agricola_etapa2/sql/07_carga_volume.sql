-- Projeto Final - Laboratorio de Banco de Dados 2026/2
-- Tema: Cooperativa Agricola - Etapa 2
-- B4 - Carga de volume para o estudo de desempenho
-- Autores: Artur Gabriel Queiroz de Morais; Arthur Goncalves Silva;
-- Arthur Marques Cipriano; Arthur Melo Mesquita Mitrovich; Fabricio Nogueira de Brito

-- ---------------------------------------------------------------------------
-- POR QUE ESTE SCRIPT EXISTE
--
-- A carga da Etapa 1 tem 160 entregas. Nesse volume, qualquer plano de execucao
-- e rapido e o otimizador do MySQL quase sempre escolhe varredura completa,
-- porque ler 160 linhas sequenciais custa menos do que percorrer um indice e
-- fazer acessos aleatorios a tabela. Medir ganho de indice ali produz numeros
-- sem significado: a variacao entre execucoes e maior que o efeito medido.
--
-- Este script eleva a tabela entrega a ~200 mil linhas, mantendo as mesmas
-- chaves estrangeiras e os mesmos dominios da Etapa 1, para que o estudo de
-- desempenho do B4 seja feito em um volume onde a escolha do plano importa.
--
-- O script e idempotente: apaga a carga sintetica anterior (id_entrega > 160)
-- antes de inserir.
-- ---------------------------------------------------------------------------

USE cooperativa_agricola;

SET SQL_SAFE_UPDATES = 0;
DELETE FROM entrega WHERE id_entrega > 160;
SET SQL_SAFE_UPDATES = 1;

-- Tabela auxiliar de numeros: 10^4 linhas a partir de digitos.
DROP TEMPORARY TABLE IF EXISTS tmp_numeros;
CREATE TEMPORARY TABLE tmp_numeros (n INT UNSIGNED NOT NULL PRIMARY KEY);

INSERT INTO tmp_numeros (n)
SELECT d4.d * 1000 + d3.d * 100 + d2.d * 10 + d1.d AS n
FROM (SELECT 0 d UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3
      UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6
      UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) d1
CROSS JOIN (SELECT 0 d UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3
      UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6
      UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) d2
CROSS JOIN (SELECT 0 d UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3
      UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6
      UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) d3
CROSS JOIN (SELECT 0 d UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3
      UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6
      UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) d4;

-- 120 lotes x 1667 repeticoes = 200.040 entregas sinteticas.
-- A data e distribuida dentro do periodo da safra do lote, respeitando a RN20.
INSERT INTO entrega (id_safra, numero_lote, data_entrega, quantidade,
                     qualidade, preco_unitario_kg, status)
SELECT
    l.id_safra,
    l.numero_lote,
    DATE_ADD(s.data_inicio,
             INTERVAL MOD(num.n * 7 + l.numero_lote,
                          GREATEST(DATEDIFF(s.data_fim, s.data_inicio), 1)) DAY),
    ROUND(50 + MOD(num.n * 13 + l.numero_lote * 7, 4950) + 0.5, 2),
    ELT(1 + MOD(num.n + l.numero_lote, 3), 'A', 'B', 'C'),
    ROUND(1.20 + MOD(num.n * 3 + l.numero_lote, 880) / 100, 2),
    ELT(1 + MOD(num.n, 10), 'RECEBIDA','RECEBIDA','RECEBIDA','RECEBIDA',
                            'RECEBIDA','RECEBIDA','RECEBIDA','RECEBIDA',
                            'PENDENTE','CANCELADA')
FROM lote l
JOIN safra s ON s.id_safra = l.id_safra
CROSS JOIN tmp_numeros num
WHERE num.n < 1667;

DROP TEMPORARY TABLE IF EXISTS tmp_numeros;

ANALYZE TABLE entrega;

SELECT COUNT(*) AS total_entregas,
       MIN(data_entrega) AS primeira,
       MAX(data_entrega) AS ultima
FROM entrega;
