"""Consultas de extracao executadas no SQL Server (AdventureWorks / OLTP).

Toda consulta recebe o mesmo parametro posicional ``?``: a marca d'agua da
entidade. O predicado ``ModifiedDate > ?`` e o que torna a extracao
incremental -- na primeira execucao a marca vale 1900-01-01 e o resultado
equivale a uma carga completa.

Nas consultas dos fatos o predicado considera a maior data de modificacao
entre o item e o cabecalho do pedido. Isso e necessario porque, no
AdventureWorks, alteracoes no cabecalho (por exemplo o preenchimento da data
de envio) atualizam apenas ``SalesOrderHeader.ModifiedDate``, sem tocar nas
linhas de detalhe. Ignorar o cabecalho faria a ETL perder essas mudancas.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# DIMENSOES
# ---------------------------------------------------------------------------

PRODUTO = """
SELECT
    p.ProductID                                        AS id_produto,
    p.ProductNumber                                    AS cd_produto,
    p.Name                                             AS nm_produto,
    ISNULL(pc.Name, 'Sem Categoria')                   AS nm_categoria,
    ISNULL(ps.Name, 'Sem Subcategoria')                AS nm_subcategoria,
    ISNULL(pm.Name, 'Sem Modelo')                      AS nm_modelo,
    CASE p.ProductLine
         WHEN 'R' THEN 'Road'      WHEN 'M' THEN 'Mountain'
         WHEN 'T' THEN 'Touring'   WHEN 'S' THEN 'Standard'
         ELSE 'Nao Informado' END                      AS ds_linha,
    CASE p.Class
         WHEN 'H' THEN 'Alta'      WHEN 'M' THEN 'Media'
         WHEN 'L' THEN 'Baixa'     ELSE 'Nao Informado' END AS ds_classe,
    CASE p.Style
         WHEN 'M' THEN 'Masculino' WHEN 'W' THEN 'Feminino'
         WHEN 'U' THEN 'Unissex'   ELSE 'Nao Informado' END AS ds_estilo,
    ISNULL(p.Color, 'Nao Informado')                   AS ds_cor,
    p.Size                                             AS ds_tamanho,
    p.Weight                                           AS vl_peso,
    um.Name                                            AS nm_unidade_peso,
    p.StandardCost                                     AS vl_custo_padrao,
    p.ListPrice                                        AS vl_preco_lista,
    p.MakeFlag                                         AS fl_fabricacao_propria,
    p.FinishedGoodsFlag                                AS fl_produto_acabado,
    p.SafetyStockLevel                                 AS qt_estoque_seguranca,
    p.ReorderPoint                                     AS qt_ponto_reposicao,
    p.DaysToManufacture                                AS nr_dias_fabricacao,
    CAST(p.SellStartDate    AS date)                   AS dt_inicio_venda,
    CAST(p.SellEndDate      AS date)                   AS dt_fim_venda,
    CAST(p.DiscontinuedDate AS date)                   AS dt_descontinuado,
    p.ModifiedDate                                     AS dt_modificacao_origem
FROM Production.Product AS p
LEFT JOIN Production.ProductSubcategory AS ps ON ps.ProductSubcategoryID = p.ProductSubcategoryID
LEFT JOIN Production.ProductCategory    AS pc ON pc.ProductCategoryID    = ps.ProductCategoryID
LEFT JOIN Production.ProductModel       AS pm ON pm.ProductModelID       = p.ProductModelID
LEFT JOIN Production.UnitMeasure        AS um ON um.UnitMeasureCode      = p.WeightUnitMeasureCode
WHERE p.ModifiedDate > ?
ORDER BY p.ModifiedDate, p.ProductID;
"""

CLIENTE = """
SELECT
    c.CustomerID                                       AS id_cliente,
    c.AccountNumber                                    AS cd_conta,
    CASE WHEN c.StoreID IS NOT NULL THEN 'Loja' ELSE 'Pessoa Fisica' END AS tp_cliente,
    COALESCE(
        st.Name,
        NULLIF(LTRIM(RTRIM(ISNULL(pe.FirstName, '') + ' ' + ISNULL(pe.LastName, ''))), ''),
        'Cliente ' + CAST(c.CustomerID AS varchar(12))
    )                                                  AS nm_cliente,
    pe.FirstName                                       AS nm_primeiro,
    pe.LastName                                        AS nm_sobrenome,
    st.Name                                            AS nm_loja,
    ea.EmailAddress                                    AS ds_email,
    CAST(CASE WHEN ISNULL(pe.EmailPromotion, 0) > 0 THEN 1 ELSE 0 END AS bit) AS fl_aceita_promocao,
    c.ModifiedDate                                     AS dt_modificacao_origem
