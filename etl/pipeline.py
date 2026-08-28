"""Orquestracao do ciclo de ETL incremental.

Fluxo executado para cada entidade:

    marca d'agua  ->  extracao filtrada (SQL Server)
                  ->  ingestao em stg via COPY (PostgreSQL)
                  ->  transformacao idempotente stg -> dw
                  ->  avanco da marca d'agua
                  ->  COMMIT

Cada entidade e uma transacao independente. Uma falha em ``fato_compras`` nao
desfaz a carga ja confirmada de ``fato_vendas``, e a marca d'agua da entidade
que falhou permanece no valor anterior -- portanto a proxima execucao
reprocessa exatamente a janela pendente, sem lacunas.

O log de auditoria (``meta.etl_execucao``) usa uma conexao propria em modo
autocommit, para que o registro do erro sobreviva ao rollback da carga.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Iterable

import psycopg

from etl import controle, dimensao_tempo, transformacoes
from etl.config import DESTINO, EXECUCAO
from etl.consultas_origem import CATALOGO_EXTRACAO
from etl.infra import conexao_destino, conexao_origem, obter_logger

logger = obter_logger()

# As dimensoes sao carregadas antes dos fatos: a busca das chaves substitutas
# durante a carga do fato depende das dimensoes ja atualizadas.
ORDEM_CARGA: tuple[str, ...] = (
    "dim_produto",
    "dim_cliente",
    "dim_funcionario",
    "dim_territorio",
    "dim_geografia",
    "dim_fornecedor",
    "dim_promocao",
    "dim_metodo_envio",
    "fato_vendas",
    "fato_compras",
)


class ResultadoEntidade:
    def __init__(self, entidade: str) -> None:
        self.entidade = entidade
        self.extraidos = 0
        self.inseridos = 0
        self.atualizados = 0
        self.marca_ate: datetime | None = None
        self.segundos = 0.0
        self.status = "SUCESSO"
        self.mensagem: str | None = None


# ---------------------------------------------------------------------------
# Extracao + ingestao no staging
# ---------------------------------------------------------------------------

def _extrair_para_staging(
    cursor_origem,
    conexao_dw: psycopg.Connection,
    entidade: str,
    janela: controle.JanelaIncremental,
) -> tuple[int, datetime | None]:
    """Copia o recorte incremental do OLTP para a tabela de staging.

    Devolve a quantidade de linhas transferidas e a maior ``ModifiedDate``
    observada -- que sera a nova marca d'agua da entidade.
    """
    catalogo = CATALOGO_EXTRACAO[entidade]
    tabela_staging = catalogo["staging"]

    conexao_dw.execute(f"TRUNCATE TABLE {tabela_staging};")

    parametros = [janela.marca_consulta] * catalogo["parametros"]
    cursor_origem.execute(catalogo["sql"], parametros)

    colunas = [descricao[0] for descricao in cursor_origem.description]
    indice_modificacao = colunas.index("dt_modificacao_origem")
    lista_colunas = ", ".join(colunas)

    total = 0
    maior_marca: datetime | None = None

    comando_copy = f"COPY {tabela_staging} ({lista_colunas}) FROM STDIN"
    with conexao_dw.cursor() as cursor_dw, cursor_dw.copy(comando_copy) as copia:
        while True:
            lote = cursor_origem.fetchmany(EXECUCAO.tamanho_lote)
            if not lote:
                break
            for linha in lote:
                copia.write_row(tuple(linha))
                marca = linha[indice_modificacao]
                if marca is not None and (maior_marca is None or marca > maior_marca):
                    maior_marca = marca
            total += len(lote)
            logger.info("    %-16s | %8d linhas em staging", entidade, total)

    return total, maior_marca


# ---------------------------------------------------------------------------
# Transformacao staging -> dimensional
# ---------------------------------------------------------------------------

def _contar_resultado(cursor) -> tuple[int, int]:
    """Separa insercoes de atualizacoes a partir do RETURNING (xmax = 0)."""
    if cursor.description is None:
        return 0, 0
    linhas = cursor.fetchall()
    inseridos = sum(1 for linha in linhas if linha[0])
    return inseridos, len(linhas) - inseridos


def _transformar(conexao_dw: psycopg.Connection, entidade: str) -> tuple[int, int]:
    if entidade == "dim_produto":
        with conexao_dw.cursor() as cursor:
            cursor.execute(transformacoes.PRODUTO_SCD2_DETECTAR)
            cursor.execute(transformacoes.PRODUTO_SCD2_ENCERRAR)
            versoes_encerradas = cursor.rowcount
            cursor.execute(transformacoes.PRODUTO_SCD2_INSERIR)
            novas_versoes, _ = _contar_resultado(cursor)
        # Em SCD Tipo 2 toda mudanca gera uma linha nova; o numero de versoes
        # encerradas equivale as "atualizacoes" logicas de produtos existentes.
        return novas_versoes - versoes_encerradas, versoes_encerradas

    comando = transformacoes.SCD1.get(entidade) or transformacoes.FATOS.get(entidade)
    if comando is None:
        raise ValueError(f"Nenhuma transformacao definida para '{entidade}'.")

    with conexao_dw.cursor() as cursor:
        cursor.execute(comando)
        return _contar_resultado(cursor)


# ---------------------------------------------------------------------------
# Carga de uma entidade
# ---------------------------------------------------------------------------

def _carregar_entidade(
    cursor_origem,
    conexao_dw: psycopg.Connection,
    conexao_log: psycopg.Connection,
    id_lote,
    entidade: str,
) -> ResultadoEntidade:
    resultado = ResultadoEntidade(entidade)
    inicio = time.perf_counter()

    janela = controle.obter_janela(conexao_dw, entidade)
    fase = "DIMENSAO" if entidade.startswith("dim_") else "FATO"
    id_execucao = controle.registrar_inicio(conexao_log, id_lote, entidade, fase, janela)

    logger.info("  %-16s | %s", entidade, janela.descricao)

    try:
        extraidos, maior_marca = _extrair_para_staging(
            cursor_origem, conexao_dw, entidade, janela
        )
        resultado.extraidos = extraidos
        resultado.marca_ate = maior_marca

        if extraidos == 0:
            logger.info("  %-16s | nada a processar", entidade)
            controle.avancar_marca(conexao_dw, entidade, None, 0)
        else:
            resultado.inseridos, resultado.atualizados = _transformar(conexao_dw, entidade)
            controle.avancar_marca(conexao_dw, entidade, maior_marca, extraidos)

        conexao_dw.commit()

    except Exception as erro:  # noqa: BLE001 - a excecao e registrada e repropagada
        conexao_dw.rollback()
        resultado.status = "ERRO"
        resultado.mensagem = f"{type(erro).__name__}: {erro}"
        controle.registrar_fim(
            conexao_log, id_execucao, status="ERRO", mensagem=resultado.mensagem
        )
        logger.error("  %-16s | FALHOU: %s", entidade, resultado.mensagem)
        raise

    resultado.segundos = time.perf_counter() - inicio
    controle.registrar_fim(
        conexao_log,
        id_execucao,
        extraidos=resultado.extraidos,
        inseridos=resultado.inseridos,
        atualizados=resultado.atualizados,
        marca_ate=resultado.marca_ate,
    )

    logger.info(
        "  %-16s | extraidos=%d inseridos=%d atualizados=%d | %.2fs",
        entidade,
        resultado.extraidos,
        resultado.inseridos,
        resultado.atualizados,
        resultado.segundos,
    )
    return resultado


# ---------------------------------------------------------------------------
# Ciclo completo
# ---------------------------------------------------------------------------

def executar(
    entidades: Iterable[str] | None = None,
    *,
    recarga_completa: bool = False,
) -> list[ResultadoEntidade]:
    """Executa um ciclo de ETL sobre as entidades informadas (padrao: todas)."""
    alvos = tuple(entidades) if entidades else ORDEM_CARGA
    desconhecidas = [e for e in alvos if e not in CATALOGO_EXTRACAO]
    if desconhecidas:
        raise ValueError(f"Entidades desconhecidas: {', '.join(desconhecidas)}")

    id_lote = controle.novo_lote()
    inicio = time.perf_counter()

    logger.info("=" * 78)
    logger.info("CICLO DE ETL | lote %s", id_lote)
    logger.info("Destino: %s", DESTINO.string_conexao_mascarada())
    logger.info("=" * 78)

    resultados: list[ResultadoEntidade] = []

    with conexao_origem() as origem, conexao_destino() as conexao_dw, conexao_destino(
        autocommit=True
    ) as conexao_log:

        if recarga_completa:
            logger.warning("Recarga completa solicitada: marcas d'agua reiniciadas.")
            controle.reiniciar_marcas(conexao_dw)
            conexao_dw.commit()

        cursor_origem = origem.cursor()

        # --- dimensao tempo -------------------------------------------------
        inicio_cal, fim_cal = dimensao_tempo.intervalo_necessario(cursor_origem)
        inicio_cal = min(inicio_cal, EXECUCAO.data_inicio_calendario)
        fim_cal = max(fim_cal, EXECUCAO.data_fim_calendario)
        novas_datas = dimensao_tempo.carregar(conexao_dw, inicio_cal, fim_cal)
        conexao_dw.commit()
        logger.info(
            "  %-16s | intervalo %s a %s | %d datas novas",
            "dim_tempo",
            inicio_cal,
            fim_cal,
            novas_datas,
        )

        # --- demais entidades ----------------------------------------------
        for entidade in alvos:
            resultados.append(
                _carregar_entidade(
                    cursor_origem, conexao_dw, conexao_log, id_lote, entidade
                )
            )

    duracao = time.perf_counter() - inicio
    total_extraidos = sum(r.extraidos for r in resultados)
    logger.info("-" * 78)
    logger.info(
        "CICLO CONCLUIDO | %d entidades | %d registros | %.2fs",
        len(resultados),
        total_extraidos,
        duracao,
    )
    logger.info("=" * 78)
    return resultados


def manutencao() -> None:
    """Atualiza as estatisticas do planejador apos uma carga volumosa."""
    with conexao_destino(autocommit=True) as conexao:
        for tabela in ("dw.dim_produto", "dw.dim_cliente", "dw.dim_geografia",
                       "dw.fato_vendas", "dw.fato_compras"):
            conexao.execute(f"VACUUM ANALYZE {tabela};")
    logger.info("Estatisticas do PostgreSQL atualizadas (VACUUM ANALYZE).")
