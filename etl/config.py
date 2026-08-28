"""Configuracao central da ETL.

Le o arquivo .env (ou as variaveis de ambiente do sistema) e expoe as
credenciais e parametros de execucao em estruturas imutaveis, evitando que
qualquer credencial fique escrita no codigo-fonte versionado.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
DIR_LOGS = RAIZ_PROJETO / "logs"
DIR_SQL = RAIZ_PROJETO / "sql"

load_dotenv(RAIZ_PROJETO / ".env")


def _texto(chave: str, padrao: str = "") -> str:
    return os.getenv(chave, padrao).strip()


def _inteiro(chave: str, padrao: int) -> int:
    try:
        return int(os.getenv(chave, str(padrao)))
    except ValueError:
        return padrao


def _data(chave: str, padrao: str) -> date:
    return date.fromisoformat(_texto(chave, padrao))


@dataclass(frozen=True)
class ConfigOrigem:
    """Parametros de conexao com o SQL Server (AdventureWorks / OLTP)."""

    servidor: str
    banco: str
    driver: str
    autenticacao_integrada: bool
    usuario: str
    senha: str
    confiar_certificado: bool

    def string_conexao(self) -> str:
        partes = [
            f"DRIVER={{{self.driver}}}",
            f"SERVER={self.servidor}",
            f"DATABASE={self.banco}",
        ]
        if self.autenticacao_integrada:
            partes.append("Trusted_Connection=yes")
        else:
            partes.append(f"UID={self.usuario}")
            partes.append(f"PWD={self.senha}")
        if self.confiar_certificado:
            partes.append("TrustServerCertificate=yes")
        partes.append("Encrypt=no")
        return ";".join(partes) + ";"


@dataclass(frozen=True)
class ConfigDestino:
    """Parametros de conexao com o PostgreSQL (Data Warehouse / OLAP)."""

    host: str
    porta: int
    banco: str
    usuario: str
    senha: str

    def string_conexao(self) -> str:
        return (
            f"host={self.host} port={self.porta} dbname={self.banco} "
            f"user={self.usuario} password={self.senha}"
        )

    def string_conexao_mascarada(self) -> str:
        return (
            f"host={self.host} port={self.porta} dbname={self.banco} "
            f"user={self.usuario} password=***"
        )


@dataclass(frozen=True)
class ConfigExecucao:
    """Parametros que governam o comportamento da carga incremental."""

    tamanho_lote: int
    segundos_retrocesso: int
    data_inicio_calendario: date
    data_fim_calendario: date


ORIGEM = ConfigOrigem(
    servidor=_texto("SRC_SERVER", r"localhost\SQLEXPRESS"),
    banco=_texto("SRC_DATABASE", "AdventureWorks2022"),
    driver=_texto("SRC_DRIVER", "ODBC Driver 18 for SQL Server"),
    autenticacao_integrada=_texto("SRC_TRUSTED_CONNECTION", "yes").lower() == "yes",
    usuario=_texto("SRC_USER"),
    senha=_texto("SRC_PASSWORD"),
    confiar_certificado=_texto("SRC_TRUST_SERVER_CERTIFICATE", "yes").lower() == "yes",
)

DESTINO = ConfigDestino(
    host=_texto("DW_HOST", "localhost"),
    porta=_inteiro("DW_PORT", 5432),
    banco=_texto("DW_DATABASE", "dw_adventureworks"),
    usuario=_texto("DW_USER", "dw_user"),
    senha=_texto("DW_PASSWORD", "dw_pass"),
)

EXECUCAO = ConfigExecucao(
    tamanho_lote=_inteiro("ETL_BATCH_SIZE", 20000),
    segundos_retrocesso=_inteiro("ETL_LOOKBACK_SECONDS", 2),
    data_inicio_calendario=_data("ETL_DATA_INICIO", "2010-01-01"),
    data_fim_calendario=_data("ETL_DATA_FIM", "2015-12-31"),
)