FROM Sales.Customer AS c
LEFT JOIN Person.Person       AS pe ON pe.BusinessEntityID = c.PersonID
LEFT JOIN Sales.Store         AS st ON st.BusinessEntityID = c.StoreID
OUTER APPLY (
    SELECT TOP 1 e.EmailAddress
    FROM Person.EmailAddress AS e
    WHERE e.BusinessEntityID = c.PersonID
    ORDER BY e.EmailAddressID
) AS ea
WHERE c.ModifiedDate > ?
ORDER BY c.ModifiedDate, c.CustomerID;
"""

FUNCIONARIO = """
SELECT
    e.BusinessEntityID                                 AS id_funcionario,
    LTRIM(RTRIM(p.FirstName + ' ' + ISNULL(p.MiddleName + ' ', '') + p.LastName)) AS nm_funcionario,
    e.JobTitle                                         AS ds_cargo,
    CASE e.Gender WHEN 'M' THEN 'Masculino' WHEN 'F' THEN 'Feminino'
                  ELSE 'Nao Informado' END             AS ds_genero,
    CASE e.MaritalStatus WHEN 'M' THEN 'Casado' WHEN 'S' THEN 'Solteiro'
                         ELSE 'Nao Informado' END      AS ds_estado_civil,
    CAST(e.BirthDate AS date)                          AS dt_nascimento,
    CAST(e.HireDate  AS date)                          AS dt_admissao,
    e.SalariedFlag                                     AS fl_assalariado,
    CAST(CASE WHEN sp.BusinessEntityID IS NOT NULL THEN 1 ELSE 0 END AS bit) AS fl_vendedor,
    sp.SalesQuota                                      AS vl_cota_vendas,
    sp.Bonus                                           AS vl_bonus,
    sp.CommissionPct                                   AS pc_comissao,
    e.ModifiedDate                                     AS dt_modificacao_origem
FROM HumanResources.Employee AS e
INNER JOIN Person.Person     AS p  ON p.BusinessEntityID  = e.BusinessEntityID
LEFT  JOIN Sales.SalesPerson AS sp ON sp.BusinessEntityID = e.BusinessEntityID
WHERE e.ModifiedDate > ?
ORDER BY e.ModifiedDate, e.BusinessEntityID;
"""

TERRITORIO = """
SELECT
    t.TerritoryID                                      AS id_territorio,
    t.Name                                             AS nm_territorio,
    t.[Group]                                          AS nm_grupo,
    t.CountryRegionCode                                AS cd_pais,
    cr.Name                                            AS nm_pais,
    t.SalesYTD                                         AS vl_vendas_ano_atual,
    t.SalesLastYear                                    AS vl_vendas_ano_ante,
    t.CostYTD                                          AS vl_custo_ano_atual,
    t.ModifiedDate                                     AS dt_modificacao_origem
FROM Sales.SalesTerritory AS t
LEFT JOIN Person.CountryRegion AS cr ON cr.CountryRegionCode = t.CountryRegionCode
WHERE t.ModifiedDate > ?
ORDER BY t.ModifiedDate, t.TerritoryID;
"""

GEOGRAFIA = """
SELECT
    a.AddressID                                        AS id_endereco,
    ISNULL(a.City, 'Nao Informado')                    AS ds_cidade,
    sp.StateProvinceCode                               AS cd_estado,
    ISNULL(sp.Name, 'Nao Informado')                   AS nm_estado,
    sp.CountryRegionCode                               AS cd_pais,
    ISNULL(cr.Name, 'Nao Informado')                   AS nm_pais,
    ISNULL(t.[Group], 'Nao Informado')                 AS nm_regiao,
    a.PostalCode                                       AS cd_postal,
    a.ModifiedDate                                     AS dt_modificacao_origem
