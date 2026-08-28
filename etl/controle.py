"""Controle da carga incremental: marcas d'agua e log de execucao.

Estrategia adotada (change data capture por coluna de auditoria):

1. Antes de extrair uma entidade, a ETL le em ``meta.etl_controle`` a maior
   ``ModifiedDate`` ja processada com sucesso (a marca d'agua).
2. Subtrai dessa marca uma pequena janela de retrocesso (``lookback``), o que
   protege contra transacoes de longa duracao que gravam um ``ModifiedDate``
   anterior ao instante em que se tornam visiveis para outras sessoes.
3. Extrai do OLTP somente as linhas com ``ModifiedDate > marca_ajustada``.
4. Aplica os dados no DW por meio de operacoes idempotentes (``INSERT ...
   ON CONFLICT DO UPDATE``), de modo que reprocessar a mesma janela nao
   duplica registros.
5. So depois do commit bem-sucedido a marca d'agua avanca para a maior
   ``ModifiedDate`` observada no lote.

Esse encadeamento garante as duas propriedades desejadas: nenhum registro se
perde (a janela e sempre inclusiva por seguranca) e nenhum registro se
duplica (a aplicacao e idempotente).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

import psycopg

from etl.config import EXECUCAO

MARCA_INICIAL = datetime(1900, 1, 1)


@dataclass
class JanelaIncremental:
    """Intervalo de ``ModifiedDate`` a ser processado para uma entidade."""

    entidade: str
    marca_anterior: datetime
    marca_consulta: datetime  # marca_anterior - lookback
    primeira_carga: bool

    @property
    def descricao(self) -> str:
        if self.primeira_carga:
            return "carga inicial (full)"
        return f"incremental a partir de {self.marca_consulta:%Y-%m-%d %H:%M:%S}"


def obter_janela(conexao: psycopg.Connection, entidade: str) -> JanelaIncremental:
    """Le a marca d'agua da entidade e devolve a janela a ser extraida."""
    linha = conexao.execute(
        "SELECT dt_ultima_carga FROM meta.etl_controle WHERE nm_entidade = %s;",
        (entidade,),
    ).fetchone()

    if linha is None:
        raise ValueError(
            f"Entidade '{entidade}' nao registrada em meta.etl_controle. "
            "Execute o script sql/01_ddl_dw.sql."
        )

    marca_anterior: datetime = linha[0]
    primeira_carga = marca_anterior <= MARCA_INICIAL
    marca_consulta = (
        marca_anterior
        if primeira_carga
        else marca_anterior - timedelta(seconds=EXECUCAO.segundos_retrocesso)
    )

    return JanelaIncremental(
        entidade=entidade,
        marca_anterior=marca_anterior,
        marca_consulta=marca_consulta,
        primeira_carga=primeira_carga,
    )


def avancar_marca(
    conexao: psycopg.Connection,
    entidade: str,
    nova_marca: datetime | None,
    qt_registros: int,
) -> None:
    """Persiste a nova marca d'agua apos a carga bem-sucedida da entidade.

    A marca nunca retrocede: usa-se ``GREATEST`` para que uma execucao que
    processe um lote antigo (reprocessamento manual) nao invalide o avanco ja
    conquistado por execucoes anteriores.
    """
    if nova_marca is None:
        conexao.execute(
            """
            UPDATE meta.etl_controle
               SET qt_registros_ultima = 0,
                   dt_atualizacao      = CURRENT_TIMESTAMP
             WHERE nm_entidade = %s;
            """,
            (entidade,),
        )
        return

    conexao.execute(
        """
        UPDATE meta.etl_controle
           SET dt_ultima_carga     = GREATEST(dt_ultima_carga, %s),
               qt_registros_ultima = %s,
               qt_registros_total  = qt_registros_total + %s,
               dt_atualizacao      = CURRENT_TIMESTAMP
         WHERE nm_entidade = %s;
        """,
        (nova_marca, qt_registros, qt_registros, entidade),
    )


def novo_lote() -> uuid.UUID:
    """Identificador unico do ciclo completo de ETL."""
    return uuid.uuid4()


def registrar_inicio(
    conexao: psycopg.Connection,
    id_lote: uuid.UUID,
    entidade: str,
    fase: str,
    janela: JanelaIncremental,
) -> int:
    """Abre uma linha de auditoria em ``meta.etl_execucao``."""
    return conexao.execute(
        """
        INSERT INTO meta.etl_execucao
            (id_lote, nm_entidade, ds_fase, dt_inicio, ds_marca_agua_de, ds_status)
        VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s, 'EM_EXECUCAO')
        RETURNING id_execucao;
        """,
        (id_lote, entidade, fase, janela.marca_consulta),
    ).fetchone()[0]


def registrar_fim(
    conexao: psycopg.Connection,
    id_execucao: int,
    *,
    extraidos: int = 0,
    inseridos: int = 0,
    atualizados: int = 0,
    marca_ate: datetime | None = None,
    status: str = "SUCESSO",
    mensagem: str | None = None,
) -> None:
    """Fecha a linha de auditoria com o resultado da carga."""
    conexao.execute(
        """
        UPDATE meta.etl_execucao
           SET dt_fim            = CURRENT_TIMESTAMP,
               qt_extraidos      = %s,
               qt_inseridos      = %s,
               qt_atualizados    = %s,
               ds_marca_agua_ate = %s,
               ds_status         = %s,
               ds_mensagem       = %s
         WHERE id_execucao = %s;
        """,
        (extraidos, inseridos, atualizados, marca_ate, status, mensagem, id_execucao),
    )


def reiniciar_marcas(conexao: psycopg.Connection) -> None:
    """Zera todas as marcas d'agua, forcando uma recarga completa no proximo ciclo."""
    conexao.execute(
        """
        UPDATE meta.etl_controle
           SET dt_ultima_carga     = %s,
               qt_registros_ultima = 0,
               dt_atualizacao      = CURRENT_TIMESTAMP;
        """,
        (MARCA_INICIAL,),
    )
