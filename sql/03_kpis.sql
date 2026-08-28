-- =============================================================================
-- INDICADORES (KPIs) DO DATA WAREHOUSE ADVENTUREWORKS
--
-- Dez indicadores implementados exclusivamente sobre o modelo estrela,
-- sem qualquer acesso ao sistema transacional. Cada bloco traz a definicao
-- do indicador, a formula de calculo, as dimensoes de analise utilizadas e
-- a consulta SQL correspondente.
--
-- Execucao completa:
--   docker exec -i dw_adventureworks_pg psql -U dw_user -d dw_adventureworks \
--       -f /dev/stdin < sql/03_kpis.sql
-- =============================================================================


-- #############################################################################
-- KPI 01 - RECEITA LIQUIDA TOTAL
--
-- Definicao : valor efetivamente faturado, ja deduzidos os descontos concedidos.
-- Formula   : SUM(vl_liquido), onde vl_liquido = qt * preco * (1 - desconto)
-- Dimensoes : dim_tempo (ano, trimestre) x dim_territorio (grupo, territorio)
-- Uso       : indicador primario de desempenho comercial; base de comparacao
--             para todos os demais indicadores de valor.
-- #############################################################################

SELECT
    t.nr_ano                                                  AS ano,
    t.ds_ano_trimestre                                        AS trimestre,
    te.nm_grupo                                               AS regiao,
    te.nm_territorio                                          AS territorio,
    COUNT(DISTINCT f.id_pedido)                               AS qt_pedidos,
    SUM(f.qt_vendida)                                         AS qt_itens,
    ROUND(SUM(f.vl_bruto),    2)                              AS vl_receita_bruta,
    ROUND(SUM(f.vl_desconto), 2)                              AS vl_descontos,
    ROUND(SUM(f.vl_liquido),  2)                              AS vl_receita_liquida
FROM dw.fato_vendas   AS f
JOIN dw.dim_tempo     AS t  ON t.sk_tempo      = f.sk_tempo_pedido
JOIN dw.dim_territorio AS te ON te.sk_territorio = f.sk_territorio
GROUP BY ROLLUP (t.nr_ano, t.ds_ano_trimestre, te.nm_grupo, te.nm_territorio)
HAVING t.nr_ano IS NOT NULL
ORDER BY ano, trimestre NULLS LAST, regiao NULLS LAST, vl_receita_liquida DESC;


-- #############################################################################
-- KPI 02 - TICKET MEDIO POR PEDIDO
--
-- Definicao : valor medio faturado em cada pedido de venda.
-- Formula   : SUM(vl_liquido) / COUNT(DISTINCT id_pedido)
-- Dimensoes : dim_tempo (ano, mes) x dim_canal_venda
-- Observacao: exige contagem DISTINTA do pedido porque o grao do fato e o
--             item; somar linhas sem distinguir o pedido inflaria o
--             denominador e subestimaria o ticket.
-- #############################################################################

SELECT
    t.nr_ano                                                  AS ano,
    t.ds_ano_mes                                              AS ano_mes,
    c.nm_canal                                                AS canal,
    COUNT(DISTINCT f.id_pedido)                               AS qt_pedidos,
    ROUND(SUM(f.vl_liquido), 2)                               AS vl_receita_liquida,
    ROUND(SUM(f.vl_liquido) / NULLIF(COUNT(DISTINCT f.id_pedido), 0), 2)
                                                              AS vl_ticket_medio,
    ROUND(SUM(f.qt_vendida)::numeric / NULLIF(COUNT(DISTINCT f.id_pedido), 0), 2)
                                                              AS qt_itens_por_pedido
FROM dw.fato_vendas     AS f
JOIN dw.dim_tempo       AS t ON t.sk_tempo = f.sk_tempo_pedido
JOIN dw.dim_canal_venda AS c ON c.sk_canal = f.sk_canal
GROUP BY t.nr_ano, t.ds_ano_mes, c.nm_canal
ORDER BY ano_mes, canal;