FROM Person.Address AS a
LEFT JOIN Person.StateProvince  AS sp ON sp.StateProvinceID    = a.StateProvinceID
LEFT JOIN Person.CountryRegion  AS cr ON cr.CountryRegionCode  = sp.CountryRegionCode
LEFT JOIN Sales.SalesTerritory  AS t  ON t.TerritoryID         = sp.TerritoryID
WHERE a.ModifiedDate > ?
ORDER BY a.ModifiedDate, a.AddressID;
"""

FORNECEDOR = """
SELECT
    v.BusinessEntityID                                 AS id_fornecedor,
    v.AccountNumber                                    AS cd_conta,
    v.Name                                             AS nm_fornecedor,
    v.CreditRating                                     AS nr_nivel_credito,
    v.ActiveFlag                                       AS fl_fornecedor_ativo,
    v.PreferredVendorStatus                            AS fl_preferencial,
    v.ModifiedDate                                     AS dt_modificacao_origem
FROM Purchasing.Vendor AS v
WHERE v.ModifiedDate > ?
ORDER BY v.ModifiedDate, v.BusinessEntityID;
"""

PROMOCAO = """
SELECT
    so.SpecialOfferID                                  AS id_promocao,
    so.Description                                     AS ds_promocao,
    ISNULL(so.Type, 'Nao Informado')                   AS tp_promocao,
    ISNULL(so.Category, 'Nao Informado')               AS ds_categoria,
    so.DiscountPct                                     AS pc_desconto,
    so.MinQty                                          AS qt_minima,
    so.MaxQty                                          AS qt_maxima,
    CAST(so.StartDate AS date)                         AS dt_inicio,
    CAST(so.EndDate   AS date)                         AS dt_fim,
    so.ModifiedDate                                    AS dt_modificacao_origem
FROM Sales.SpecialOffer AS so
WHERE so.ModifiedDate > ?
ORDER BY so.ModifiedDate, so.SpecialOfferID;
"""

METODO_ENVIO = """
SELECT
    sm.ShipMethodID                                    AS id_metodo_envio,
    sm.Name                                            AS nm_metodo_envio,
    sm.ShipBase                                        AS vl_taxa_base,
    sm.ShipRate                                        AS vl_taxa_por_peso,
    sm.ModifiedDate                                    AS dt_modificacao_origem
FROM Purchasing.ShipMethod AS sm
WHERE sm.ModifiedDate > ?
ORDER BY sm.ModifiedDate, sm.ShipMethodID;
"""

# ---------------------------------------------------------------------------
# FATOS
#
# O custo do produto e buscado em Production.ProductCostHistory, tomando a
# versao vigente na data do pedido. Isso preserva a fidelidade historica da
# margem: usar o custo atual do produto distorceria a lucratividade de vendas
# antigas. Quando nao ha historico para a data, recorre-se ao custo padrao
# corrente do cadastro.
# ---------------------------------------------------------------------------

VENDA_ITEM = """
SELECT
    d.SalesOrderDetailID                               AS id_item_venda,
    h.SalesOrderID                                     AS id_pedido,
    h.SalesOrderNumber                                 AS nr_pedido,
    h.PurchaseOrderNumber                              AS nr_pedido_cliente,
    CAST(h.OrderDate AS date)                          AS dt_pedido,
    CAST(h.DueDate   AS date)                          AS dt_vencimento,
    CAST(h.ShipDate  AS date)                          AS dt_envio,
    d.ProductID                                        AS id_produto,
    h.CustomerID                                       AS id_cliente,
    h.SalesPersonID                                    AS id_vendedor,
    h.TerritoryID                                      AS id_territorio,
    d.SpecialOfferID                                   AS id_promocao,
    h.ShipToAddressID                                  AS id_endereco_entrega,
    h.ShipMethodID                                     AS id_metodo_envio,
    h.OnlineOrderFlag                                  AS fl_pedido_online,
    h.Status                                           AS cd_status,
    d.OrderQty                                         AS qt_vendida,
    d.UnitPrice                                        AS vl_preco_unitario,
    d.UnitPriceDiscount                                AS pc_desconto_unitario,
    ISNULL(pch.StandardCost, p.StandardCost)           AS vl_custo_unitario,
    h.Freight                                          AS vl_frete_pedido,
    h.TaxAmt                                           AS vl_imposto_pedido,
    h.SubTotal                                         AS vl_subtotal_pedido,
    CASE WHEN h.ModifiedDate > d.ModifiedDate
         THEN h.ModifiedDate ELSE d.ModifiedDate END   AS dt_modificacao_origem
