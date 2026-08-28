-- =============================================================================
-- VALIDACAO E QUALIDADE DO DATA WAREHOUSE
--
-- Consultas de verificacao executadas apos cada ciclo de ETL. Cobrem
-- integridade referencial, granularidade, consistencia das metricas, saude
-- do SCD Tipo 2 e comprovacao do comportamento incremental.
--
-- Execucao:
--   docker exec -i dw_adventureworks_pg psql -U dw_user -d dw_adventureworks \
--       < sql/99_validacao.sql
-- =============================================================================


-- #############################################################################
-- 1. VOLUMETRIA DAS TABELAS DO MODELO
-- #############################################################################

SELECT 'dw.dim_tempo'         AS tabela, count(*) AS qt_linhas FROM dw.dim_tempo
UNION ALL SELECT 'dw.dim_produto (todas as versoes)', count(*) FROM dw.dim_produto
UNION ALL SELECT 'dw.dim_produto (versao corrente)', count(*) FROM dw.dim_produto WHERE fl_corrente
UNION ALL SELECT 'dw.dim_cliente',       count(*) FROM dw.dim_cliente
UNION ALL SELECT 'dw.dim_funcionario',   count(*) FROM dw.dim_funcionario
UNION ALL SELECT 'dw.dim_territorio',    count(*) FROM dw.dim_territorio
UNION ALL SELECT 'dw.dim_geografia',     count(*) FROM dw.dim_geografia
UNION ALL SELECT 'dw.dim_fornecedor',    count(*) FROM dw.dim_fornecedor
UNION ALL SELECT 'dw.dim_promocao',      count(*) FROM dw.dim_promocao
UNION ALL SELECT 'dw.dim_metodo_envio',  count(*) FROM dw.dim_metodo_envio
UNION ALL SELECT 'dw.dim_canal_venda',   count(*) FROM dw.dim_canal_venda
UNION ALL SELECT 'dw.dim_status_pedido', count(*) FROM dw.dim_status_pedido
UNION ALL SELECT 'dw.fato_vendas',       count(*) FROM dw.fato_vendas
UNION ALL SELECT 'dw.fato_compras',      count(*) FROM dw.fato_compras
ORDER BY tabela;


-- #############################################################################
-- 2. INTEGRIDADE E GRANULARIDADE
--
-- Espera-se zero em todas as linhas. As chaves estrangeiras sao garantidas
-- pelo banco; o que se verifica aqui e a QUALIDADE do relacionamento, ou seja,
-- quantos fatos precisaram recorrer ao membro "Nao Informado" (-1).
-- #############################################################################

SELECT 'fato_vendas: chave de negocio duplicada' AS verificacao,
       count(*) AS qt_ocorrencias
  FROM (SELECT id_item_venda FROM dw.fato_vendas
         GROUP BY id_item_venda HAVING count(*) > 1) AS d
UNION ALL
SELECT 'fato_compras: chave de negocio duplicada',
       count(*)
  FROM (SELECT id_item_compra FROM dw.fato_compras
         GROUP BY id_item_compra HAVING count(*) > 1) AS d
UNION ALL
SELECT 'fato_vendas: receita liquida negativa',
       count(*) FROM dw.fato_vendas WHERE vl_liquido < 0
UNION ALL
SELECT 'fato_vendas: quantidade nao positiva',
       count(*) FROM dw.fato_vendas WHERE qt_vendida <= 0
UNION ALL
SELECT 'fato_vendas: liquido diferente de bruto - desconto',
       count(*) FROM dw.fato_vendas
       WHERE ROUND(vl_bruto - vl_desconto, 2) <> ROUND(vl_liquido, 2)
UNION ALL
SELECT 'fato_vendas: margem diferente de liquido - custo',
       count(*) FROM dw.fato_vendas
       WHERE ROUND(vl_liquido - vl_custo_total, 2) <> ROUND(vl_margem_bruta, 2)
UNION ALL
SELECT 'dim_produto: mais de uma versao corrente por produto',
       count(*) FROM (SELECT id_produto FROM dw.dim_produto
                       WHERE fl_corrente GROUP BY id_produto HAVING count(*) > 1) AS d
UNION ALL
SELECT 'dim_produto: intervalo de vigencia invertido',
       count(*) FROM dw.dim_produto WHERE dt_fim_validade < dt_inicio_validade;


-- #############################################################################
-- 3. USO DO MEMBRO "NAO INFORMADO" (-1) NA FATO DE VENDAS
--
-- Nao e um erro: revela onde o OLTP legitimamente nao informa a chave.
-- No AdventureWorks, todo pedido pela internet nasce sem vendedor associado,
-- e pedidos ainda nao expedidos nao possuem data de envio.
-- #############################################################################

