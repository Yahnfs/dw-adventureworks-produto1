"""Ponto de entrada da ETL.

Exemplos de uso:

    python -m etl.main --testar-conexao      valida origem e destino
    python -m etl.main                       executa um ciclo incremental
    python -m etl.main --full                reinicia as marcas e recarrega tudo
    python -m etl.main --entidade fato_vendas
    python -m etl.main --status              exibe as marcas d'agua atuais
    python -m etl.main --validar             confere as contagens origem x destino
"""

from __future__ import annotations

import argparse
import sys

from etl import pipeline
from etl.infra import conexao_destino, conexao_origem, obter_logger, testar_conexoes

logger = obter_logger()

# Pares (tabela do DW, consulta equivalente no OLTP) usados na conferencia.
CONFERENCIAS = [
    ("dw.dim_produto (versoes correntes)",
     "SELECT count(*) FROM dw.dim_produto WHERE fl_corrente AND sk_produto > 0",
     "SELECT count(*) FROM Production.Product"),
    ("dw.dim_cliente",
     "SELECT count(*) FROM dw.dim_cliente WHERE sk_cliente > 0",
     "SELECT count(*) FROM Sales.Customer"),
    ("dw.dim_funcionario",
     "SELECT count(*) FROM dw.dim_funcionario WHERE sk_funcionario > 0",
     "SELECT count(*) FROM HumanResources.Employee"),
    ("dw.dim_geografia",
     "SELECT count(*) FROM dw.dim_geografia WHERE sk_geografia > 0",
     "SELECT count(*) FROM Person.Address"),
    ("dw.dim_fornecedor",
     "SELECT count(*) FROM dw.dim_fornecedor WHERE sk_fornecedor > 0",
     "SELECT count(*) FROM Purchasing.Vendor"),
    ("dw.fato_vendas",
     "SELECT count(*) FROM dw.fato_vendas",
     "SELECT count(*) FROM Sales.SalesOrderDetail"),
    ("dw.fato_compras",
     "SELECT count(*) FROM dw.fato_compras",
     "SELECT count(*) FROM Purchasing.PurchaseOrderDetail"),
    ("Receita liquida total",
     "SELECT ROUND(SUM(vl_liquido), 2) FROM dw.fato_vendas",
     "SELECT ROUND(SUM(LineTotal), 2) FROM Sales.SalesOrderDetail"),
]


def exibir_status() -> None:
    with conexao_destino(autocommit=True) as conexao:
        linhas = conexao.execute(
            """
            SELECT nm_entidade, ds_tabela_origem, dt_ultima_carga,
                   qt_registros_ultima, qt_registros_total, dt_atualizacao
              FROM meta.etl_controle
             ORDER BY nm_entidade;
            """
        ).fetchall()

    print(f"\n{'ENTIDADE':<18} {'ORIGEM':<32} {'MARCA D AGUA':<20} {'ULT.':>8} {'TOTAL':>9}")
    print("-" * 92)
    for entidade, origem, marca, ultima, total, _ in linhas:
        print(f"{entidade:<18} {origem:<32} {marca:%Y-%m-%d %H:%M:%S}  {ultima:>8} {total:>9}")
    print()


def validar() -> None:
    """Compara contagens e somatorios entre o OLTP e o Data Warehouse."""
    with conexao_destino(autocommit=True) as destino, conexao_origem() as origem:
        cursor_origem = origem.cursor()
        print(f"\n{'CONFERENCIA':<38} {'ORIGEM':>18} {'DESTINO':>18}  RESULTADO")
        print("-" * 88)
        divergencias = 0
        for rotulo, sql_dw, sql_oltp in CONFERENCIAS:
            valor_dw = destino.execute(sql_dw).fetchone()[0] or 0
            cursor_origem.execute(sql_oltp)
            valor_oltp = cursor_origem.fetchone()[0] or 0
            diferenca = abs(float(valor_dw) - float(valor_oltp))
            # Tolerancia relativa: somatorios monetarios da ordem de 10^8 acumulam
            # centavos de diferenca porque a origem soma LineTotal (numeric(38,6))
            # enquanto o DW recalcula a receita em numeric(19,4). Divergencias
            # acima de 0,00001% indicam perda ou duplicacao real de registros.
            tolerancia = max(0.01, abs(float(valor_oltp)) * 1e-7)
            igual = diferenca <= tolerancia
            divergencias += 0 if igual else 1
            marca = "OK" if igual else "DIVERGENTE"
            print(f"{rotulo:<38} {float(valor_oltp):>18,.2f} {float(valor_dw):>18,.2f}  {marca}")
        print("-" * 88)
        print(f"{'Divergencias:':<38} {divergencias}\n")


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="etl",
        description="ETL incremental AdventureWorks -> Data Warehouse PostgreSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--testar-conexao", action="store_true",
                        help="valida a conectividade com origem e destino e encerra")
    parser.add_argument("--status", action="store_true",
                        help="exibe as marcas d'agua registradas e encerra")
    parser.add_argument("--validar", action="store_true",
                        help="compara contagens entre OLTP e DW e encerra")
    parser.add_argument("--full", action="store_true",
                        help="reinicia as marcas d'agua, forcando recarga completa")
    parser.add_argument("--entidade", action="append", metavar="NOME",
                        help="restringe a carga a uma entidade (pode repetir)")
    parser.add_argument("--sem-manutencao", action="store_true",
                        help="nao executa VACUUM ANALYZE ao final")
    return parser


def main(argumentos: list[str] | None = None) -> int:
    args = construir_parser().parse_args(argumentos)

    try:
        if args.testar_conexao:
            testar_conexoes()
            return 0
        if args.status:
            exibir_status()
            return 0
        if args.validar:
            validar()
            return 0

        testar_conexoes()
        pipeline.executar(args.entidade, recarga_completa=args.full)
        if not args.sem_manutencao:
            pipeline.manutencao()
        return 0

    except Exception as erro:  # noqa: BLE001
        logger.error("Execucao interrompida: %s: %s", type(erro).__name__, erro)
        return 1


if __name__ == "__main__":
    sys.exit(main())
