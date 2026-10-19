-- Projeto Final - Laboratorio de Banco de Dados 2026/2
-- Tema: Cooperativa Agricola - Etapa 2
-- B4 - Indices criados no estudo de otimizacao
-- Autores: Artur Gabriel Queiroz de Morais; Arthur Goncalves Silva;
-- Arthur Marques Cipriano; Arthur Melo Mesquita Mitrovich; Fabricio Nogueira de Brito

-- Este arquivo consolida os indices definidos a partir do estudo documentado em
-- docs/B4_otimizacao.md. A medicao completa (plano antes, plano depois e tempo)
-- esta em experimentos/resultados/B4_explain.txt.

USE cooperativa_agricola;

-- ---------------------------------------------------------------------------
-- CONSULTA 1 - Janela de recebimento
-- "Quanto foi recebido entre duas datas?" E a consulta que abre a tela de
-- conferencia diaria do patio e a mais executada do sistema.
--
-- Ordem das colunas: data_entrega primeiro porque e o predicado de FAIXA e
-- define o intervalo a percorrer no indice; status depois, para filtrar dentro
-- da faixa sem voltar a tabela. Invertendo a ordem, o indice so poderia ser
-- usado ate a igualdade de status e a faixa de data viraria filtro residual.
-- As colunas quantidade e preco entram para tornar o indice COBRIDOR: o plano
-- resolve a agregacao sem nenhum acesso a tabela base.
-- ---------------------------------------------------------------------------
CREATE INDEX idx_entrega_data_status_valor
    ON entrega (data_entrega, status, quantidade, preco_unitario_kg);

-- ---------------------------------------------------------------------------
-- CONSULTA 3 - Classificacao por qualidade e preco
-- "Quais entregas de qualidade X sairam acima de determinado preco?" Usada na
-- conferencia de precos pagos por classificacao.
--
-- Ordem das colunas: qualidade primeiro (predicado de IGUALDADE), preco depois
-- (predicado de FAIXA). Esta e a regra geral: igualdade antes de faixa. Com a
-- ordem invertida o indice seria percorrido pela faixa de preco e a qualidade
-- viraria filtro linha a linha.
-- ---------------------------------------------------------------------------
CREATE INDEX idx_entrega_qualidade_preco
    ON entrega (qualidade, preco_unitario_kg);

-- ---------------------------------------------------------------------------
-- CONSULTA 2 - Contagem por status: a hipotese da equipe estava ERRADA
--
-- Nossa previsao era que este indice seria inutil. O raciocinio parecia solido:
-- 160.355 das 200.200 linhas tem status = 'RECEBIDA', ou seja, 80% da tabela.
-- Um indice que aponta para 80% das linhas normalmente e ignorado pelo
-- otimizador, porque o acesso aleatorio a tabela sairia mais caro que ler tudo
-- em sequencia.
--
-- A medicao desmentiu a previsao: 239,3 ms -> 118,9 ms (queda de 50%), e o
-- tempo do servidor no EXPLAIN ANALYZE caiu de 312 ms para 140 ms.
--
-- O motivo do ganho nao e seletividade, e LARGURA. A consulta e COUNT(*) com
-- filtro apenas em status, entao o indice e COBRIDOR: o MySQL responde
-- percorrendo apenas a entrada do indice secundario, que guarda status mais o
-- ponteiro da chave primaria, sem tocar na tabela. Como a linha completa de
-- entrega tem oito colunas, percorrer o indice estreito le muito menos paginas
-- do que percorrer o indice agrupado. O plano confirma: passou de
-- "covering index skip scan" para "covering index lookup".
--
-- A licao que levamos: seletividade baixa afasta o indice quando ele obriga a
-- voltar na tabela. Quando o indice cobre a consulta inteira, ele continua
-- valendo a pena mesmo com seletividade ruim.
--
-- O indice foi MANTIDO por causa do resultado medido.
-- ---------------------------------------------------------------------------
CREATE INDEX idx_entrega_status ON entrega (status);