-- #############################################################################
-- KPI 03 - MARGEM BRUTA PERCENTUAL
--
-- Definicao : parcela da receita liquida que sobra apos o custo do produto.
-- Formula   : (SUM(vl_liquido) - SUM(vl_custo_total)) / SUM(vl_liquido) * 100
-- Dimensoes : dim_produto (categoria, subcategoria) x dim_tempo (ano)
-- Observacao: o custo gravado no fato e o vigente na data do pedido
--             (Production.ProductCostHistory), o que preserva a fidelidade
--             historica da margem.
-- #############################################################################

SELECT
    t.nr_ano                                                  AS ano,
    p.nm_categoria                                            AS categoria,
    p.nm_subcategoria                                         AS subcategoria,
    ROUND(SUM(f.vl_liquido),       2)                         AS vl_receita_liquida,
    ROUND(SUM(f.vl_custo_total),   2)                         AS vl_custo_total,
    ROUND(SUM(f.vl_margem_bruta),  2)                         AS vl_margem_bruta,
    ROUND(100.0 * SUM(f.vl_margem_bruta) / NULLIF(SUM(f.vl_liquido), 0), 2)
                                                              AS pc_margem_bruta
FROM dw.fato_vendas AS f
JOIN dw.dim_tempo   AS t ON t.sk_tempo   = f.sk_tempo_pedido
JOIN dw.dim_produto AS p ON p.sk_produto = f.sk_produto
GROUP BY t.nr_ano, p.nm_categoria, p.nm_subcategoria
HAVING SUM(f.vl_liquido) > 0
ORDER BY ano, pc_margem_bruta DESC;


-- #############################################################################
-- KPI 04 - TAXA MEDIA DE DESCONTO CONCEDIDO
--
-- Definicao : percentual da receita bruta renunciado sob forma de desconto.
-- Formula   : SUM(vl_desconto) / SUM(vl_bruto) * 100
-- Dimensoes : dim_promocao (tipo, categoria) x dim_tempo (ano)
-- Uso       : mede a eficacia das campanhas promocionais confrontando o
--             desconto concedido com o volume incremental gerado.
-- #############################################################################

SELECT
    t.nr_ano                                                  AS ano,
    pr.tp_promocao                                            AS tipo_promocao,
    pr.ds_promocao                                            AS promocao,
    COUNT(*)                                                  AS qt_linhas_venda,
    SUM(f.qt_vendida)                                         AS qt_itens,
    ROUND(SUM(f.vl_bruto),    2)                              AS vl_receita_bruta,
    ROUND(SUM(f.vl_desconto), 2)                              AS vl_desconto_concedido,
    ROUND(100.0 * SUM(f.vl_desconto) / NULLIF(SUM(f.vl_bruto), 0), 2)
                                                              AS pc_desconto_medio
FROM dw.fato_vendas  AS f
JOIN dw.dim_tempo    AS t  ON t.sk_tempo    = f.sk_tempo_pedido
JOIN dw.dim_promocao AS pr ON pr.sk_promocao = f.sk_promocao
GROUP BY t.nr_ano, pr.tp_promocao, pr.ds_promocao
ORDER BY ano, pc_desconto_medio DESC;


-- #############################################################################
-- KPI 05 - CRESCIMENTO DE RECEITA ANO CONTRA ANO (YoY)
--
-- Definicao : variacao percentual da receita de um mes em relacao ao mesmo
--             mes do ano anterior.
-- Formula   : (receita_mes - receita_mes_ano_anterior) / receita_mes_ano_anterior * 100
-- Dimensoes : dim_tempo (ano, mes)
-- Tecnica   : funcao de janela LAG particionada pelo mes e ordenada pelo ano,
--             o que alinha automaticamente cada mes ao seu equivalente
--             do ano anterior.
-- #############################################################################