FROM Sales.SalesOrderDetail AS d
INNER JOIN Sales.SalesOrderHeader AS h ON h.SalesOrderID = d.SalesOrderID
INNER JOIN Production.Product     AS p ON p.ProductID    = d.ProductID
OUTER APPLY (
    SELECT TOP 1 c.StandardCost
    FROM Production.ProductCostHistory AS c
    WHERE c.ProductID  = d.ProductID
      AND c.StartDate <= h.OrderDate
      AND (c.EndDate IS NULL OR c.EndDate >= h.OrderDate)
    ORDER BY c.StartDate DESC
) AS pch
WHERE d.ModifiedDate > ? OR h.ModifiedDate > ?
ORDER BY dt_modificacao_origem, d.SalesOrderDetailID;
"""

COMPRA_ITEM = """
SELECT
    d.PurchaseOrderDetailID                            AS id_item_compra,
    h.PurchaseOrderID                                  AS id_ordem_compra,
    CAST(h.OrderDate AS date)                          AS dt_pedido,
    CAST(d.DueDate   AS date)                          AS dt_previsto,
    CAST(h.ShipDate  AS date)                          AS dt_envio,
    d.ProductID                                        AS id_produto,
    h.VendorID                                         AS id_fornecedor,
    h.EmployeeID                                       AS id_comprador,
    h.ShipMethodID                                     AS id_metodo_envio,
    h.Status                                           AS cd_status,
    d.OrderQty                                         AS qt_pedida,
    d.ReceivedQty                                      AS qt_recebida,
    d.RejectedQty                                      AS qt_rejeitada,
    d.UnitPrice                                        AS vl_preco_unitario,
    d.LineTotal                                        AS vl_total_linha,
    h.Freight                                          AS vl_frete_pedido,
    h.TaxAmt                                           AS vl_imposto_pedido,
    h.SubTotal                                         AS vl_subtotal_pedido,
    CASE WHEN h.ModifiedDate > d.ModifiedDate
         THEN h.ModifiedDate ELSE d.ModifiedDate END   AS dt_modificacao_origem
FROM Purchasing.PurchaseOrderDetail AS d
INNER JOIN Purchasing.PurchaseOrderHeader AS h ON h.PurchaseOrderID = d.PurchaseOrderID
WHERE d.ModifiedDate > ? OR h.ModifiedDate > ?
ORDER BY dt_modificacao_origem, d.PurchaseOrderDetailID;
"""


# Mapeia cada entidade do DW a: consulta, tabela de staging e numero de
# parametros de marca d'agua exigidos pela consulta.
CATALOGO_EXTRACAO: dict[str, dict] = {
    "dim_produto":      {"sql": PRODUTO,      "staging": "stg.produto",      "parametros": 1},
    "dim_cliente":      {"sql": CLIENTE,      "staging": "stg.cliente",      "parametros": 1},
    "dim_funcionario":  {"sql": FUNCIONARIO,  "staging": "stg.funcionario",  "parametros": 1},
    "dim_territorio":   {"sql": TERRITORIO,   "staging": "stg.territorio",   "parametros": 1},
    "dim_geografia":    {"sql": GEOGRAFIA,    "staging": "stg.geografia",    "parametros": 1},
    "dim_fornecedor":   {"sql": FORNECEDOR,   "staging": "stg.fornecedor",   "parametros": 1},
    "dim_promocao":     {"sql": PROMOCAO,     "staging": "stg.promocao",     "parametros": 1},
    "dim_metodo_envio": {"sql": METODO_ENVIO, "staging": "stg.metodo_envio", "parametros": 1},
    "fato_vendas":      {"sql": VENDA_ITEM,   "staging": "stg.venda_item",   "parametros": 2},
    "fato_compras":     {"sql": COMPRA_ITEM,  "staging": "stg.compra_item",  "parametros": 2},
}
