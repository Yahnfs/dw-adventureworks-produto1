"""Gera o artigo academico em .docx conforme o Guia Unisales (6. ed., 2024).

    python docs/artigo/gerar_artigo.py
    python docs/artigo/gerar_artigo.py --sem-apendices

Regras de formatacao aplicadas, com o item do Guia entre parenteses:

* A4; margens superior e esquerda 3 cm, inferior e direita 2 cm (1.2.1, 1.2.2)
* Arial 12, entrelinha 1,0 em todo o texto (1.2.3)
* Fonte 10 em citacoes longas, legendas e fontes de ilustracoes, texto de
  quadros e paginacao (1.2.3)
* Paragrafos SEM recuo de primeira linha, 0 pt antes e 6 pt depois (1.2.4)
* Titulos "1 MAIUSCULAS NEGRITO" e "1.1 MAIUSCULAS NORMAL", 0 pt antes e
  0 pt depois, sem linha em branco antes do texto (1.2.5)
* Paginacao em Arial 10 (1.2.6)
* Ilustracoes centralizadas e com borda; titulo acima, com travessao, e fonte
  abaixo (1.2.10)
* Quadros fechados, texto em fonte 10 (1.2.12)
* Citacao direta longa com recuo de 4 cm, fonte 10, entrelinha simples e sem
  aspas (2.1.2)
* Estrutura: TITULO, autoria, RESUMO, ABSTRACT, 1 INTRODUCAO, 2 REFERENCIAL
  TEORICO, 3 METODOLOGIA, 4 RESULTADOS E DISCUSSAO, 5 CONSIDERACOES FINAIS,
  REFERENCIAS, APENDICES (1.3.1)
* Referencias em ordem alfabetica, entrelinha simples, separadas por um
  paragrafo em branco (3.1)
"""

from __future__ import annotations

import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

DIR_ARTIGO = Path(__file__).resolve().parent
DIR_DOCS = DIR_ARTIGO.parent
DIR_RAIZ = DIR_DOCS.parent
SAIDA = DIR_ARTIGO / "Artigo_DW_AdventureWorks_Unisales.docx"
FIGURA_MODELO = DIR_DOCS / "modelo_estrela.png"

FONTE = "Arial"
FONTE_CODIGO = "Consolas"
FONTE_PROPRIA = "Fonte: elaboração própria (2026)."

_contadores = {"quadro": 0, "figura": 0}


def _proximo(tipo: str) -> int:
    _contadores[tipo] += 1
    return _contadores[tipo]


# ---------------------------------------------------------------------------
# Formatacao base
# ---------------------------------------------------------------------------

def configurar_documento() -> Document:
    documento = Document()

    secao = documento.sections[0]
    secao.page_width, secao.page_height = Cm(21.0), Cm(29.7)
    secao.top_margin, secao.left_margin = Cm(3.0), Cm(3.0)
    secao.bottom_margin, secao.right_margin = Cm(2.0), Cm(2.0)

    estilo = documento.styles["Normal"]
    estilo.font.name = FONTE
    estilo.font.size = Pt(12)
    estilo.element.rPr.rFonts.set(qn("w:eastAsia"), FONTE)
    formato = estilo.paragraph_format
    formato.line_spacing_rule = WD_LINE_SPACING.SINGLE
    formato.space_before = Pt(0)
    formato.space_after = Pt(6)

    _numerar_paginas(secao)
    return documento


def _numerar_paginas(secao) -> None:
    """Numero da pagina no cabecalho, a direita, em Arial 10 (Guia 1.2.6)."""
    paragrafo = secao.header.paragraphs[0]
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    paragrafo.paragraph_format.space_after = Pt(0)
    execucao = paragrafo.add_run()
    _fonte(execucao, 10)

    inicio = OxmlElement("w:fldChar")
    inicio.set(qn("w:fldCharType"), "begin")
    instrucao = OxmlElement("w:instrText")
    instrucao.set(qn("xml:space"), "preserve")
    instrucao.text = "PAGE"
    fim = OxmlElement("w:fldChar")
    fim.set(qn("w:fldCharType"), "end")
    for elemento in (inicio, instrucao, fim):
        execucao._r.append(elemento)


def _fonte(execucao, tamanho=12, negrito=False, italico=False, nome=FONTE):
    execucao.font.name = nome
    execucao.font.size = Pt(tamanho)
    execucao.bold = negrito
    execucao.italic = italico
    execucao._element.rPr.rFonts.set(qn("w:eastAsia"), nome)
    return execucao


def _sombrear(celula, cor_hex: str) -> None:
    elemento = OxmlElement("w:shd")
    elemento.set(qn("w:val"), "clear")
    elemento.set(qn("w:fill"), cor_hex)
    celula._tc.get_or_add_tcPr().append(elemento)


def vazio(doc: Document, tamanho: int = 12) -> None:
    """Paragrafo em branco: o 'enter' previsto pelo Guia entre elementos."""
    paragrafo = doc.add_paragraph()
    paragrafo.paragraph_format.space_after = Pt(0)
    _fonte(paragrafo.add_run(""), tamanho)


# ---------------------------------------------------------------------------
# Elementos pre-textuais
# ---------------------------------------------------------------------------

def titulo_trabalho(doc: Document, texto: str, subtitulo: str) -> None:
    paragrafo = doc.add_paragraph()
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragrafo.paragraph_format.space_after = Pt(0)
    _fonte(paragrafo.add_run(texto.upper()), 12, negrito=True)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.paragraph_format.space_after = Pt(12)
    _fonte(sub.add_run(subtitulo), 12, negrito=True)


def autoria(doc: Document, linhas: list[str]) -> None:
    for texto in linhas:
        paragrafo = doc.add_paragraph()
        paragrafo.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        paragrafo.paragraph_format.space_after = Pt(0)
        _fonte(paragrafo.add_run(texto), 12)
    vazio(doc)


def bloco_resumo(doc: Document, rotulo: str, texto: str,
                 rotulo_chaves: str, chaves: str) -> None:
    corpo = doc.add_paragraph()
    corpo.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    corpo.paragraph_format.space_after = Pt(6)
    _fonte(corpo.add_run(f"{rotulo}: "), 12, negrito=True)
    _fonte(corpo.add_run(texto), 12)

    palavras = doc.add_paragraph()
    palavras.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    palavras.paragraph_format.space_after = Pt(12)
    _fonte(palavras.add_run(f"{rotulo_chaves}: "), 12, negrito=True)
    _fonte(palavras.add_run(chaves), 12)


# ---------------------------------------------------------------------------
# Titulos de secao (Guia 1.2.5)
# ---------------------------------------------------------------------------

def _titulo(doc: Document, texto: str, negrito: bool, maiusculas: bool):
    paragrafo = doc.add_paragraph()
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragrafo.paragraph_format.space_before = Pt(0)
    paragrafo.paragraph_format.space_after = Pt(0)
    paragrafo.paragraph_format.keep_with_next = True
    _fonte(paragrafo.add_run(texto.upper() if maiusculas else texto),
           12, negrito=negrito)
    return paragrafo