WITH receita_mensal AS (
    SELECT
        t.nr_ano                        AS ano,
        t.nr_mes                        AS mes,
        t.nm_mes                        AS nome_mes,
        SUM(f.vl_liquido)               AS vl_receita
    FROM dw.fato_vendas AS f
    JOIN dw.dim_tempo   AS t ON t.sk_tempo = f.sk_tempo_pedido
    WHERE t.sk_tempo > 0
    GROUP BY t.nr_ano, t.nr_mes, t.nm_mes
)
SELECT
    ano,
    mes,
    nome_mes,
    ROUND(vl_receita, 2)                                      AS vl_receita,
    ROUND(LAG(vl_receita) OVER (PARTITION BY mes ORDER BY ano), 2)
                                                              AS vl_receita_ano_anterior,
    ROUND(vl_receita - LAG(vl_receita) OVER (PARTITION BY mes ORDER BY ano), 2)
                                                              AS vl_variacao_absoluta,
    ROUND(100.0 * (vl_receita - LAG(vl_receita) OVER (PARTITION BY mes ORDER BY ano))
          / NULLIF(LAG(vl_receita) OVER (PARTITION BY mes ORDER BY ano), 0), 2)
                                                              AS pc_crescimento_yoy
FROM receita_mensal
ORDER BY ano, mes;


-- #############################################################################
-- KPI 06 - CURVA ABC DE PRODUTOS (PARETO)
--
-- Definicao : classificacao dos produtos pela contribuicao acumulada a receita.
--             Classe A ate 80% da receita, B ate 95%, C o restante.
-- Formula   : receita acumulada / receita total, sobre o ranking decrescente.
-- Dimensoes : dim_produto (produto, categoria)
-- Tecnica   : SUM() OVER (ORDER BY ...) para o acumulado e NTILE/CASE para a
--             faixa de classificacao.
-- #############################################################################

