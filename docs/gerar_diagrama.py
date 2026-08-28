"""Gera a figura do modelo estrela em PNG.

    python docs/gerar_diagrama.py

Produz ``docs/modelo_estrela.png``, utilizado no artigo e no README. O
desenho e programatico (matplotlib) para que o diagrama permaneca
versionado como codigo e possa ser regerado apos qualquer mudanca no modelo.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

SAIDA = Path(__file__).resolve().parent / "modelo_estrela.png"

COR_FATO = "#1f3864"
COR_FATO_BORDA = "#0d1b33"
COR_CONFORMADA = "#c55a11"
COR_CONFORMADA_BORDA = "#843c0c"
COR_DIM = "#375623"
COR_DIM_BORDA = "#243d17"
COR_LINHA = "#8c8c8c"

# (rotulo, atributos, x, y, largura, altura, tipo)
FATOS = [
    (
        "FATO_VENDAS",
        "grao: item de pedido de venda\n\n"
        "12 chaves estrangeiras\n"
        "id_item_venda (DD)\n"
        "nr_pedido (DD)\n\n"
        "qt_vendida\nvl_bruto\nvl_desconto\nvl_liquido\n"
        "vl_custo_total\nvl_margem_bruta\nvl_frete_rateado\n"
        "vl_imposto_rateado\nqt_dias_entrega\nfl_entrega_atrasada",
        -3.55, 0.0, 2.5, 5.0,
    ),
    (
        "FATO_COMPRAS",
        "grao: item de ordem de compra\n\n"
        "8 chaves estrangeiras\n"
        "id_item_compra (DD)\n"
        "id_ordem_compra (DD)\n\n"
        "qt_pedida\nqt_recebida\nqt_rejeitada\nqt_aceita\n"
        "vl_total_linha\nvl_frete_rateado\nvl_imposto_rateado\n"
        "qt_dias_recebimento\nfl_recebimento_atrasado",
        3.55, 0.0, 2.5, 5.0,
    ),
]

CONFORMADAS = [
    ("DIM_TEMPO", "sk_tempo (AAAAMMDD)\nnr_ano | nr_trimestre\nnr_mes | nm_mes\nfl_fim_semana", 0.0, 3.55),
    ("DIM_PRODUTO", "sk_produto\nid_produto\nnm_categoria\nnm_subcategoria\nSCD Tipo 2", 0.0, 1.75),
    ("DIM_FUNCIONARIO", "sk_funcionario\nnm_funcionario\nds_cargo\nvl_cota_vendas\nmultiplos papeis", 0.0, -0.05),
    ("DIM_METODO_ENVIO", "sk_metodo_envio\nnm_metodo_envio\nvl_taxa_base", 0.0, -1.75),
    ("DIM_STATUS_PEDIDO", "sk_status\nds_dominio\nnm_status", 0.0, -3.35),
]

EXCLUSIVAS_VENDAS = [
    ("DIM_CLIENTE", "sk_cliente\nnm_cliente\ntp_cliente\nds_email", -7.3, 3.4),
    ("DIM_TERRITORIO", "sk_territorio\nnm_territorio\nnm_grupo\nnm_pais", -7.3, 1.6),
    ("DIM_GEOGRAFIA", "sk_geografia\nds_cidade\nnm_estado\nnm_pais", -7.3, -0.2),
    ("DIM_PROMOCAO", "sk_promocao\nds_promocao\ntp_promocao\npc_desconto", -7.3, -2.0),
    ("DIM_CANAL_VENDA", "sk_canal\nnm_canal", -7.3, -3.6),
]

EXCLUSIVAS_COMPRAS = [
    ("DIM_FORNECEDOR", "sk_fornecedor\nnm_fornecedor\nds_nivel_credito\nfl_preferencial", 7.3, -0.05),
]

LARGURA_DIM = 2.35
ALTURA_DIM = 1.35


def _caixa(eixo, rotulo, atributos, x, y, largura, altura, cor, cor_borda,
           tamanho_titulo=8.5, tamanho_texto=6.4):
    eixo.add_patch(
        FancyBboxPatch(
            (x - largura / 2, y - altura / 2),
            largura, altura,
            boxstyle="round,pad=0.04,rounding_size=0.08",
            linewidth=1.4, edgecolor=cor_borda, facecolor=cor, zorder=3,
        )
    )
    eixo.text(x, y + altura / 2 - 0.2, rotulo, ha="center", va="center",
              fontsize=tamanho_titulo, fontweight="bold", color="white", zorder=4)
    eixo.plot([x - largura / 2 + 0.12, x + largura / 2 - 0.12],
              [y + altura / 2 - 0.33, y + altura / 2 - 0.33],
              color="white", linewidth=0.8, alpha=0.55, zorder=4)
    eixo.text(x, y + altura / 2 - 0.42, atributos, ha="center", va="top",
              fontsize=tamanho_texto, color="white", linespacing=1.35, zorder=4)


def _ligacao(eixo, x1, y1, x2, y2):
    eixo.plot([x1, x2], [y1, y2], color=COR_LINHA, linewidth=1.0,
              linestyle="-", zorder=1, alpha=0.85)


def gerar() -> Path:
    figura, eixo = plt.subplots(figsize=(16, 9.4))
    eixo.set_xlim(-9.2, 9.2)
    eixo.set_ylim(-5.1, 5.4)
    eixo.axis("off")

    x_vendas, y_vendas = FATOS[0][2], FATOS[0][3]
    x_compras, y_compras = FATOS[1][2], FATOS[1][3]

    # Ligacoes desenhadas antes das caixas, para passarem por tras delas.
    for _, _, x, y in CONFORMADAS:
        _ligacao(eixo, x_vendas, y_vendas, x, y)
        _ligacao(eixo, x_compras, y_compras, x, y)
    for _, _, x, y in EXCLUSIVAS_VENDAS:
        _ligacao(eixo, x_vendas, y_vendas, x, y)
    for _, _, x, y in EXCLUSIVAS_COMPRAS:
        _ligacao(eixo, x_compras, y_compras, x, y)

    for rotulo, atributos, x, y, largura, altura in FATOS:
        _caixa(eixo, rotulo, atributos, x, y, largura, altura,
               COR_FATO, COR_FATO_BORDA, tamanho_titulo=10, tamanho_texto=6.8)

    for rotulo, atributos, x, y in CONFORMADAS:
        _caixa(eixo, rotulo, atributos, x, y, LARGURA_DIM, ALTURA_DIM,
               COR_CONFORMADA, COR_CONFORMADA_BORDA)

    for rotulo, atributos, x, y in EXCLUSIVAS_VENDAS + EXCLUSIVAS_COMPRAS:
        _caixa(eixo, rotulo, atributos, x, y, LARGURA_DIM, ALTURA_DIM,
               COR_DIM, COR_DIM_BORDA)

    eixo.text(0, 5.15, "Modelo Estrela - Data Warehouse AdventureWorks",
              ha="center", va="center", fontsize=15, fontweight="bold",
              color="#1f1f1f")
    eixo.text(0, 4.72,
              "Duas tabelas fato conectadas por dimensoes conformadas "
              "(coluna central)",
              ha="center", va="center", fontsize=9.5, color="#555555")

    legenda = [
        (COR_FATO, "Tabela fato"),
        (COR_CONFORMADA, "Dimensao conformada (compartilhada)"),
        (COR_DIM, "Dimensao exclusiva de um processo"),
    ]
    for indice, (cor, texto) in enumerate(legenda):
        x_legenda = -6.6 + indice * 4.6
        eixo.add_patch(
            FancyBboxPatch((x_legenda, -4.92), 0.32, 0.2,
                           boxstyle="round,pad=0.02,rounding_size=0.04",
                           linewidth=0.8, edgecolor="#333333", facecolor=cor)
        )
        eixo.text(x_legenda + 0.45, -4.82, texto, ha="left", va="center",
                  fontsize=8.6, color="#333333")

    figura.tight_layout()
    figura.savefig(SAIDA, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(figura)
    return SAIDA


if __name__ == "__main__":
    print(f"Diagrama gerado em: {gerar()}")