def secao(doc: Document, numero: str, texto: str) -> None:
    """Secao primaria: tamanho 12, negrito, maiusculas."""
    vazio(doc)
    _titulo(doc, f"{numero} {texto}".strip(), negrito=True, maiusculas=True)


def subsecao(doc: Document, numero: str, texto: str) -> None:
    """Secao secundaria: tamanho 12, normal, maiusculas."""
    vazio(doc)
    _titulo(doc, f"{numero} {texto}", negrito=False, maiusculas=True)


# ---------------------------------------------------------------------------
# Corpo do texto
# ---------------------------------------------------------------------------

def par(doc: Document, texto: str):
    paragrafo = doc.add_paragraph()
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragrafo.paragraph_format.space_after = Pt(6)
    _fonte(paragrafo.add_run(texto), 12)
    return paragrafo


def citacao(doc: Document, texto: str, fonte: str) -> None:
    """Citacao direta longa: recuo 4 cm, fonte 10, 0 pt antes e 6 pt depois."""
    paragrafo = doc.add_paragraph()
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragrafo.paragraph_format.left_indent = Cm(4.0)
    paragrafo.paragraph_format.space_before = Pt(0)
    paragrafo.paragraph_format.space_after = Pt(6)
    _fonte(paragrafo.add_run(f"{texto} ({fonte})."), 10)


# ---------------------------------------------------------------------------
# Ilustracoes e quadros (Guia 1.2.10 e 1.2.12)
# ---------------------------------------------------------------------------

def legenda_superior(doc: Document, texto: str) -> None:
    paragrafo = doc.add_paragraph()
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragrafo.paragraph_format.space_before = Pt(0)
    paragrafo.paragraph_format.space_after = Pt(0)
    paragrafo.paragraph_format.keep_with_next = True
    _fonte(paragrafo.add_run(texto), 10)


def legenda_fonte(doc: Document, texto: str) -> None:
    paragrafo = doc.add_paragraph()
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragrafo.paragraph_format.space_before = Pt(0)
    paragrafo.paragraph_format.space_after = Pt(6)
    _fonte(paragrafo.add_run(texto), 10)


def figura(doc: Document, caminho: Path, titulo: str, fonte: str,
           largura_cm: float = 14.5) -> None:
    numero = _proximo("figura")
    legenda_superior(doc, f"Figura {numero} – {titulo}")

    tabela = doc.add_table(rows=1, cols=1)
    tabela.style = "Table Grid"
    tabela.alignment = WD_TABLE_ALIGNMENT.CENTER
    celula = tabela.rows[0].cells[0]
    celula.text = ""
    paragrafo = celula.paragraphs[0]
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragrafo.paragraph_format.space_after = Pt(0)
    paragrafo.add_run().add_picture(str(caminho), width=Cm(largura_cm))

    legenda_fonte(doc, fonte)


def _margens_celulas(tabela, cm: float = 0.04) -> None:
    """Reduz o espacamento interno das celulas, adensando quadros extensos."""
    largura = str(int(cm * 567))  # centimetros -> twips
    propriedades = tabela._tbl.tblPr
    margens = OxmlElement("w:tblCellMar")
    for lado in ("top", "left", "bottom", "right"):
        elemento = OxmlElement(f"w:{lado}")
        elemento.set(qn("w:w"), largura)
        elemento.set(qn("w:type"), "dxa")
        margens.append(elemento)
    propriedades.append(margens)


def quadro(doc: Document, titulo: str, cabecalho: list[str],
           linhas: list[list[str]], fonte: str, tamanho: float = 10,
           larguras: list[float] | None = None,
           compacto: bool = False) -> None:
    if titulo:
        legenda_superior(doc, f"Quadro {_proximo('quadro')} – {titulo}")

    tabela = doc.add_table(rows=1, cols=len(cabecalho))
    tabela.style = "Table Grid"
    tabela.alignment = WD_TABLE_ALIGNMENT.CENTER

    for indice, texto in enumerate(cabecalho):
        celula = tabela.rows[0].cells[indice]
        celula.text = ""
        paragrafo = celula.paragraphs[0]
        paragrafo.paragraph_format.space_after = Pt(0)
        _fonte(paragrafo.add_run(texto), tamanho, negrito=True)
        _sombrear(celula, "D9D9D9")

    for valores in linhas:
        celulas = tabela.add_row().cells
        for indice, texto in enumerate(valores):
            celula = celulas[indice]
            celula.text = ""
            paragrafo = celula.paragraphs[0]
            paragrafo.paragraph_format.space_after = Pt(0)
            _fonte(paragrafo.add_run(texto), tamanho)

    if compacto:
        _margens_celulas(tabela)

    if larguras:
        for linha in tabela.rows:
            for indice, largura in enumerate(larguras):
                linha.cells[indice].width = Cm(largura)

    if fonte:
        legenda_fonte(doc, fonte)


def quadro_codigo(doc: Document, titulo: str, linhas: list[str],
                  fonte: str = FONTE_PROPRIA, tamanho: float = 9,
                  compacto: bool = False) -> None:
    """Trecho de codigo emoldurado, apresentado como quadro (Guia 1.2.12)."""
    legenda_superior(doc, f"Quadro {_proximo('quadro')} – {titulo}")

    tabela = doc.add_table(rows=1, cols=1)
    tabela.style = "Table Grid"
    tabela.alignment = WD_TABLE_ALIGNMENT.CENTER
    if compacto:
        _margens_celulas(tabela)
    celula = tabela.rows[0].cells[0]
    _sombrear(celula, "F2F2F2")
    celula.text = ""

    primeiro = True
    for linha in linhas:
        paragrafo = celula.paragraphs[0] if primeiro else celula.add_paragraph()
        primeiro = False
        paragrafo.alignment = WD_ALIGN_PARAGRAPH.LEFT
        paragrafo.paragraph_format.space_before = Pt(0)
        paragrafo.paragraph_format.space_after = Pt(0)
        _fonte(paragrafo.add_run(linha if linha.strip() else " "),
               tamanho, nome=FONTE_CODIGO)

    legenda_fonte(doc, fonte)


def referencia(doc: Document, partes: list[tuple[str, bool]]) -> None:
    paragrafo = doc.add_paragraph()
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragrafo.paragraph_format.space_before = Pt(0)
    paragrafo.paragraph_format.space_after = Pt(0)
    for texto, negrito in partes:
        _fonte(paragrafo.add_run(texto), 12, negrito=negrito)
    vazio(doc)


def apendice(doc: Document, letra: str, texto: str) -> None:
    doc.add_page_break()
    _titulo(doc, f"APÊNDICE {letra} – {texto}",
            negrito=True, maiusculas=True)
    vazio(doc)


# ---------------------------------------------------------------------------
# Leitura dos artefatos que alimentam os apendices
# ---------------------------------------------------------------------------

