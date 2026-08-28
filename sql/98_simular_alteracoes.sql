-- =============================================================================
-- SIMULACAO DE MOVIMENTO NO OLTP  (executar no SQL SERVER / AdventureWorks)
--
-- Objetivo: comprovar empiricamente que a ETL e incremental. O script provoca
-- no sistema transacional os tres eventos que a carga precisa reconhecer:
--
--   (A) ALTERACAO de atributo monitorado de dimensao com historico
--       -> deve gerar uma NOVA VERSAO em dw.dim_produto (SCD Tipo 2)
--   (B) ALTERACAO de atributo de dimensao sem historico
--       -> deve SOBRESCREVER a linha em dw.dim_fornecedor (SCD Tipo 1)
--   (C) INSERCAO de nova transacao de venda
--       -> deve acrescentar linhas a dw.fato_vendas
--
-- Roteiro de comprovacao:
--   1. python -m etl.main --status            (anota as marcas d'agua)
--   2. sqlcmd -S localhost\SQLEXPRESS -E -d AdventureWorks2022 -i sql\98_simular_alteracoes.sql
--   3. python -m etl.main                     (observa o volume processado)
--   4. sql\99_validacao.sql secao 5           (confere os efeitos no DW)
--
-- ATENCAO: este script ESCREVE no banco de origem. Ele foi concebido para a
-- base de demonstracao AdventureWorks, nao para um ambiente produtivo.
-- =============================================================================

USE AdventureWorks2022;
GO

-- O sqlcmd inicia a sessao com QUOTED_IDENTIFIER OFF. Sales.SalesOrderHeader
-- possui indices filtrados e colunas computadas persistidas, e o SQL Server
-- recusa qualquer INSERT nessa condicao (erro 1934). As opcoes abaixo deixam
-- o script executavel tanto pelo sqlcmd quanto pelo SSMS.
SET QUOTED_IDENTIFIER ON;
SET ANSI_NULLS ON;
SET NOCOUNT ON;
GO

PRINT '--- (A) SCD Tipo 2: reajuste de preco de lista em produto ---';

-- Reajuste de 10% no preco de lista do produto 707 (Sport-100 Helmet, Red).
-- Como vl_preco_lista integra o hash monitorado de dim_produto, a ETL deve
-- encerrar a versao vigente e inserir a versao 2.
UPDATE Production.Product
   SET ListPrice    = ListPrice * 1.10,
       ModifiedDate = SYSDATETIME()
 WHERE ProductID = 707;

SELECT ProductID, Name, ListPrice, ModifiedDate
  FROM Production.Product
 WHERE ProductID = 707;
GO

PRINT '--- (B) SCD Tipo 1: alteracao cadastral de fornecedor ---';

-- Alteracao do nivel de credito do fornecedor 1492. Como dim_fornecedor e
-- SCD Tipo 1, a ETL deve SOBRESCREVER a linha existente, sem criar versao.
UPDATE Purchasing.Vendor
   SET CreditRating = CASE WHEN CreditRating = 1 THEN 2 ELSE 1 END,
       ModifiedDate = SYSDATETIME()
 WHERE BusinessEntityID = 1492;

SELECT BusinessEntityID, Name, CreditRating, ModifiedDate
  FROM Purchasing.Vendor
 WHERE BusinessEntityID = 1492;
GO

PRINT '--- (C) Nova transacao: pedido de venda com dois itens ---';

BEGIN TRANSACTION;

DECLARE @SalesOrderID int;

INSERT INTO Sales.SalesOrderHeader
    (RevisionNumber, OrderDate, DueDate, ShipDate, Status, OnlineOrderFlag,
     CustomerID, SalesPersonID, TerritoryID, BillToAddressID, ShipToAddressID,
     ShipMethodID, SubTotal, TaxAmt, Freight, ModifiedDate)
VALUES
    (1, SYSDATETIME(), DATEADD(day, 7, SYSDATETIME()), DATEADD(day, 3, SYSDATETIME()),
     5, 0, 29825, 279, 5, 985, 985, 5, 0, 0, 0, SYSDATETIME());

SET @SalesOrderID = SCOPE_IDENTITY();

INSERT INTO Sales.SalesOrderDetail
    (SalesOrderID, OrderQty, ProductID, SpecialOfferID, UnitPrice,
     UnitPriceDiscount, ModifiedDate)
VALUES
    (@SalesOrderID, 3, 707, 1, 34.99, 0.00, SYSDATETIME()),
    (@SalesOrderID, 2, 708, 1, 34.99, 0.10, SYSDATETIME());

-- Recalcula o subtotal do cabecalho a partir das linhas inseridas, para que o
-- rateio de frete e imposto realizado pela ETL permaneca consistente.
UPDATE h
   SET h.SubTotal     = d.Subtotal,
       h.Freight      = ROUND(d.Subtotal * 0.025, 4),
       h.TaxAmt       = ROUND(d.Subtotal * 0.080, 4),
       h.ModifiedDate = SYSDATETIME()
  FROM Sales.SalesOrderHeader AS h
 CROSS APPLY (
     SELECT SUM(LineTotal) AS Subtotal
       FROM Sales.SalesOrderDetail
      WHERE SalesOrderID = @SalesOrderID
 ) AS d
 WHERE h.SalesOrderID = @SalesOrderID;

COMMIT TRANSACTION;

PRINT 'Pedido inserido:';
SELECT h.SalesOrderID, h.SalesOrderNumber, h.OrderDate, h.SubTotal,
       COUNT(d.SalesOrderDetailID) AS Itens
  FROM Sales.SalesOrderHeader AS h
  JOIN Sales.SalesOrderDetail AS d ON d.SalesOrderID = h.SalesOrderID
 WHERE h.SalesOrderID = (SELECT MAX(SalesOrderID) FROM Sales.SalesOrderHeader)
 GROUP BY h.SalesOrderID, h.SalesOrderNumber, h.OrderDate, h.SubTotal;
GO

PRINT '';
PRINT 'Simulacao concluida. Execute agora: python -m etl.main';
GO
