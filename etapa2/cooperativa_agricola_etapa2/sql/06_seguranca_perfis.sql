-- Projeto Final - Laboratorio de Banco de Dados 2026/2
-- Tema: Cooperativa Agricola - Etapa 2
-- B5 - Seguranca e controle de acesso
-- Autores: Artur Gabriel Queiroz de Morais; Arthur Goncalves Silva;
-- Arthur Marques Cipriano; Arthur Melo Mesquita Mitrovich; Fabricio Nogueira de Brito

USE cooperativa_agricola;

-- ---------------------------------------------------------------------------
-- Tabela de usuarios da aplicacao
--
-- A autenticacao da aplicacao NAO usa usuarios do MySQL. Sao duas camadas
-- diferentes: o usuario da aplicacao (linha nesta tabela) e o usuario do banco
-- (conta MySQL que a aplicacao usa para conectar, escolhida conforme o perfil).
--
-- A senha nunca e gravada em texto claro. Guardamos PBKDF2-HMAC-SHA256 com sal
-- aleatorio de 16 bytes por usuario e 260.000 iteracoes. O sal por usuario
-- impede que duas pessoas com a mesma senha tenham o mesmo hash, e o custo de
-- iteracao encarece ataque de forca bruta.
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS usuario_app;
CREATE TABLE usuario_app (
    id_usuario   INT UNSIGNED NOT NULL AUTO_INCREMENT,
    login        VARCHAR(40)  NOT NULL,
    nome         VARCHAR(120) NOT NULL,
    perfil       VARCHAR(20)  NOT NULL,
    senha_hash   VARCHAR(255) NOT NULL,
    senha_sal    VARCHAR(64)  NOT NULL,
    algoritmo    VARCHAR(40)  NOT NULL DEFAULT 'pbkdf2_sha256$260000',
    ativo        TINYINT(1)   NOT NULL DEFAULT 1,
    criado_em    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_usuario_app PRIMARY KEY (id_usuario),
    CONSTRAINT uq_usuario_app_login UNIQUE (login),
    CONSTRAINT ck_usuario_app_perfil
        CHECK (perfil IN ('LEITURA','OPERACIONAL','FINANCEIRO'))
);

-- ---------------------------------------------------------------------------
-- PERFIS DE ACESSO (papeis do MySQL 8)
--
-- Tres perfis, cada um com o minimo necessario para a sua funcao.
-- ---------------------------------------------------------------------------
DROP ROLE IF EXISTS coop_leitura, coop_operacional, coop_financeiro;
CREATE ROLE coop_leitura, coop_operacional, coop_financeiro;

-- --- PERFIL 1: LEITURA -------------------------------------------------------
-- Consulta institucional: conselho fiscal, auditoria externa, analista que
-- monta indicador. Le a operacao inteira, mas nao escreve nada e nao enxerga
-- dois conjuntos de dados:
--
--   1. documento pessoal (CPF/CNPJ) - so pela visao mascarada;
--   2. valores financeiros por associado nas tabelas base - so pela visao
--      consolidada vw_relatorio_safra_associado.
--
-- Sobre o item 2: a visao funciona para este perfil mesmo sem GRANT em
-- prestacao_contas porque, por padrao, a visao do MySQL e SQL SECURITY DEFINER
-- - ela executa com o privilegio de quem a criou, nao de quem a consulta. E
-- exatamente esse mecanismo que permite liberar o agregado sem liberar a linha.
GRANT SELECT ON cooperativa_agricola.vw_associado_publico         TO coop_leitura;
GRANT SELECT ON cooperativa_agricola.vw_relatorio_safra_associado TO coop_leitura;
GRANT SELECT ON cooperativa_agricola.vw_lote_em_operacao          TO coop_leitura;
GRANT SELECT ON cooperativa_agricola.associado                    TO coop_leitura;
GRANT SELECT ON cooperativa_agricola.propriedade                  TO coop_leitura;
GRANT SELECT ON cooperativa_agricola.cultura                      TO coop_leitura;
GRANT SELECT ON cooperativa_agricola.safra                        TO coop_leitura;
GRANT SELECT ON cooperativa_agricola.safra_cultura                TO coop_leitura;
GRANT SELECT ON cooperativa_agricola.lote                         TO coop_leitura;
GRANT SELECT ON cooperativa_agricola.entrega                      TO coop_leitura;
-- Deliberadamente AUSENTES: associado_pf, associado_pj (documento pessoal),
-- prestacao_contas, movimento_financeiro (financeiro por associado),
-- historico_associado e auditoria.