def _ler_scripts_kpi() -> list[str]:
    """Le sql/03_kpis.sql e descarta molduras e comentarios de cabecalho."""
    arquivo = DIR_RAIZ / "sql" / "03_kpis.sql"
    if not arquivo.exists():
        return []

    enxuto: list[str] = []
    vazia_anterior = False
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        despida = linha.rstrip()
        sem_ruido = despida.replace("-", "").replace(" ", "")
        if despida and set(sem_ruido) <= {"#", "="}:
            continue
        vazia = not despida.strip()
        if vazia and vazia_anterior:
            continue
        enxuto.append(despida)
        vazia_anterior = vazia

    # Descarta o cabecalho do arquivo: o apendice ja tem titulo proprio.
    for indice, linha in enumerate(enxuto):
        if linha.startswith("-- KPI 01"):
            return enxuto[indice:]
    return enxuto


def _ler_dicionario() -> list[tuple[str, str, list[list[str]]]]:
    """Extrai (tabela, descricao, colunas) do dicionario em Markdown."""
    arquivo = DIR_DOCS / "dicionario_dados.md"
    if not arquivo.exists():
        return []

    tabelas: list[tuple[str, str, list[list[str]]]] = []
    nome = descricao = None
    colunas: list[list[str]] = []
    cabecalho_visto = False

    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        if linha.startswith("### "):
            if nome:
                tabelas.append((nome, descricao or "", colunas))
            nome = linha[4:].strip().strip("`")
            descricao, colunas, cabecalho_visto = None, [], False
        elif nome and linha.startswith("|"):
            # O pipe pode aparecer dentro de uma descricao, escapado no
            # Markdown como barra-invertida + pipe. Protege-se essa
            # ocorrencia com um marcador antes de dividir a linha.
            escapado = chr(92) + "|"
            marcador = "@@PIPE@@"
            bruto = linha.strip().strip("|").replace(escapado, marcador)
            celulas = [c.strip().replace(marcador, "|")
                       for c in bruto.split("|")]
            if not cabecalho_visto:
                cabecalho_visto = True
                continue
            if set("".join(celulas)) <= {"-"}:
                continue
            celulas = [c.strip("`") for c in celulas][:5]
            celulas += [""] * (5 - len(celulas))
            colunas.append(celulas)
        elif nome and linha.strip() and not linha.startswith(("|", "**", ">")):
            if descricao is None:
                descricao = linha.strip()

    if nome:
        tabelas.append((nome, descricao or "", colunas))
    return [t for t in tabelas if t[0].startswith(("dw.", "meta."))]


# ---------------------------------------------------------------------------
# Conteudo do artigo
# ---------------------------------------------------------------------------

