"""Gera o dicionario de dados do Data Warehouse a partir do catalogo do PostgreSQL.

    python docs/gerar_dicionario.py

Produz ``docs/dicionario_dados.md``. Extrair a documentacao do proprio
catalogo (information_schema e pg_description) garante que o dicionario nunca
divirja do que esta efetivamente implantado no banco.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from etl.infra import conexao_destino  # noqa: E402

SAIDA = Path(__file__).resolve().parent / "dicionario_dados.md"

CONSULTA_TABELAS = """
SELECT c.relnamespace::regnamespace::text AS esquema,
       c.relname                          AS tabela,
       obj_description(c.oid, 'pg_class') AS descricao,
       c.reltuples::bigint                AS estimativa_linhas
  FROM pg_class AS c
 WHERE c.relkind = 'r'
   AND c.relnamespace::regnamespace::text IN ('dw', 'meta')
 ORDER BY CASE c.relnamespace::regnamespace::text
               WHEN 'dw' THEN 1 ELSE 2 END,
          CASE WHEN c.relname LIKE 'fato%' THEN 1
               WHEN c.relname LIKE 'dim%'  THEN 2
               ELSE 3 END,
          c.relname;
"""

CONSULTA_COLUNAS = """
SELECT a.attname                                            AS coluna,
       format_type(a.atttypid, a.atttypmod)                 AS tipo,
       NOT a.attnotnull                                     AS aceita_nulo,
       pg_get_expr(d.adbin, d.adrelid)                      AS padrao,
       col_description(a.attrelid, a.attnum)                AS descricao,
       EXISTS (SELECT 1 FROM pg_constraint AS k
                WHERE k.conrelid = a.attrelid AND k.contype = 'p'
                  AND a.attnum = ANY (k.conkey))            AS chave_primaria,
       (SELECT cf.confrelid::regclass::text FROM pg_constraint AS cf
         WHERE cf.conrelid = a.attrelid AND cf.contype = 'f'
           AND a.attnum = ANY (cf.conkey) LIMIT 1)          AS referencia
  FROM pg_attribute AS a
  LEFT JOIN pg_attrdef AS d ON d.adrelid = a.attrelid AND d.adnum = a.attnum
 WHERE a.attrelid = %s::regclass
   AND a.attnum > 0
   AND NOT a.attisdropped
 ORDER BY a.attnum;
"""


def _escapar(texto: str | None) -> str:
    if not texto:
        return ""
    return texto.replace("|", "\\|").replace("\n", " ")


def gerar() -> Path:
    linhas: list[str] = [
        "# Dicionario de Dados - Data Warehouse AdventureWorks",
        "",
        "> Documento gerado automaticamente a partir do catalogo do PostgreSQL",
        "> (`pg_class`, `pg_attribute`, `pg_description`) pelo script",
        "> `docs/gerar_dicionario.py`. Para atualiza-lo apos qualquer alteracao",
        "> de DDL, basta reexecutar o script.",
        "",
        "## Convencoes de nomenclatura",
        "",
        "| Prefixo | Significado | Exemplo |",
        "|---|---|---|",
        "| `sk_` | *surrogate key* (chave substituta gerada pelo DW) | `sk_produto` |",
        "| `id_` | chave natural herdada do sistema de origem | `id_produto` |",
        "| `cd_` | codigo alfanumerico de negocio | `cd_produto` |",
        "| `nm_` | nome ou descritor curto | `nm_categoria` |",
        "| `ds_` | descricao textual | `ds_cargo` |",
        "| `dt_` | data ou data e hora | `dt_pedido` |",
        "| `vl_` | valor monetario | `vl_liquido` |",
        "| `qt_` | quantidade | `qt_vendida` |",
        "| `pc_` | percentual | `pc_desconto_unitario` |",
        "| `nr_` | numero sequencial ou ordinal | `nr_versao` |",
        "| `fl_` | indicador logico (*flag*) | `fl_corrente` |",
        "",
        "`DD` identifica uma *dimensao degenerada*: atributo de identificacao da",
        "transacao que reside na propria tabela fato, por nao possuir outros",
        "atributos que justifiquem uma dimensao propria.",
        "",
    ]

    with conexao_destino(autocommit=True) as conexao:
        tabelas = conexao.execute(CONSULTA_TABELAS).fetchall()

        esquema_atual = None
        for esquema, tabela, descricao, estimativa in tabelas:
            if esquema != esquema_atual:
                esquema_atual = esquema
                titulo = ("Camada dimensional (`dw`)" if esquema == "dw"
                          else "Metadados de controle (`meta`)")
                linhas += ["", f"## {titulo}", ""]

            contagem = conexao.execute(
                f"SELECT count(*) FROM {esquema}.{tabela};"
            ).fetchone()[0]

            linhas += [
                f"### `{esquema}.{tabela}`",
                "",
                f"{descricao or 'Sem descricao registrada.'}",
                "",
                f"**Linhas carregadas:** {contagem:,}".replace(",", "."),
                "",
                "| Coluna | Tipo | Nulo | Chave | Descricao |",
                "|---|---|---|---|---|",
            ]

            colunas = conexao.execute(
                CONSULTA_COLUNAS, (f"{esquema}.{tabela}",)
            ).fetchall()

            for (coluna, tipo, aceita_nulo, _padrao, desc_coluna,
                 chave_primaria, referencia) in colunas:
                if chave_primaria:
                    chave = "PK"
                elif referencia:
                    chave = f"FK -> `{referencia}`"
                else:
                    chave = ""
                nulo = "sim" if aceita_nulo else "nao"
                linhas.append(
                    f"| `{coluna}` | {tipo} | {nulo} | {chave} | "
                    f"{_escapar(desc_coluna)} |"
                )
            linhas.append("")

    SAIDA.write_text("\n".join(linhas), encoding="utf-8")
    return SAIDA


if __name__ == "__main__":
    print(f"Dicionario gerado em: {gerar()}")