WITH receita_produto AS (
    SELECT
        p.id_produto,
        p.nm_produto,
        p.nm_categoria,
        SUM(f.vl_liquido)     AS vl_receita,
        SUM(f.qt_vendida)     AS qt_vendida,
        SUM(f.vl_margem_bruta) AS vl_margem
    FROM dw.fato_vendas AS f
    JOIN dw.dim_produto AS p ON p.sk_produto = f.sk_produto
    GROUP BY p.id_produto, p.nm_produto, p.nm_categoria
),
acumulado AS (
    SELECT
        rp.*,
        ROW_NUMBER() OVER (ORDER BY vl_receita DESC)                       AS nr_ranking,
        100.0 * vl_receita / SUM(vl_receita) OVER ()                       AS pc_participacao,
        100.0 * SUM(vl_receita) OVER (ORDER BY vl_receita DESC
                                      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
              / SUM(vl_receita) OVER ()                                    AS pc_acumulado
    FROM receita_produto AS rp
)
SELECT
    nr_ranking                                                AS ranking,
    nm_produto                                                AS produto,
    nm_categoria                                              AS categoria,
    qt_vendida                                                AS qt_vendida,
    ROUND(vl_receita, 2)                                      AS vl_receita_liquida,
    ROUND(vl_margem,  2)                                      AS vl_margem_bruta,
    ROUND(pc_participacao, 4)                                 AS pc_participacao,
    ROUND(pc_acumulado,    2)                                 AS pc_acumulado,
    CASE WHEN pc_acumulado <= 80 THEN 'A'
         WHEN pc_acumulado <= 95 THEN 'B'
         ELSE 'C' END                                         AS classe_abc
FROM acumulado
ORDER BY nr_ranking;


-- #############################################################################
-- KPI 07 - MIX DE RECEITA POR CANAL DE VENDA
--
-- Definicao : participacao de cada canal (Internet x Revenda) na receita.
-- Formula   : receita_canal / receita_total_do_periodo * 100
-- Dimensoes : dim_canal_venda x dim_tempo (ano) x dim_cliente (tipo)
-- Uso       : acompanha a migracao do faturamento entre os canais direto e
--             indireto ao longo do tempo.
-- #############################################################################

SELECT
    t.nr_ano                                                  AS ano,
    ca.nm_canal                                               AS canal,
    cl.tp_cliente                                             AS tipo_cliente,
    COUNT(DISTINCT f.id_pedido)                               AS qt_pedidos,
    COUNT(DISTINCT f.sk_cliente)                              AS qt_clientes_distintos,
    ROUND(SUM(f.vl_liquido), 2)                               AS vl_receita_liquida,
    ROUND(100.0 * SUM(SUM(f.vl_liquido)) OVER (PARTITION BY t.nr_ano, ca.nm_canal)
          / SUM(SUM(f.vl_liquido)) OVER (PARTITION BY t.nr_ano), 2)
                                                              AS pc_participacao_canal
FROM dw.fato_vendas     AS f
JOIN dw.dim_tempo       AS t  ON t.sk_tempo   = f.sk_tempo_pedido
JOIN dw.dim_canal_venda AS ca ON ca.sk_canal  = f.sk_canal
JOIN dw.dim_cliente     AS cl ON cl.sk_cliente = f.sk_cliente
GROUP BY t.nr_ano, ca.nm_canal, cl.tp_cliente
ORDER BY ano, canal, tipo_cliente;


-- #############################################################################
-- KPI 08 - PONTUALIDADE DE ENTREGA (OTD) E PRAZO MEDIO
--
-- Definicao : OTD e o percentual de itens entregues ate a data prometida;
--             o prazo medio e o intervalo entre pedido e envio.
-- Formula   : OTD = 100 * (1 - itens_atrasados / itens_entregues)
--             Prazo medio = AVG(qt_dias_entrega)
-- Dimensoes : dim_metodo_envio x dim_geografia (pais) x dim_tempo (ano)
-- Observacao: consideram-se apenas itens ja enviados (sk_tempo_envio > 0),
--             pois pedidos em aberto nao possuem prazo realizado.
-- #############################################################################

SELECT
    t.nr_ano                                                  AS ano,
    me.nm_metodo_envio                                        AS metodo_envio,
    g.nm_pais                                                 AS pais_entrega,
    COUNT(*)                                                  AS qt_itens_entregues,
    ROUND(AVG(f.qt_dias_entrega), 2)                          AS qt_dias_entrega_medio,
    MAX(f.qt_dias_entrega)                                    AS qt_dias_entrega_maximo,
    COUNT(*) FILTER (WHERE f.fl_entrega_atrasada)             AS qt_itens_atrasados,
    ROUND(100.0 * COUNT(*) FILTER (WHERE NOT f.fl_entrega_atrasada)
          / NULLIF(COUNT(*), 0), 2)                           AS pc_entregas_no_prazo
FROM dw.fato_vendas      AS f
JOIN dw.dim_tempo        AS t  ON t.sk_tempo         = f.sk_tempo_pedido
JOIN dw.dim_metodo_envio AS me ON me.sk_metodo_envio = f.sk_metodo_envio
JOIN dw.dim_geografia    AS g  ON g.sk_geografia     = f.sk_geografia_entrega
WHERE f.sk_tempo_envio > 0
GROUP BY t.nr_ano, me.nm_metodo_envio, g.nm_pais
HAVING COUNT(*) >= 50
ORDER BY ano, pc_entregas_no_prazo DESC, qt_itens_entregues DESC;


-- #############################################################################
-- KPI 09 - DESEMPENHO DA FORCA DE VENDAS E ATINGIMENTO DE COTA
--
-- Definicao : receita gerada por vendedor e sua relacao com a cota cadastrada.
-- Formula   : receita_vendedor / vl_cota_vendas * 100
-- Dimensoes : dim_funcionario (papel VENDEDOR) x dim_territorio x dim_tempo
-- Observacao: exclui-se o membro "Nao Informado" (-1), que concentra as vendas
--             pela internet, nas quais nao ha vendedor associado.
-- #############################################################################

SELECT
    t.nr_ano                                                  AS ano,
    v.nm_funcionario                                          AS vendedor,
    v.ds_cargo                                                AS cargo,
    te.nm_territorio                                          AS territorio,
    COUNT(DISTINCT f.id_pedido)                               AS qt_pedidos,
    COUNT(DISTINCT f.sk_cliente)                              AS qt_clientes_atendidos,
    ROUND(SUM(f.vl_liquido),      2)                          AS vl_receita_liquida,
    ROUND(SUM(f.vl_margem_bruta), 2)                          AS vl_margem_bruta,
    ROUND(v.vl_cota_vendas, 2)                                AS vl_cota,
    ROUND(100.0 * SUM(f.vl_liquido) / NULLIF(v.vl_cota_vendas, 0), 2)
                                                              AS pc_atingimento_cota,
    RANK() OVER (PARTITION BY t.nr_ano ORDER BY SUM(f.vl_liquido) DESC)
                                                              AS nr_ranking_ano
FROM dw.fato_vendas     AS f
JOIN dw.dim_tempo       AS t  ON t.sk_tempo       = f.sk_tempo_pedido
JOIN dw.dim_funcionario AS v  ON v.sk_funcionario = f.sk_vendedor
JOIN dw.dim_territorio  AS te ON te.sk_territorio = f.sk_territorio
WHERE f.sk_vendedor > 0
GROUP BY t.nr_ano, v.nm_funcionario, v.ds_cargo, te.nm_territorio, v.vl_cota_vendas
ORDER BY ano, vl_receita_liquida DESC;


-- #############################################################################
-- KPI 10 - DESEMPENHO DE FORNECEDORES: CUSTO DE AQUISICAO E TAXA DE REJEICAO
--
-- Definicao : volume comprado, custo unitario medio e qualidade do
--             fornecimento (percentual de itens rejeitados no recebimento).
-- Formula   : Custo medio  = SUM(vl_total_linha) / SUM(qt_pedida)
--             Taxa rejeicao = SUM(qt_rejeitada) / SUM(qt_recebida) * 100
-- Dimensoes : dim_fornecedor x dim_produto (categoria) x dim_tempo (ano)
-- Fato      : dw.fato_compras -- demonstra o uso das dimensoes conformadas
--             (tempo e produto) por um segundo processo de negocio.
-- #############################################################################

SELECT
    t.nr_ano                                                  AS ano,
    fo.nm_fornecedor                                          AS fornecedor,
    fo.ds_nivel_credito                                       AS nivel_credito,
    COUNT(DISTINCT f.id_ordem_compra)                         AS qt_ordens_compra,
    COUNT(DISTINCT f.sk_produto)                              AS qt_produtos_distintos,
    SUM(f.qt_pedida)                                          AS qt_pedida,
    SUM(f.qt_recebida)                                        AS qt_recebida,
    SUM(f.qt_rejeitada)                                       AS qt_rejeitada,
    ROUND(SUM(f.vl_total_linha), 2)                           AS vl_total_comprado,
    ROUND(SUM(f.vl_total_linha) / NULLIF(SUM(f.qt_pedida), 0), 4)
                                                              AS vl_custo_unitario_medio,
    ROUND(100.0 * SUM(f.qt_rejeitada) / NULLIF(SUM(f.qt_recebida), 0), 2)
                                                              AS pc_taxa_rejeicao,
    ROUND(AVG(f.qt_dias_recebimento), 1)                      AS qt_dias_recebimento_medio,
    ROUND(100.0 * COUNT(*) FILTER (WHERE NOT f.fl_recebimento_atrasado)
          / NULLIF(COUNT(*), 0), 2)                           AS pc_recebimentos_no_prazo
FROM dw.fato_compras   AS f
JOIN dw.dim_tempo      AS t  ON t.sk_tempo      = f.sk_tempo_pedido
JOIN dw.dim_fornecedor AS fo ON fo.sk_fornecedor = f.sk_fornecedor
WHERE f.sk_fornecedor > 0
GROUP BY t.nr_ano, fo.nm_fornecedor, fo.ds_nivel_credito
HAVING SUM(f.qt_recebida) > 0
ORDER BY ano, pc_taxa_rejeicao DESC, vl_total_comprado DESC;