def montar(incluir_apendices: bool = True) -> Path:
    _contadores["quadro"] = _contadores["figura"] = 0
    doc = configurar_documento()

    # ------------------------------------------------------ pre-textuais
    titulo_trabalho(
        doc,
        "Modelagem multidimensional e ETL incremental na construção "
        "de um Data Warehouse",
        "Um estudo de caso com a base AdventureWorks e o SGBD PostgreSQL",
    )

    autoria(doc, [
        "Yahn de Freitas Santos*",
        "[Nome completo do(a) coautor(a)]**",
        "[Nome completo do(a) professor(a) orientador(a)]***",
    ])

    bloco_resumo(
        doc, "RESUMO",
        "Sistemas transacionais registram operações com integridade, "
        "mas sua estrutura normalizada dificulta a análise gerencial. Este "
        "artigo apresenta o projeto e a implementação de um Data "
        "Warehouse construído a partir da base AdventureWorks, com "
        "modelagem no padrão Star Schema e ETL incremental desenvolvida em "
        "Python. O modelo reúne duas tabelas fato, vendas e compras, "
        "articuladas por cinco dimensões conformadas, e sustenta dez "
        "indicadores implementados em SQL. A carga incremental baseia-se em "
        "marcas d'água sobre a coluna de auditoria, escrita idempotente e "
        "historização por Slowly Changing Dimensions. A carga completa "
        "de 170.525 registros levou 17,95 segundos e os ciclos incrementais "
        "seguintes, 1,03 segundo — redução de 94,3% — sem "
        "perda de consistência entre origem e destino.",
        "Palavras-chave",
        "Data Warehouse. Modelagem multidimensional. Star Schema. ETL "
        "incremental. OLAP.",
    )

    bloco_resumo(
        doc, "ABSTRACT",
        "Transactional systems record operations reliably, but their normalized "
        "structure hinders managerial analysis. This article presents the design "
        "and implementation of a Data Warehouse built from the AdventureWorks "
        "database, using Star Schema modeling and an incremental ETL process "
        "written in Python. The model comprises two fact tables, sales and "
        "purchases, linked by five conformed dimensions, and supports ten "
        "indicators implemented in SQL. The full load of 170,525 records took "
        "17.95 seconds, while subsequent incremental cycles took 1.03 seconds, a "
        "94.3% reduction, with no loss of consistency between source and target.",
        "Keywords",
        "Data Warehouse. Multidimensional modeling. Star Schema. Incremental "
        "ETL. OLAP.",
    )

    # -------------------------------------------------------- 1 INTRODUCAO
    secao(doc, "1", "Introdução")

    par(doc,
        "Sistemas transacionais, designados na literatura como OLTP (Online "
        "Transaction Processing), são otimizados para gravações "
        "frequentes e concorrentes. Para isso, seus modelos são "
        "normalizados, o que reduz a redundância e protege a integridade, "
        "mas fragmenta a informação em dezenas de tabelas "
        "inter-relacionadas.")

    par(doc,
        "Essa mesma normalização torna-se um obstáculo quando o "
        "objetivo deixa de ser registrar a operação e passa a ser "
        "compreendê-la. Uma pergunta gerencial simples — qual foi a "
        "margem bruta por categoria de produto em cada território nos "
        "últimos três anos? — exige junções entre múltiplas "
        "tabelas e agregações sobre milhões de linhas, com custo "
        "computacional elevado e resultado difícil de auditar.")

    par(doc,
        "O Data Warehouse responde a esse impasse: um repositório "
        "analítico separado do ambiente transacional, alimentado por "
        "processos de extração, transformação e carga (ETL) e "
        "estruturado segundo a modelagem multidimensional, que privilegia a "
        "legibilidade do modelo e o desempenho das consultas de "
        "agregação em detrimento da normalização.")

    par(doc,
        "Este artigo relata o projeto e a implementação de um Data "
        "Warehouse construído sobre a base AdventureWorks, banco de "
        "demonstração mantido pela Microsoft que simula as "
        "operações de uma fabricante e distribuidora de bicicletas. O "
        "objetivo geral é propor e implementar um modelo multidimensional "
        "no padrão Star Schema capaz de sustentar um conjunto de "
        "indicadores gerenciais, acompanhado de um processo de ETL "
        "obrigatoriamente incremental.")

    par(doc,
        "São objetivos específicos: analisar o modelo relacional de "
        "origem; elaborar dez indicadores de desempenho; projetar o modelo "
        "estrela correspondente; implementar o Data Warehouse em PostgreSQL; "
        "construir em Python uma ETL que processe apenas registros novos ou "
        "modificados; e comprovar, por consultas SQL, o funcionamento dos "
        "indicadores propostos. A relevância do trabalho reside menos no "
        "resultado final e mais no encadeamento das decisões que a ele "
        "conduzem, pois cada escolha de projeto determina quais perguntas o "
        "repositório poderá responder.")

    # ------------------------------------------------ 2 REFERENCIAL TEORICO
    secao(doc, "2", "Referencial teórico")

    subsecao(doc, "2.1", "Do modelo normalizado ao modelo dimensional")

    par(doc,
        "Chaudhuri e Dayal (1997) caracterizam os sistemas OLTP como voltados a "
        "transações curtas e concorrentes, enquanto os sistemas OLAP "
        "(Online Analytical Processing) atendem a consultas complexas, de "
        "leitura predominante, que percorrem grandes volumes históricos. "
        "Essa diferença de propósito impõe diferenças de "
        "projeto: o ambiente OLTP é normalizado, ao passo que o ambiente "
        "OLAP é deliberadamente desnormalizado. Elmasri e Navathe (2019) "
        "observam que essa desnormalização não viola os "
        "princípios de projeto de banco de dados: em um repositório "
        "cuja carga é controlada por um processo único e periódico, "
        "as anomalias de atualização que a normalização "
        "previne simplesmente não ocorrem.")

    par(doc, "Inmon (2005) define o repositório analítico por quatro "
             "propriedades:")

    citacao(doc,
            "“Um data warehouse é uma coleção de dados "
            "orientada por assunto, integrada, não volátil e "
            "variável em relação ao tempo, de apoio às "
            "decisões gerenciais”",
            "Inmon, 2005, p. 29, tradução nossa")

    par(doc,
        "A variação no tempo é a propriedade de consequência "
        "mais direta sobre este trabalho, pois impõe preservar o estado "
        "histórico dos dados, e não apenas sua fotografia mais "
        "recente.")

    par(doc,
        "A modelagem multidimensional organiza os dados em tabelas fato, que "
        "armazenam as medições numéricas de um processo de "
        "negócio, e tabelas dimensão, que guardam os atributos "
        "descritivos pelos quais essas medições são filtradas e "
        "agrupadas. Quando cada dimensão é representada por uma "
        "única tabela desnormalizada ligada diretamente à fato, o "
        "esquema assume graficamente a forma de uma estrela — o Star "
        "Schema. Vaisman e Zimányi (2022) observam que normalizar as "
        "dimensões, alternativa conhecida como Snowflake Schema, produz "
        "economia de armazenamento marginal ao custo de junções "
        "adicionais e de perda de legibilidade do modelo.")

    par(doc,
        "Dois conceitos operacionais sustentam a construção do modelo. "
        "A granularidade, definida por Kimball e Ross (2013) como a "
        "declaração do que representa uma única linha da tabela "
        "fato, é a decisão mais consequente do projeto: nenhuma "
        "agregação posterior recupera um detalhe que o grão "
        "descartou. A chave substituta (surrogate key), identificador inteiro "
        "gerado pelo próprio repositório, isola o Data Warehouse de "
        "mudanças de codificação na origem e — "
        "condição indispensável — permite que uma mesma "
        "entidade possua múltiplas versões históricas "
        "simultâneas.")

    par(doc,
        "Quando mais de um processo de negócio é modelado, a "
        "integração entre as fatos se dá pelas dimensões "
        "conformadas: tabelas fisicamente compartilhadas, com chaves e "
        "atributos idênticos. Kimball e Ross (2013) sustentam que essa "
        "conformidade é o mecanismo que confere coerência ao "
        "repositório, permitindo analisar lado a lado indicadores "
        "oriundos de processos distintos. Caso particular é a dimensão "
        "de múltiplos papéis, referenciada diversas vezes pela mesma "
        "fato com significados semânticos distintos.")

    subsecao(doc, "2.2", "Historização e carga incremental")

    par(doc,
        "Atributos dimensionais mudam ao longo do tempo, problema que Kimball e "
        "Ross (2013) tratam sob a designação de Slowly Changing "
        "Dimensions. No tipo 1, o novo valor sobrescreve o anterior: a "
        "implementação é trivial, mas a história se perde. No "
        "tipo 2, a alteração insere uma nova linha com nova chave "
        "substituta, enquanto a anterior é encerrada por atributos de "
        "vigência; os fatos carregados antes da mudança permanecem "
        "apontando para a versão antiga, o que preserva a fidelidade "
        "histórica ao custo do crescimento da dimensão.")

    par(doc,
        "Kimball e Caserta (2004) atribuem à camada de ETL a "
        "responsabilidade por obter os dados da origem com o menor impacto "
        "possível, conformá-los e entregá-los ao modelo "
        "dimensional de maneira auditável. A extração pode operar "
        "em dois regimes. Na carga completa, a totalidade dos dados é lida "
        "a cada ciclo, abordagem simples cujo custo cresce linearmente com o "
        "histórico acumulado. Na carga incremental, apenas os registros "
        "criados ou modificados desde o último ciclo são processados, "
        "mantendo o custo proporcional ao movimento do período.")

    par(doc,
        "A carga incremental depende de algum mecanismo de "
        "identificação de mudanças, genericamente designado Change "
        "Data Capture. Vaisman e Zimányi (2022) descrevem as alternativas "
        "usuais: leitura do log de transações, gatilhos, "
        "comparação integral entre origem e destino e uso de colunas "
        "de auditoria de data e hora. As três primeiras oferecem maior "
        "completude ao custo de intervenção na origem; a quarta é "
        "não intrusiva e econômica, exigindo em contrapartida que a "
        "origem mantenha disciplinadamente essa coluna.")

    par(doc,
        "A técnica associada a essa quarta alternativa é a marca "
        "d'água (high-water mark): o processo registra o maior valor da "
        "coluna de auditoria já processado e restringe a "
        "extração seguinte aos registros que o superem. Sua "
        "correção repousa sobre duas condições que o projeto "
        "precisa assegurar: a marca só pode avançar após a "
        "confirmação transacional da carga, e a aplicação dos "
        "dados no destino precisa ser idempotente.")

    # ----------------------------------------------------- 3 METODOLOGIA
    secao(doc, "3", "Metodologia")

    subsecao(doc, "3.1", "Análise da base de origem")

    par(doc,
        "A base AdventureWorks, em sua versão 2022, foi restaurada em uma "
        "instância Microsoft SQL Server Express e submetida a análise "
        "estrutural. Reúne 71 tabelas distribuídas em seis esquemas, "
        "dos quais cinco são funcionais — Sales, Purchasing, "
        "Production, Person e HumanResources — e correspondem aos "
        "macroprocessos da empresa modelada.")

    par(doc,
        "A inspeção do catálogo revelou duas "
        "características determinantes. A primeira é que praticamente "
        "todas as tabelas de negócio mantêm a coluna de auditoria "
        "ModifiedDate, o que viabilizou a estratégia de marca d'água "
        "sem gatilhos nem leitura de log. A segunda é a "
        "separação entre cabeçalho e itens nas tabelas "
        "transacionais: Sales.SalesOrderHeader concentra os atributos do "
        "pedido, enquanto Sales.SalesOrderDetail armazena suas 121.317 linhas "
        "de detalhe. Essa separação define a granularidade candidata "
        "do modelo e impõe cuidado específico à "
        "detecção de mudanças, discutido na seção 3.4.")

    subsecao(doc, "3.2", "Definição dos indicadores")

    par(doc,
        "Os indicadores foram definidos antes da modelagem. A ordem não "
        "é arbitrária: em modelagem dimensional, é o conjunto de "
        "perguntas que o negócio precisa responder que determina o "
        "grão da tabela fato e a composição das dimensões. O "
        "Quadro 1 apresenta os dez indicadores elaborados.")

    quadro(
        doc,
        "Indicadores propostos e respectivas fórmulas de cálculo",
        ["#", "Indicador", "Fórmula", "Dimensões"],
        [
            ["01", "Receita Líquida Total", "SUM(vl_liquido)",
             "Tempo, Território"],
            ["02", "Ticket Médio por Pedido",
             "SUM(vl_liquido) / COUNT(DISTINCT id_pedido)", "Tempo, Canal"],
            ["03", "Margem Bruta Percentual",
             "SUM(vl_margem_bruta) / SUM(vl_liquido) × 100",
             "Tempo, Produto"],
            ["04", "Taxa Média de Desconto",
             "SUM(vl_desconto) / SUM(vl_bruto) × 100", "Tempo, Promoção"],
            ["05", "Crescimento de Receita YoY",
             "(receita − LAG(receita)) / LAG(receita) × 100", "Tempo"],
            ["06", "Curva ABC de Produtos",
             "receita acumulada / receita total", "Produto"],
            ["07", "Mix de Receita por Canal",
             "receita do canal / receita total × 100",
             "Tempo, Canal, Cliente"],
            ["08", "Pontualidade de Entrega",
             "itens no prazo / itens entregues × 100",
             "Tempo, Método de envio, Geografia"],
            ["09", "Desempenho da Força de Vendas",
             "receita do vendedor / cota × 100",
             "Tempo, Funcionário, Território"],
            ["10", "Rejeição por Fornecedor",
             "SUM(qt_rejeitada) / SUM(qt_recebida) × 100",
             "Tempo, Fornecedor, Produto"],
        ],
        FONTE_PROPRIA,
        tamanho=9,
        larguras=[0.9, 4.0, 5.4, 5.2],
    )

    par(doc,
        "A distribuição não é homogênea por acaso. Nove "
        "indicadores recaem sobre o processo de vendas e o décimo sobre o "
        "de compras. Essa inclusão não é ornamental: é "
        "precisamente o indicador de compras que exige a segunda tabela fato e, "
        "por consequência, torna necessária a conformidade das "
        "dimensões tempo, produto, funcionário, método de envio e "
        "situação.")

    subsecao(doc, "3.3", "Decisões de modelagem e suas justificativas")

    par(doc,
        "O grão das duas tabelas fato foi estabelecido no nível mais "
        "atômico disponível: cada linha de fato_vendas representa um "
        "item de pedido e cada linha de fato_compras, um item de ordem de "
        "compra. A escolha decorre da orientação de Kimball e Ross "
        "(2013) segundo a qual o grão mais fino confere máxima "
        "flexibilidade analítica. As demais decisões que não "
        "decorrem automaticamente do padrão estrela estão "
        "justificadas no Quadro 2.")

    quadro(
        doc,
        "Decisões de modelagem e respectivas justificativas",
        ["Decisão", "Justificativa"],
        [
            ["Duas tabelas fato, e não uma só",
             "Vendas e compras possuem granularidades e medidas "
             "incompatíveis. Unificá-las produziria uma tabela esparsa "
             "e exigiria filtro por tipo de transação em toda consulta."],
            ["SCD Tipo 2 apenas em dim_produto",
             "Preço de lista e custo padrão evoluem e sua "
             "evolução tem significado analítico. Já a "
             "correção de um e-mail de cliente não sustenta "
             "análise histórica que justifique o versionamento."],
            ["Dimensão única de funcionários",
             "Vendedores e compradores são registros da mesma tabela de "
             "origem e compartilham atributos. Separá-los duplicaria dados "
             "e impediria análises que cruzem os dois papéis."],
            ["Custo histórico, e não corrente",
             "O custo é buscado em ProductCostHistory na versão vigente "
             "na data do pedido. Usar o custo atual para uma venda de "
             "três anos atrás produziria margem historicamente falsa."],
            ["Rateio de frete e imposto",
             "Medidas do cabeçalho não pertencem ao grão do item. "
             "Replicá-las contaria o mesmo valor tantas vezes quantos "
             "fossem os itens; o rateio proporcional as torna aditivas."],
            ["Membro “Não Informado” (−1)",
             "Chaves estrangeiras nulas inviabilizariam junções "
             "internas. O membro −1 preserva a integridade referencial e "
             "torna a ausência de informação mensurável."],
            ["Chave inteligente em dim_tempo",
             "O calendário é a única dimensão de conteúdo "
             "previsível e imútável. O formato AAAAMMDD dispensa a "
             "junção de resolução na carga dos fatos."],
        ],
        FONTE_PROPRIA,
        tamanho=9,
        larguras=[4.2, 11.3],
    )

    subsecao(doc, "3.4", "Estratégia de ETL incremental")

    par(doc,
        "A ETL foi desenvolvida em Python, com acesso à origem por pyodbc e "
        "ao destino por psycopg. O ciclo de cada entidade percorre cinco etapas. "
        "Primeiro, consulta-se a tabela de controle para recuperar a marca "
        "d'água; na implantação inicial ela vale 1900-01-01, de "
        "modo que a primeira execução equivale a uma carga completa sem "
        "exigir código específico. Segundo, a marca é reduzida por "
        "uma janela de retrocesso de poucos segundos, que protege contra "
        "transações de longa duração cuja data de "
        "modificação antecede o instante em que se tornam "
        "visíveis. Terceiro, os dados extraídos são gravados em "
        "área de staging por meio do comando COPY. Quarto, são "
        "promovidos ao modelo dimensional por instruções executadas "
        "dentro do PostgreSQL. Quinto, somente após a confirmação "
        "de todas as escritas, a marca avança e a transação "
        "é encerrada.")

    par(doc,
        "A ordem da quinta etapa é essencial: avançar a marca antes da "
        "confirmação permitiria que uma falha posterior fizesse os "
        "registros da janela jamais serem reprocessados. Cada entidade é "
        "processada em transação independente, de modo que a falha em "
        "uma não desfaz a carga já confirmada das demais.")

    par(doc,
        "A idempotência é assegurada pela cláusula ON CONFLICT. "
        "Nas tabelas fato, a chave de conflito é a dimensão degenerada "
        "que identifica a transação na origem, e a "
        "atualização é condicionada ao predicado do Quadro 3, que "
        "impede que um reprocessamento sobrescreva um dado mais recente por um "
        "mais antigo.")

    quadro_codigo(doc, "Predicado de idempotência na carga dos fatos", [
        "ON CONFLICT (id_item_venda) DO UPDATE",
        "   SET vl_liquido            = EXCLUDED.vl_liquido,",
        "       -- demais colunas ...",
        "       dt_atualizacao        = CURRENT_TIMESTAMP",
        " WHERE f.dt_modificacao_origem <= EXCLUDED.dt_modificacao_origem;",
    ])

    par(doc,
        "Nas dimensões de tipo 1, a atualização é "
        "adicionalmente condicionada à divergência de um resumo MD5 "
        "calculado sobre os atributos monitorados: registros que retornam do "
        "staging sem alteração de conteúdo não sofrem escrita "
        "alguma. A dimensão produto, historizada como tipo 2, exige "
        "tratamento em três passos sequenciais dentro da mesma "
        "transação — identificar os registros cujo resumo "
        "divergiu, encerrar a versão vigente e inserir a nova — porque "
        "no PostgreSQL as sub-instruções de um mesmo comando enxergam "
        "o mesmo instantâneo e não têm ordem de "
        "execução garantida.")

    par(doc,
        "Merece registro específico a detecção de mudanças nas "
        "tabelas fato. Como cabeçalho e itens são tabelas distintas, "
        "alterações restritas ao cabeçalho — o preenchimento "
        "da data de envio, por exemplo — não tocam nas linhas de "
        "detalhe. Uma extração que observasse apenas a coluna de "
        "auditoria do detalhe perderia silenciosamente essas "
        "atualizações. A consulta adotada, reproduzida no Quadro 4, "
        "avalia o predicado sobre ambas as tabelas.")

    quadro_codigo(doc, "Detecção de mudanças em cabeçalho e itens", [
        "WHERE d.ModifiedDate > ? OR h.ModifiedDate > ?",
        "-- e, na projecao:",
        "CASE WHEN h.ModifiedDate > d.ModifiedDate",
        "     THEN h.ModifiedDate ELSE d.ModifiedDate END AS dt_modificacao_origem",
    ])

    par(doc,
        "Cabe explicitar a limitação inerente à estratégia: a "
        "marca d'água sobre coluna de auditoria não detecta "
        "exclusões físicas, pois um registro removido por DELETE "
        "não altera ModifiedDate. A limitação é "
        "aceitável neste contexto, uma vez que sistemas corporativos "
        "tipicamente praticam exclusão lógica.")

    subsecao(doc, "3.5", "Implementação e materiais")

    par(doc,
        "O Data Warehouse foi implantado em PostgreSQL 16, executado em "
        "contêiner Docker descrito de forma declarativa em arquivo "
        "versionado junto ao projeto, o que permite a qualquer integrante "
        "levantar ambiente idêntico com um único comando. O banco foi "
        "organizado em três esquemas: dw, com o modelo dimensional; stg, "
        "área de staging sem chaves nem índices, que privilegia a "
        "velocidade de ingestão; e meta, com as marcas d'água e o log "
        "de execuções.")

    par(doc,
        "A nomenclatura das colunas segue convenção de prefixos que "
        "explicita a natureza semântica de cada atributo: sk_ para chaves "
        "substitutas, id_ para chaves naturais, vl_ para valores "
        "monetários, qt_ para quantidades, pc_ para percentuais, dt_ para "
        "datas e fl_ para indicadores lógicos. A documentação do "
        "modelo foi registrada no próprio catálogo do PostgreSQL por "
        "instruções COMMENT ON, e o dicionário de dados "
        "apresentado no Apêndice B é extraído desse catálogo "
        "por rotina automatizada, o que assegura que a "
        "documentação jamais divirja da estrutura implantada.")

    par(doc,
        "O código-fonte da ETL, os scripts SQL, o arquivo de "
        "orquestração do contêiner e os roteiros de "
        "reprodução estão disponíveis no repositório "
        "público https://github.com/Yahnfs/dw-adventureworks-produto1.")

    # -------------------------------------------- 4 RESULTADOS E DISCUSSAO
    secao(doc, "4", "Resultados e discussão")

    subsecao(doc, "4.1", "O modelo estrela implementado")

    par(doc,
        "O modelo resultante compreende duas tabelas fato e onze "
        "dimensões, cinco delas conformadas, conforme a Figura 1. As cores "
        "distinguem as dimensões compartilhadas entre os dois processos "
        "daquelas exclusivas de um deles.")

    figura(
        doc, FIGURA_MODELO,
        "Modelo estrela do Data Warehouse AdventureWorks",
        FONTE_PROPRIA,
    )

    par(doc,
        "As medidas são predominantemente aditivas. Valores percentuais "
        "são armazenados em forma decomposta: registra-se o valor "
        "monetário do desconto, que é aditivo, e o percentual é "
        "recalculado na consulta como razão entre somatórios, o que "
        "evita o erro de calcular a média aritmética de percentuais. O "
        "Quadro 5 resume a composição das tabelas implantadas; o "
        "dicionário de dados completo consta do Apêndice B.")

    quadro(
        doc,
        "Composição das tabelas do modelo dimensional",
        ["Tabela", "Tipo", "Grão ou chave natural", "Linhas"],
        [
            ["dw.fato_vendas", "Fato transacional",
             "Item de pedido de venda", "121.319"],
            ["dw.fato_compras", "Fato transacional",
             "Item de ordem de compra", "8.845"],
            ["dw.dim_tempo", "Conformada", "Data do calendário", "6.092"],
            ["dw.dim_produto", "Conformada (SCD 2)",
             "Versão de produto", "506"],
            ["dw.dim_funcionario", "Conformada (SCD 1)",
             "Funcionário", "291"],
            ["dw.dim_metodo_envio", "Conformada (SCD 1)",
             "Modalidade de frete", "6"],
            ["dw.dim_status_pedido", "Conformada (estática)",
             "Situação do pedido", "11"],
            ["dw.dim_cliente", "Dimensão (SCD 1)", "Cliente", "19.821"],
            ["dw.dim_geografia", "Dimensão (SCD 1)", "Endereço", "19.615"],
            ["dw.dim_territorio", "Dimensão (SCD 1)", "Território", "11"],
            ["dw.dim_fornecedor", "Dimensão (SCD 1)", "Fornecedor", "105"],
            ["dw.dim_promocao", "Dimensão (SCD 1)", "Oferta", "17"],
            ["dw.dim_canal_venda", "Dimensão (estática)",
             "Canal de venda", "3"],
        ],
        "Fonte: elaboração própria a partir do banco implantado "
        "(2026). As contagens incluem o membro “Não Informado”.",
        tamanho=9,
        larguras=[4.0, 4.4, 4.6, 2.5],
    )

    par(doc,
        "A verificação da topologia confirmou o padrão estrela: "
        "as vinte chaves estrangeiras do modelo — doze em fato_vendas e "
        "oito em fato_compras — partem sempre de uma fato e chegam a uma "
        "dimensão, e nenhuma dimensão referencia outra. É essa "
        "ausência de ligações entre dimensões que distingue o "
        "Star Schema do Snowflake Schema.")

    subsecao(doc, "4.2", "Desempenho da carga incremental")

    par(doc,
        "A carga inicial processou 170.525 registros em 17,95 segundos. A "
        "conferência entre origem e destino confirmou a identidade das "
        "contagens em todas as tabelas e a equivalência dos "
        "somatórios monetários, com divergência residual de "
        "R$ 0,03 sobre R$ 109.846.381,40 — resultado do arredondamento "
        "decorrente do recálculo da receita no destino, e não de perda "
        "de registros.")

    quadro(
        doc,
        "Comparativo entre os ciclos de carga executados",
        ["Ciclo", "Situação", "Registros", "Duração"],
        [
            ["1º", "Carga inicial (completa)", "170.525", "17,95 s"],
            ["2º", "Sem alterações na origem", "20.023", "1,03 s"],
            ["3º", "Após movimento simulado no OLTP", "20.027", "1,62 s"],
        ],
        "Fonte: elaboração própria a partir de meta.etl_execucao "
        "(2026).",
        tamanho=10,
        larguras=[1.6, 6.4, 3.8, 3.7],
    )

    par(doc,
        "A redução de 17,95 para 1,03 segundo entre o primeiro e o "
        "segundo ciclo — 94,3% menos tempo — evidencia o ganho da "
        "estratégia. Observa-se, contudo, que o segundo ciclo ainda "
        "extraiu 20.023 registros apesar de nada ter mudado na origem. O "
        "fenômeno decorre da distribuição das datas de "
        "modificação na base de demonstração: as 19.820 "
        "linhas de Sales.Customer compartilham a mesma data, de modo que a "
        "janela de retrocesso as recaptura integralmente. Nenhuma escrita "
        "efetiva ocorreu, porque a comparação de resumo MD5 "
        "identificou a ausência de alteração — os dois "
        "mecanismos operam em camadas complementares: o retrocesso privilegia "
        "a completude da extração e a verificação de resumo "
        "protege o destino de escritas inúteis.")

    par(doc,
        "Para comprovar empiricamente o comportamento incremental, um script "
        "provocou na origem três eventos: reajuste de 10% no preço de "
        "um produto, alteração cadastral de um fornecedor e "
        "inserção de um pedido com dois itens. O ciclo subsequente "
        "processou corretamente os três, conforme o Quadro 7.")

    quadro(
        doc,
        "Efeitos do movimento simulado na origem sobre o Data Warehouse",
        ["Evento na origem", "Tratamento", "Efeito observado"],
        [
            ["Reajuste de preço do produto 707", "SCD Tipo 2",
             "Versão 1 encerrada e versão 2 criada, vigente e com o "
             "novo preço"],
            ["Alteração do nível de crédito do fornecedor 1492",
             "SCD Tipo 1",
             "Linha única sobrescrita, com dt_carga preservada e "
             "dt_atualizacao renovada"],
            ["Inserção de pedido com dois itens", "MERGE na fato",
             "Duas linhas acrescentadas a dw.fato_vendas"],
        ],
        FONTE_PROPRIA,
        tamanho=9,
        larguras=[4.6, 2.8, 8.1],
    )

    par(doc,
        "O efeito prático da historização merece destaque. "
        "Após o reajuste, as 3.083 linhas de venda do produto 707 "
        "registradas entre 2011 e 2014 permaneceram vinculadas à "
        "versão de preço R$ 34,99, enquanto a venda posterior "
        "vinculou-se à versão de R$ 42,34. É essa propriedade que "
        "permite reconstruir com fidelidade o contexto vigente em qualquer "
        "período passado, e que se perderia sob tratamento por "
        "sobrescrita.")

    subsecao(doc, "4.3", "Resultados dos indicadores")

    par(doc,
        "As dez consultas foram executadas sobre o modelo carregado, sem "
        "qualquer acesso à base transacional. Os scripts completos constam "
        "do Apêndice A e os principais resultados, do Quadro 8.")

    quadro(
        doc,
        "Resultados consolidados dos indicadores",
        ["Indicador", "Resultado apurado"],
        [
            ["Receita líquida total", "R$ 109.846.549,38"],
            ["Pedidos distintos", "31.466"],
            ["Ticket médio por pedido", "R$ 3.490,96"],
            ["Margem bruta percentual", "11,43%"],
            ["Taxa média de desconto", "0,4779%"],
            ["Mix por canal",
             "Revenda 73,3% e Internet 26,7% da receita"],
            ["Curva ABC",
             "23,7% dos produtos concentram 79,9% da receita"],
            ["Pontualidade de entrega",
             "100,00% em ambas as transportadoras"],
            ["Maior receita por vendedor",
             "R$ 10.367.007,43 (Linda C. Mitchell)"],
            ["Volume adquirido de fornecedores", "R$ 63.791.994,84"],
            ["Maior taxa de rejeição", "5,88%"],
        ],
        "Fonte: elaboração própria a partir do Data Warehouse "
        "implantado (2026).",
        tamanho=10,
        larguras=[7.0, 8.5],
    )

    par(doc,
        "Dois resultados merecem leitura crítica. O indicador de "
        "pontualidade apresentou 100% em todas as transportadoras. O valor "
        "não descreve excelência logística, e sim uma "
        "característica da base de demonstração, na qual as datas "
        "de envio e de vencimento são geradas por regra "
        "determinística — sete e doze dias após o pedido —, de "
        "modo que nenhum atraso pode ocorrer. O indicador permanece no modelo "
        "por sua validade metodológica: a estrutura que o sustenta "
        "produziria resultados significativos sobre dados reais.")

    par(doc,
        "A curva ABC, por sua vez, confirmou o princípio de Pareto de "
        "forma nítida: 63 dos 266 produtos comercializados, ou 23,7% do "
        "catálogo, respondem por praticamente 80% da receita, ao passo que "
        "137 produtos, mais da metade do catálogo, somam apenas 5,1%. "
        "Registre-se ainda a variação da margem bruta ao longo dos "
        "anos — 15,1% em 2011, 9,0% em 2012, 9,6% em 2013 e 17,2% em 2014 "
        "—, resultado apurável apenas porque o custo utilizado é o "
        "vigente na data de cada pedido. Sob a alternativa de empregar o custo "
        "corrente, a série apresentaria comportamento uniforme e "
        "artificial, o que ilustra a consequência analítica de uma "
        "decisão de modelagem.")

    # ---------------------------------------------- 5 CONSIDERACOES FINAIS
    secao(doc, "5", "Considerações finais")

    par(doc,
        "Este artigo apresentou o projeto e a implementação de um Data "
        "Warehouse construído a partir da base AdventureWorks, abrangendo a "
        "análise do modelo de origem, a definição de dez "
        "indicadores, o desenho de um modelo estrela com duas tabelas fato e "
        "onze dimensões, sua implantação em PostgreSQL e o "
        "desenvolvimento de uma ETL incremental em Python.")

    par(doc,
        "Os objetivos foram integralmente atendidos. O modelo sustenta os dez "
        "indicadores por meio de consultas que operam exclusivamente sobre a "
        "camada analítica; a ETL demonstrou comportamento incremental "
        "verificável, com redução de 94,3% no tempo de "
        "processamento; e a conferência entre origem e destino confirmou a "
        "consistência dos dados carregados.")

    par(doc,
        "Do percurso extraem-se três aprendizados. O primeiro é que a "
        "definição dos indicadores precede necessariamente a "
        "modelagem: foi a inclusão de um indicador de qualidade de "
        "fornecimento que impôs a segunda tabela fato e, com ela, as "
        "dimensões conformadas. O segundo é que a carga incremental "
        "correta não se resume a filtrar a extração por data; ela "
        "exige o encadeamento de três propriedades — "
        "extração conservadora, aplicação idempotente e "
        "avanço da marca apenas após confirmação —, cuja "
        "ausência isolada compromete todo o mecanismo. O terceiro é "
        "que decisões aparentemente técnicas possuem consequências "
        "analíticas diretas, como evidenciou o uso do custo histórico "
        "no cálculo da margem.")

    par(doc,
        "O trabalho apresenta limitações. A estratégia de "
        "detecção de mudanças não captura exclusões "
        "físicas na origem; a base utilizada é sintética, o que se "
        "manifestou no indicador de pontualidade; e não foram implementadas "
        "tabelas agregadas nem particionamento, recursos cuja necessidade "
        "só se manifesta em volumes superiores aos aqui processados.")

    par(doc,
        "Como continuidade, identificam-se quatro direções: substituir "
        "a marca d'água por Change Data Capture baseado em log de "
        "transações, o que permitiria capturar exclusões; "
        "introduzir uma fato de estoque com granularidade de instantâneo "
        "periódico, exercitando medidas semiaditivas; construir tabelas "
        "agregadas com atualização incremental; e orquestrar o "
        "pipeline por ferramenta especializada, como o Apache Airflow, "
        "adicionando escalonamento e monitoramento.")

    # ------------------------------------------------------- REFERENCIAS
    secao(doc, "", "Referências")

    referencia(doc, [
        ("CHAUDHURI, S.; DAYAL, U. An overview of data warehousing and OLAP "
         "technology. ", False),
        ("ACM SIGMOD Record", True),
        (", New York, v. 26, n. 1, p. 65-74, mar. 1997.", False),
    ])
    referencia(doc, [
        ("ELMASRI, R.; NAVATHE, S. B. ", False),
        ("Sistemas de banco de dados", True),
        (". 7. ed. São Paulo: Pearson, 2019.", False),
    ])
    referencia(doc, [
        ("INMON, W. H. ", False),
        ("Building the data warehouse", True),
        (". 4. ed. Indianapolis: Wiley Publishing, 2005.", False),
    ])
    referencia(doc, [
        ("KIMBALL, R.; CASERTA, J. ", False),
        ("The data warehouse ETL toolkit", True),
        (": practical techniques for extracting, cleaning, conforming, and "
         "delivering data. Indianapolis: Wiley Publishing, 2004.", False),
    ])
    referencia(doc, [
        ("KIMBALL, R.; ROSS, M. ", False),
        ("The data warehouse toolkit", True),
        (": the definitive guide to dimensional modeling. 3. ed. Indianapolis: "
         "John Wiley & Sons, 2013.", False),
    ])
    referencia(doc, [
        ("MACHADO, F. N. R. ", False),
        ("Tecnologia e projeto de data warehouse", True),
        (": uma visão multidimensional. 6. ed. São Paulo: "
         "Érica, 2013.", False),
    ])
    referencia(doc, [
        ("MICROSOFT. ", False),
        ("AdventureWorks sample databases", True),
        (". [S. l.]: Microsoft Learn, 2024. Disponível em: "
         "https://learn.microsoft.com/pt-br/sql/samples/"
         "adventureworks-install-configure. Acesso em: 28 ago. 2026.", False),
    ])
    referencia(doc, [
        ("POSTGRESQL GLOBAL DEVELOPMENT GROUP. ", False),
        ("PostgreSQL 16 documentation", True),
        (". [S. l.]: The PostgreSQL Global Development Group, 2023. "
         "Disponível em: https://www.postgresql.org/docs/16/. "
         "Acesso em: 28 ago. 2026.", False),
    ])
    referencia(doc, [
        ("VAISMAN, A.; ZIMÁNYI, E. ", False),
        ("Data warehouse systems", True),
        (": design and implementation. 2. ed. Berlin: Springer, 2022.", False),
    ])

    # --------------------------------------------------------- APENDICES
    if incluir_apendices:
        apendice(doc, "A", "Scripts SQL dos indicadores")
        par(doc,
            "Reproduzem-se a seguir as consultas que implementam os dez "
            "indicadores do Quadro 1. Todas operam exclusivamente sobre o "
            "modelo dimensional, sem acesso ao sistema transacional.")
        linhas_sql = _ler_scripts_kpi()
        if linhas_sql:
            quadro_codigo(doc, "Consultas SQL dos dez indicadores",
                          linhas_sql, FONTE_PROPRIA, tamanho=7,
                          compacto=True)

        apendice(doc, "B", "Dicionário de dados do Data Warehouse")
        par(doc,
            "O dicionário abaixo é extraído do catálogo do "
            "próprio PostgreSQL, o que assegura sua correspondência "
            "exata com a estrutura implantada. A coluna Chave identifica "
            "chaves primárias (PK) e estrangeiras (FK). "
            "Fonte: elaboração própria a partir do catálogo "
            "do PostgreSQL (2026).")

        for nome_tabela, descricao_tabela, colunas in _ler_dicionario():
            subtitulo = doc.add_paragraph()
            subtitulo.paragraph_format.space_before = Pt(6)
            subtitulo.paragraph_format.space_after = Pt(0)
            subtitulo.paragraph_format.keep_with_next = True
            _fonte(subtitulo.add_run(nome_tabela), 10, negrito=True)
            if descricao_tabela:
                _fonte(subtitulo.add_run(f" – {descricao_tabela}"), 10)

            quadro(doc, "", ["Coluna", "Tipo", "Nulo", "Chave", "Descrição"],
                   colunas, "", tamanho=6.5,
                   larguras=[3.3, 2.5, 0.9, 3.0, 5.8], compacto=True)

    doc.save(SAIDA)
    return SAIDA


if __name__ == "__main__":
    incluir = "--sem-apendices" not in sys.argv
    caminho = montar(incluir_apendices=incluir)
    print(f"Artigo gerado em: {caminho}")
    print(f"Apêndices: {'incluídos' if incluir else 'omitidos'}")