-- --- PERFIL 2: OPERACIONAL ---------------------------------------------------
-- Secretaria e patio da cooperativa: mantem os cadastros (associado,
-- propriedade, cultura), planeja lotes e recebe entregas.
-- Nao tem nenhum privilegio sobre as tabelas financeiras.
GRANT SELECT, INSERT, UPDATE, DELETE ON cooperativa_agricola.associado    TO coop_operacional;
GRANT SELECT, INSERT, UPDATE, DELETE ON cooperativa_agricola.associado_pf TO coop_operacional;
GRANT SELECT, INSERT, UPDATE, DELETE ON cooperativa_agricola.associado_pj TO coop_operacional;
GRANT SELECT, INSERT, UPDATE, DELETE ON cooperativa_agricola.propriedade  TO coop_operacional;
GRANT SELECT, INSERT, UPDATE, DELETE ON cooperativa_agricola.cultura      TO coop_operacional;
GRANT SELECT, INSERT, UPDATE, DELETE ON cooperativa_agricola.lote         TO coop_operacional;
GRANT SELECT, INSERT, UPDATE         ON cooperativa_agricola.entrega      TO coop_operacional;
GRANT SELECT ON cooperativa_agricola.safra                    TO coop_operacional;
GRANT SELECT ON cooperativa_agricola.safra_cultura            TO coop_operacional;
GRANT SELECT ON cooperativa_agricola.historico_associado      TO coop_operacional;
GRANT SELECT ON cooperativa_agricola.vw_associado_publico     TO coop_operacional;
GRANT SELECT ON cooperativa_agricola.vw_lote_em_operacao      TO coop_operacional;
-- Note a ausencia deliberada de DELETE em entrega. Estorno de entrega e feito
-- mudando o status para CANCELADA, nunca apagando a linha: a entrega e o
-- documento que origina o pagamento e precisa permanecer rastreavel. Esta e
-- uma decisao de modelagem, nao um esquecimento.

-- --- PERFIL 3: FINANCEIRO ----------------------------------------------------
-- Fecha prestacao de contas e lanca movimentos. Le a operacao, mas nao a altera.
GRANT SELECT, INSERT, UPDATE ON cooperativa_agricola.prestacao_contas      TO coop_financeiro;
GRANT SELECT, INSERT, UPDATE ON cooperativa_agricola.movimento_financeiro  TO coop_financeiro;
-- A apuracao do valor bruto percorre entrega -> lote -> propriedade ->
-- associado, entao o perfil precisa de leitura nas quatro. propriedade entra
-- aqui por ser o elo que liga o lote ao dono da producao; sem ela a transacao
-- de fechamento nao consegue saber de quem e a entrega.
GRANT SELECT ON cooperativa_agricola.entrega                      TO coop_financeiro;
GRANT SELECT ON cooperativa_agricola.lote                         TO coop_financeiro;
GRANT SELECT ON cooperativa_agricola.propriedade                  TO coop_financeiro;
GRANT SELECT ON cooperativa_agricola.associado                    TO coop_financeiro;
GRANT SELECT ON cooperativa_agricola.safra                        TO coop_financeiro;
GRANT SELECT ON cooperativa_agricola.vw_relatorio_safra_associado TO coop_financeiro;
GRANT SELECT ON cooperativa_agricola.auditoria                    TO coop_financeiro;

-- ---------------------------------------------------------------------------
-- DEMONSTRACAO DE REVOKE
--
-- Durante o desenvolvimento, o perfil financeiro havia recebido UPDATE em
-- entrega para "corrigir precos". Isso viola a separacao de funcoes: quem
-- fecha o pagamento nao deve poder alterar o documento que origina o valor.
-- O GRANT abaixo registra o estado anterior e o REVOKE o corrige.
-- ---------------------------------------------------------------------------
GRANT UPDATE ON cooperativa_agricola.entrega TO coop_financeiro;
REVOKE UPDATE ON cooperativa_agricola.entrega FROM coop_financeiro;

-- ---------------------------------------------------------------------------
-- CONTAS DE BANCO USADAS PELA APLICACAO
--
-- Uma conta por perfil. A aplicacao escolhe a conexao conforme o perfil do
-- usuario autenticado, de modo que o proprio SGBD recusa uma operacao fora do
-- perfil, mesmo que houvesse falha na checagem da aplicacao.
--
-- As senhas abaixo sao de ambiente academico local e estao no .env, fora do
-- versionamento (ver .gitignore e .env.example).
-- ---------------------------------------------------------------------------
DROP USER IF EXISTS 'app_leitura'@'localhost';
DROP USER IF EXISTS 'app_operacional'@'localhost';
DROP USER IF EXISTS 'app_financeiro'@'localhost';

CREATE USER 'app_leitura'@'localhost'     IDENTIFIED BY 'Leitura#2026';
CREATE USER 'app_operacional'@'localhost' IDENTIFIED BY 'Operacao#2026';
CREATE USER 'app_financeiro'@'localhost'  IDENTIFIED BY 'Financeiro#2026';

GRANT coop_leitura     TO 'app_leitura'@'localhost';
GRANT coop_operacional TO 'app_operacional'@'localhost';
GRANT coop_financeiro  TO 'app_financeiro'@'localhost';

-- O papel precisa estar ativo na conexao; sem isto o usuario conecta sem
-- nenhum privilegio efetivo.
SET DEFAULT ROLE ALL TO 'app_leitura'@'localhost';
SET DEFAULT ROLE ALL TO 'app_operacional'@'localhost';
SET DEFAULT ROLE ALL TO 'app_financeiro'@'localhost';

-- Todas as contas da aplicacao precisam ler usuario_app para autenticar.
GRANT SELECT ON cooperativa_agricola.usuario_app TO 'app_leitura'@'localhost';
GRANT SELECT ON cooperativa_agricola.usuario_app TO 'app_operacional'@'localhost';
GRANT SELECT ON cooperativa_agricola.usuario_app TO 'app_financeiro'@'localhost';

FLUSH PRIVILEGES;