SELECT
    count(*)                                              AS qt_total_linhas,
    count(*) FILTER (WHERE sk_produto  = -1)              AS sem_produto,
    count(*) FILTER (WHERE sk_cliente  = -1)              AS sem_cliente,
    count(*) FILTER (WHERE sk_vendedor = -1)              AS sem_vendedor,
    count(*) FILTER (WHERE sk_territorio = -1)            AS sem_territorio,
    count(*) FILTER (WHERE sk_geografia_entrega = -1)     AS sem_geografia,
    count(*) FILTER (WHERE sk_tempo_pedido = -1)          AS sem_data_pedido,
    count(*) FILTER (WHERE sk_tempo_envio  = -1)          AS sem_data_envio,
    count(*) FILTER (WHERE sk_status = -1)                AS sem_status
FROM dw.fato_vendas;


-- #############################################################################
-- 4. ESTADO DA CARGA INCREMENTAL
-- #############################################################################

SELECT nm_entidade, ds_tabela_origem, dt_ultima_carga,
       qt_registros_ultima, qt_registros_total, dt_atualizacao
  FROM meta.etl_controle
 ORDER BY nm_entidade;

-- Ultimo ciclo executado, entidade a entidade.
SELECT nm_entidade, ds_fase, dt_inicio, dt_fim,
       ROUND(EXTRACT(EPOCH FROM (dt_fim - dt_inicio))::numeric, 2) AS segundos,
       qt_extraidos, qt_inseridos, qt_atualizados, ds_status
  FROM meta.etl_execucao
 WHERE id_lote = (SELECT id_lote FROM meta.etl_execucao
                   ORDER BY id_execucao DESC LIMIT 1)
 ORDER BY id_execucao;

-- Comparativo entre ciclos: evidencia a queda de volume da carga full para as
-- cargas incrementais subsequentes.
SELECT id_lote,
       min(dt_inicio)                                          AS inicio_ciclo,
       ROUND(EXTRACT(EPOCH FROM (max(dt_fim) - min(dt_inicio)))::numeric, 2) AS segundos,
       sum(qt_extraidos)                                       AS qt_extraidos,
       sum(qt_inseridos)                                       AS qt_inseridos,
       sum(qt_atualizados)                                     AS qt_atualizados
  FROM meta.etl_execucao
 GROUP BY id_lote
 ORDER BY inicio_ciclo;


-- #############################################################################
-- 5. COMPROVACAO DOS EFEITOS DE sql/98_simular_alteracoes.sql
-- #############################################################################

-- (A) SCD Tipo 2: o produto 707 deve apresentar duas versoes, com intervalos
--     de vigencia adjacentes e apenas a mais recente marcada como corrente.
SELECT sk_produto, id_produto, nm_produto, vl_preco_lista, nr_versao,
       dt_inicio_validade, dt_fim_validade, fl_corrente, dt_modificacao_origem
  FROM dw.dim_produto
 WHERE id_produto = 707
 ORDER BY nr_versao;

-- (B) SCD Tipo 1: o fornecedor 1492 deve continuar com UMA unica linha,
--     com o atributo sobrescrito e dt_atualizacao recente.
SELECT sk_fornecedor, id_fornecedor, nm_fornecedor, nr_nivel_credito,
       ds_nivel_credito, dt_modificacao_origem, dt_carga, dt_atualizacao
  FROM dw.dim_fornecedor
 WHERE id_fornecedor = 1492;

-- (C) Nova transacao: as linhas de venda mais recentes carregadas no DW.
SELECT f.nr_pedido, t.dt_data AS dt_pedido, p.nm_produto, f.qt_vendida,
       f.vl_preco_unitario, f.pc_desconto_unitario, f.vl_liquido,
       f.vl_margem_bruta, f.dt_carga
  FROM dw.fato_vendas AS f
  JOIN dw.dim_tempo   AS t ON t.sk_tempo   = f.sk_tempo_pedido
  JOIN dw.dim_produto AS p ON p.sk_produto = f.sk_produto
 ORDER BY f.id_item_venda DESC
 LIMIT 10;

-- (D) Fidelidade historica: as vendas antigas do produto 707 devem permanecer
--     ligadas a VERSAO 1 (preco antigo), enquanto vendas posteriores a
--     alteracao apontam para a versao 2. E este o efeito pratico do SCD Tipo 2.
SELECT p.nr_versao, p.vl_preco_lista, p.dt_inicio_validade, p.dt_fim_validade,
       count(*)                    AS qt_linhas_venda,
       min(t.dt_data)              AS primeira_venda,
       max(t.dt_data)              AS ultima_venda,
       ROUND(SUM(f.vl_liquido), 2) AS vl_receita_liquida
  FROM dw.fato_vendas AS f
  JOIN dw.dim_produto AS p ON p.sk_produto = f.sk_produto
  JOIN dw.dim_tempo   AS t ON t.sk_tempo   = f.sk_tempo_pedido
 WHERE p.id_produto = 707
 GROUP BY p.nr_versao, p.vl_preco_lista, p.dt_inicio_validade, p.dt_fim_validade
 ORDER BY p.nr_versao;
