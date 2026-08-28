"""Infraestrutura da ETL: registro de log e conexoes com origem e destino."""

from __future__ import annotations

import logging
import sys
from contextlib import contextmanager
from datetime import datetime
from typing import Iterator

import psycopg
import pyodbc

from etl.config import DESTINO, DIR_LOGS, ORIGEM

_LOGGER_CONFIGURADO = False


def obter_logger(nome: str = "etl") -> logging.Logger:
    """Devolve um logger que escreve simultaneamente no console e em arquivo."""
    global _LOGGER_CONFIGURADO

    logger = logging.getLogger(nome)
    if _LOGGER_CONFIGURADO:
        return logger

    DIR_LOGS.mkdir(parents=True, exist_ok=True)
    arquivo = DIR_LOGS / f"etl_{datetime.now():%Y%m%d}.log"

    formato = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    manipulador_arquivo = logging.FileHandler(arquivo, encoding="utf-8")
    manipulador_arquivo.setFormatter(formato)

    manipulador_console = logging.StreamHandler(sys.stdout)
    manipulador_console.setFormatter(formato)

    logger.setLevel(logging.INFO)
    logger.addHandler(manipulador_arquivo)
    logger.addHandler(manipulador_console)
    logger.propagate = False

    _LOGGER_CONFIGURADO = True
    return logger


@contextmanager
def conexao_origem() -> Iterator[pyodbc.Connection]:
    """Conexao somente leitura com o SQL Server (AdventureWorks)."""
    conexao = pyodbc.connect(ORIGEM.string_conexao(), autocommit=True)
    try:
        yield conexao
    finally:
        conexao.close()


@contextmanager
def conexao_destino(autocommit: bool = False) -> Iterator[psycopg.Connection]:
    """Conexao transacional com o PostgreSQL (Data Warehouse).

    Com autocommit desligado (padrao), o bloco inteiro de carga de uma
    entidade e atomico: ou toda a entidade e gravada e a marca d'agua
    avancada, ou nada e persistido.
    """
    conexao = psycopg.connect(DESTINO.string_conexao(), autocommit=autocommit)
    try:
        yield conexao
    finally:
        conexao.close()


def testar_conexoes() -> None:
    """Valida as duas pontas do pipeline antes de iniciar qualquer carga."""
    logger = obter_logger()

    with conexao_origem() as origem:
        cursor = origem.cursor()
        cursor.execute("SELECT @@VERSION;")
        versao = cursor.fetchone()[0].splitlines()[0]
        logger.info("Origem  OK | %s | %s", ORIGEM.servidor, versao.strip())

    with conexao_destino(autocommit=True) as destino:
        versao = destino.execute("SELECT version();").fetchone()[0]
        logger.info(
            "Destino OK | %s | %s",
            DESTINO.string_conexao_mascarada(),
            versao.split(",")[0],
        )
