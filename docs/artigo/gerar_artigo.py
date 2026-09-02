"""Gera o artigo academico no padrao Unisales/ABNT em formato .docx.

    python docs/artigo/gerar_artigo.py

Formatacao aplicada, conforme o Guia de Elaboracao e Normalizacao de Trabalhos
Academicos e de Pesquisa da Unisales e a NBR 6022/NBR 14724:

* Papel A4, margens superior e esquerda 3 cm, inferior e direita 2 cm
* Fonte Arial 12 no corpo, entrelinha 1,5, paragrafos justificados com recuo
  de primeira linha de 1,25 cm
* Resumo em paragrafo unico, sem recuo, entrelinha simples
* Citacoes diretas com mais de tres linhas em recuo de 4 cm, fonte 10 e
  entrelinha simples
* Titulos de secao numerados progressivamente
* Ilustracoes e quadros com titulo acima e fonte abaixo, ambos em fonte 10
* Referencias em ordem alfabetica, entrelinha simples, separadas entre si
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

DIR_ARTIGO = Path(__file__).resolve().parent
DIR_DOCS = DIR_ARTIGO.parent
SAIDA = DIR_ARTIGO / "Artigo_DW_AdventureWorks_Unisales.docx"
FIGURA_MODELO = DIR_DOCS / "modelo_estrela.png"

FONTE = "Arial"


# ---------------------------------------------------------------------------
# Utilitarios de formatacao
# ---------------------------------------------------------------------------

def configurar_documento() -> Document:
    documento = Document()

    secao = documento.sections[0]
    secao.page_width = Cm(21.0)
    secao.page_height = Cm(29.7)
    secao.top_margin = Cm(3.0)
    secao.left_margin = Cm(3.0)
    secao.bottom_margin = Cm(2.0)
    secao.right_margin = Cm(2.0)

    estilo = documento.styles["Normal"]
    estilo.font.name = FONTE
    estilo.font.size = Pt(12)
    estilo.element.rPr.rFonts.set(qn("w:eastAsia"), FONTE)
    formato = estilo.paragraph_format
    formato.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    formato.space_after = Pt(0)
    formato.space_before = Pt(0)

    return documento


def _fonte(execucao, tamanho=12, negrito=False, italico=False, cor=None,
           nome=FONTE):
    execucao.font.name = nome
    execucao.font.size = Pt(tamanho)
    execucao.bold = negrito
    execucao.italic = italico
    if cor is not None:
        execucao.font.color.rgb = cor
    execucao._element.rPr.rFonts.set(qn("w:eastAsia"), nome)
    return execucao


def titulo_trabalho(doc: Document, texto: str, subtitulo: str | None = None):
    paragrafo = doc.add_paragraph()
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragrafo.paragraph_format.space_after = Pt(6)
    _fonte(paragrafo.add_run(texto.upper()), 14, negrito=True)
    if subtitulo:
        sub = doc.add_paragraph()
        sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
        sub.paragraph_format.space_after = Pt(18)
        _fonte(sub.add_run(subtitulo), 12, negrito=False)


def autoria(doc: Document, linhas: list[str]):
    for texto in linhas:
        paragrafo = doc.add_paragraph()
        paragrafo.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        paragrafo.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        _fonte(paragrafo.add_run(texto), 11)
    doc.add_paragraph().paragraph_format.space_after = Pt(12)


def bloco_resumo(doc: Document, rotulo: str, texto: str, chaves_rotulo: str,
                 chaves: str):
    cabecalho = doc.add_paragraph()
    cabecalho.paragraph_format.space_before = Pt(12)
    cabecalho.paragraph_format.space_after = Pt(6)
    _fonte(cabecalho.add_run(rotulo), 12, negrito=True)

    corpo = doc.add_paragraph()
    corpo.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    corpo.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    corpo.paragraph_format.first_line_indent = Cm(0)
    corpo.paragraph_format.space_after = Pt(6)
    _fonte(corpo.add_run(texto), 12)

    palavras = doc.add_paragraph()
    palavras.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    palavras.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    palavras.paragraph_format.space_after = Pt(12)
    _fonte(palavras.add_run(f"{chaves_rotulo} "), 12, negrito=True)
    _fonte(palavras.add_run(chaves), 12)


def secao(doc: Document, numero: str, texto: str):
    paragrafo = doc.add_paragraph()
    paragrafo.paragraph_format.space_before = Pt(18)
    paragrafo.paragraph_format.space_after = Pt(12)
    paragrafo.paragraph_format.keep_with_next = True
    # Secoes sem indicativo numerico (Referencias) nao levam espaco inicial.
    rotulo = f"{numero} {texto.upper()}".strip() if numero else texto.upper()
    _fonte(paragrafo.add_run(rotulo), 12, negrito=True)


def subsecao(doc: Document, numero: str, texto: str):
    paragrafo = doc.add_paragraph()
    paragrafo.paragraph_format.space_before = Pt(12)
    paragrafo.paragraph_format.space_after = Pt(6)
    paragrafo.paragraph_format.keep_with_next = True
    _fonte(paragrafo.add_run(f"{numero} {texto}"), 12, negrito=True)


def par(doc: Document, texto: str, recuo: bool = True):
    paragrafo = doc.add_paragraph()
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragrafo.paragraph_format.first_line_indent = Cm(1.25 if recuo else 0)
    paragrafo.paragraph_format.space_after = Pt(0)
    _fonte(paragrafo.add_run(texto), 12)
    return paragrafo


def citacao(doc: Document, texto: str, fonte: str):
    paragrafo = doc.add_paragraph()
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragrafo.paragraph_format.left_indent = Cm(4.0)
    paragrafo.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    paragrafo.paragraph_format.space_before = Pt(12)
    paragrafo.paragraph_format.space_after = Pt(12)
    _fonte(paragrafo.add_run(f"{texto} ({fonte})."), 10)


def codigo(doc: Document, linhas: list[str]):
    for indice, linha in enumerate(linhas):
        paragrafo = doc.add_paragraph()
        paragrafo.paragraph_format.left_indent = Cm(1.0)
        paragrafo.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        paragrafo.paragraph_format.space_before = Pt(6 if indice == 0 else 0)
        paragrafo.paragraph_format.space_after = Pt(0)
        _fonte(paragrafo.add_run(linha if linha else " "), 9,
               nome="Courier New")


def legenda_superior(doc: Document, texto: str):
    paragrafo = doc.add_paragraph()
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragrafo.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    paragrafo.paragraph_format.space_before = Pt(12)
    paragrafo.paragraph_format.space_after = Pt(3)
    paragrafo.paragraph_format.keep_with_next = True
    _fonte(paragrafo.add_run(texto), 10, negrito=True)


def legenda_fonte(doc: Document, texto: str):
    paragrafo = doc.add_paragraph()
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragrafo.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    paragrafo.paragraph_format.space_before = Pt(3)
    paragrafo.paragraph_format.space_after = Pt(12)
    _fonte(paragrafo.add_run(texto), 10)


def figura(doc: Document, caminho: Path, titulo: str, fonte: str,
           largura_cm: float = 15.5):
    legenda_superior(doc, titulo)
    paragrafo = doc.add_paragraph()
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragrafo.paragraph_format.space_after = Pt(0)
    paragrafo.add_run().add_picture(str(caminho), width=Cm(largura_cm))
    legenda_fonte(doc, fonte)


def _sombrear(celula, cor_hex: str):
    elemento = OxmlElement("w:shd")
    elemento.set(qn("w:val"), "clear")
    elemento.set(qn("w:fill"), cor_hex)
    celula._tc.get_or_add_tcPr().append(elemento)


def quadro(doc: Document, titulo: str, cabecalho: list[str],
           linhas: list[list[str]], fonte: str, tamanho: float = 9,
           larguras: list[float] | None = None):
    if titulo:
        legenda_superior(doc, titulo)

    tabela = doc.add_table(rows=1, cols=len(cabecalho))
    tabela.style = "Table Grid"
    tabela.alignment = WD_TABLE_ALIGNMENT.CENTER
    tabela.autofit = True

    for indice, texto in enumerate(cabecalho):
        celula = tabela.rows[0].cells[indice]
        celula.text = ""
        paragrafo = celula.paragraphs[0]
        paragrafo.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        paragrafo.paragraph_format.space_after = Pt(0)
        _fonte(paragrafo.add_run(texto), tamanho, negrito=True)
        _sombrear(celula, "D9D9D9")

    for valores in linhas:
        celulas = tabela.add_row().cells
        for indice, texto in enumerate(valores):
            celula = celulas[indice]
            celula.text = ""
            paragrafo = celula.paragraphs[0]
            paragrafo.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
            paragrafo.paragraph_format.space_after = Pt(0)
            _fonte(paragrafo.add_run(texto), tamanho)

    if larguras:
        for linha in tabela.rows:
            for indice, largura in enumerate(larguras):
                linha.cells[indice].width = Cm(largura)

    if fonte:
        legenda_fonte(doc, fonte)


def referencia(doc: Document, texto_negrito_partes: list[tuple[str, bool]]):
    paragrafo = doc.add_paragraph()
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragrafo.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    paragrafo.paragraph_format.space_after = Pt(12)
    for texto, negrito in texto_negrito_partes:
        _fonte(paragrafo.add_run(texto), 12, negrito=negrito)


def apendice(doc: Document, letra: str, texto: str):
    """Titulo de apendice, sem indicativo numerico, iniciando em nova pagina."""
    doc.add_page_break()
    paragrafo = doc.add_paragraph()
    paragrafo.paragraph_format.space_after = Pt(12)
    paragrafo.paragraph_format.keep_with_next = True
    _fonte(paragrafo.add_run(f"APENDICE {letra} - {texto}".upper()
                             .replace("APENDICE", "APÊNDICE")), 12, negrito=True)


def _ler_scripts_kpi() -> list[str]:
    """Le sql/03_kpis.sql e remove as linhas decorativas dos cabecalhos."""
    arquivo = DIR_DOCS.parent / "sql" / "03_kpis.sql"
    if not arquivo.exists():
        return []
    linhas: list[str] = []
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        despida = linha.rstrip()
        # Descarta as reguas de "#" e "=" usadas como moldura no arquivo fonte.
        if set(despida.replace("-", "").replace(" ", "")) <= {"#", "="} and despida:
            continue
        linhas.append(despida)
    # Remove o cabecalho do arquivo (ate a primeira consulta) e linhas vazias
    # consecutivas, que desperdicariam espaco no documento impresso.
    enxuto: list[str] = []
    vazia_anterior = False
    for linha in linhas:
        vazia = not linha.strip()
        if vazia and vazia_anterior:
            continue
        enxuto.append(linha)
        vazia_anterior = vazia
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
                cabecalho_visto = True          # linha de titulo da tabela
                continue
            if set("".join(celulas)) <= {"-"}:  # linha separadora
                continue
            celulas = [c.strip("`") for c in celulas][:5]
            celulas += [""] * (5 - len(celulas))
            colunas.append(celulas)
        elif nome and linha.strip() and not linha.startswith(("|", "**", ">")):
            if descricao is None:
                descricao = linha.strip()

    if nome:
        tabelas.append((nome, descricao or "", colunas))
    # Apenas as tabelas do modelo dimensional e do controle da ETL.
    return [t for t in tabelas if t[0].startswith(("dw.", "meta."))]


# ---------------------------------------------------------------------------
# Conteudo do artigo
# ---------------------------------------------------------------------------

def montar() -> Path:
    doc = configurar_documento()

    # ---------------------------------------------------------------- capa
    titulo_trabalho(
        doc,
        "Modelagem multidimensional e ETL incremental aplicadas à "
        "construção de um Data Warehouse",
        "Um estudo de caso com a base AdventureWorks e o SGBD PostgreSQL",
    )

    autoria(doc, [
        "[Nome completo do(a) autor(a)]*",
        "[Nome completo do(a) coautor(a)]**",
        "[Nome completo do(a) professor(a) orientador(a)]***",
    ])

    bloco_resumo(
        doc,
        "RESUMO",
        "Sistemas transacionais são projetados para registrar operações com "
        "integridade e concorrência, e não para responder às perguntas "
        "analíticas que sustentam a tomada de decisão. Este artigo apresenta o "
        "projeto e a implementação de um Data Warehouse construído a partir da "
        "base transacional AdventureWorks, adotando modelagem multidimensional "
        "no padrão Star Schema e um processo de ETL incremental desenvolvido em "
        "Python. O modelo proposto reúne duas tabelas fato — vendas e compras — "
        "articuladas por cinco dimensões conformadas, e sustenta dez "
        "indicadores de desempenho implementados em SQL. A estratégia de carga "
        "incremental baseia-se em marcas d'água sobre a coluna de auditoria "
        "ModifiedDate, combinada a operações idempotentes de escrita e ao "
        "controle de historização por Slowly Changing Dimensions dos tipos 1 e "
        "2. O Data Warehouse foi implantado em PostgreSQL 16 executado em "
        "contêiner Docker. Os resultados demonstram que a carga completa de "
        "170.525 registros foi concluída em 17,95 segundos, ao passo que os "
        "ciclos incrementais subsequentes reduziram o tempo de execução para "
        "1,03 segundo, uma redução de 94,3%, preservando integralmente a "
        "consistência entre origem e destino. Conclui-se que a combinação entre "
        "modelagem dimensional e carga incremental idempotente viabiliza um "
        "ambiente analítico consistente, historicamente fiel e economicamente "
        "sustentável em janelas de processamento reduzidas.",
        "Palavras-chave:",
        "Data Warehouse. Modelagem multidimensional. Star Schema. ETL "
        "incremental. OLAP.",
    )

    bloco_resumo(
        doc,
        "ABSTRACT",
        "Transactional systems are designed to record operations with "
        "integrity and concurrency, rather than to answer the analytical "
        "questions that support decision making. This article presents the "
        "design and implementation of a Data Warehouse built from the "
        "AdventureWorks transactional database, adopting multidimensional "
        "modeling in the Star Schema pattern and an incremental ETL process "
        "developed in Python. The proposed model comprises two fact tables — "
        "sales and purchases — articulated by five conformed dimensions, and "
        "supports ten key performance indicators implemented in SQL. The "
        "incremental load strategy relies on high-water marks over the "
        "ModifiedDate audit column, combined with idempotent write operations "
        "and historization control through Slowly Changing Dimensions of types "
        "1 and 2. The Data Warehouse was deployed on PostgreSQL 16 running in a "
        "Docker container. Results show that the full load of 170,525 records "
        "completed in 17.95 seconds, whereas subsequent incremental cycles "
        "reduced execution time to 1.03 seconds, a 94.3% reduction, while fully "
        "preserving consistency between source and target.",
        "Keywords:",
        "Data Warehouse. Multidimensional modeling. Star Schema. Incremental "
        "ETL. OLAP.",
    )

    # ------------------------------------------------------------ 1 INTRO
    secao(doc, "1", "Introdução")

    par(doc,
        "As organizações contemporâneas registram, a cada operação de negócio, "
        "um volume crescente de dados em sistemas transacionais. Esses "
        "sistemas, designados na literatura como OLTP (Online Transaction "
        "Processing), são otimizados para gravações frequentes, de curta "
        "duração e alta concorrência. Para atingir esse objetivo, seus modelos "
        "de dados são normalizados, o que reduz a redundância e protege a "
        "integridade, mas fragmenta a informação em dezenas ou centenas de "
        "tabelas inter-relacionadas.")

    par(doc,
        "Essa mesma normalização, virtuosa no contexto operacional, torna-se um "
        "obstáculo quando o objetivo deixa de ser registrar a operação e passa "
        "a ser compreendê-la. Uma pergunta gerencial aparentemente simples — "
        "qual foi a margem bruta por categoria de produto em cada território "
        "nos últimos três anos? — exige, em um modelo normalizado, junções "
        "entre múltiplas tabelas, agregações sobre milhões de linhas e o "
        "conhecimento tácito de regras de negócio dispersas pelo esquema. O "
        "custo computacional é elevado, o tempo de resposta é incompatível com "
        "a exploração interativa e, sobretudo, o resultado é difícil de "
        "auditar.")

    par(doc,
        "O Data Warehouse surge como resposta arquitetural a esse impasse. "
        "Trata-se de um repositório analítico separado do ambiente "
        "transacional, alimentado periodicamente por processos de extração, "
        "transformação e carga (ETL), e estruturado segundo uma lógica de "
        "modelagem própria — a modelagem multidimensional —, que privilegia a "
        "legibilidade do modelo e o desempenho das consultas de agregação em "
        "detrimento da normalização.")

    par(doc,
        "O presente artigo relata o projeto e a implementação de um Data "
        "Warehouse construído sobre a base AdventureWorks, banco de dados de "
        "demonstração mantido pela Microsoft que simula as operações de uma "
        "empresa fabricante e distribuidora de bicicletas e acessórios. O "
        "trabalho tem por objetivo geral propor e implementar um modelo "
        "multidimensional no padrão Star Schema capaz de sustentar um conjunto "
        "de indicadores gerenciais, acompanhado de um processo de ETL "
        "obrigatoriamente incremental.")

    par(doc,
        "Como objetivos específicos, o trabalho compreende: (i) analisar o "
        "modelo relacional OLTP da base de origem, identificando os processos "
        "de negócio e a granularidade de suas transações; (ii) elaborar dez "
        "indicadores de desempenho relevantes ao negócio modelado; (iii) "
        "projetar um modelo estrela que sustente esses indicadores; (iv) "
        "implementar o Data Warehouse em PostgreSQL; (v) construir em Python "
        "uma ETL que processe apenas registros novos ou modificados; e (vi) "
        "comprovar, por meio de consultas SQL, o funcionamento dos indicadores "
        "propostos.")

    par(doc,
        "A relevância do trabalho reside menos no resultado final e mais no "
        "encadeamento das decisões que a ele conduzem. Definir a granularidade "
        "de uma tabela fato, escolher entre sobrescrever ou historiar o atributo "
        "de uma dimensão, decidir como identificar aquilo que mudou na origem — "
        "cada uma dessas escolhas determina quais perguntas o Data Warehouse "
        "poderá responder e quais permanecerão fora de seu alcance. É esse "
        "processo decisório que o artigo procura explicitar.")

    # ---------------------------------------------------- 2 FUNDAMENTAÇÃO
    secao(doc, "2", "Fundamentação teórica")

    subsecao(doc, "2.1", "Sistemas OLTP e OLAP")

    par(doc,
        "A distinção entre processamento transacional e processamento "
        "analítico é o ponto de partida conceitual para o projeto de qualquer "
        "ambiente de Business Intelligence. Chaudhuri e Dayal (1997) "
        "sistematizaram essa oposição ao caracterizarem os sistemas OLTP como "
        "voltados a transações curtas, altamente concorrentes e de escopo "
        "reduzido, ao passo que os sistemas OLAP (Online Analytical "
        "Processing) atendem a consultas complexas, de leitura predominante, "
        "que percorrem grandes volumes históricos e produzem agregações.")

    par(doc,
        "Essa diferença de propósito impõe diferenças de projeto. O ambiente "
        "OLTP é normalizado até a terceira forma normal ou além, o que "
        "minimiza a redundância e o custo de atualização; o ambiente OLAP é "
        "deliberadamente desnormalizado, o que multiplica a redundância mas "
        "reduz drasticamente o número de junções necessárias a uma consulta "
        "analítica. Elmasri e Navathe (2019) observam que essa desnormalização "
        "não constitui violação dos princípios de projeto de banco de dados, e "
        "sim aplicação coerente desses princípios a um requisito distinto: em "
        "um repositório cuja carga é controlada por um processo único e "
        "periódico, as anomalias de atualização que a normalização previne "
        "simplesmente não ocorrem.")

    subsecao(doc, "2.2", "Data Warehouse")

    par(doc,
        "A definição canônica de Data Warehouse foi formulada por Inmon (2005), "
        "para quem o repositório analítico se caracteriza por quatro "
        "propriedades:")

    citacao(doc,
            "“Um data warehouse é uma coleção de dados orientada por "
            "assunto, integrada, não volátil e variável em relação ao tempo, "
            "de apoio às decisões gerenciais”",
            "INMON, 2005, p. 29, tradução nossa")

    par(doc,
        "Cada uma das quatro propriedades tem consequência prática direta sobre "
        "o projeto. A orientação por assunto determina que a organização dos "
        "dados siga os processos de negócio — vendas, compras, produção — e não "
        "a estrutura dos sistemas de origem. A integração exige que "
        "codificações divergentes entre sistemas sejam conciliadas em um "
        "padrão único durante a carga. A não volatilidade estabelece que os "
        "dados, uma vez carregados, não são apagados nem alterados pelo "
        "usuário, o que confere reprodutibilidade às análises. A variação no "
        "tempo, por fim, impõe que o repositório preserve o estado histórico "
        "dos dados, e não apenas sua fotografia mais recente — requisito que "
        "se materializa nas técnicas de historização discutidas na seção 2.5.")

    par(doc,
        "Kimball e Ross (2013) propõem abordagem complementar, partindo dos "
        "processos de negócio em direção ao repositório integrado, em vez do "
        "movimento inverso. Nessa perspectiva, o Data Warehouse constitui-se "
        "pela união de modelos dimensionais que compartilham dimensões "
        "conformadas, e não por um repositório normalizado central do qual "
        "derivariam data marts departamentais. É essa segunda abordagem que "
        "orienta o presente trabalho.")

    subsecao(doc, "2.3", "Modelagem multidimensional e o Star Schema")

    par(doc,
        "A modelagem multidimensional organiza os dados analíticos em torno de "
        "duas categorias de tabelas. As tabelas fato armazenam as medições "
        "numéricas de um processo de negócio — quantidades, valores, prazos — e "
        "as chaves estrangeiras que as qualificam. As tabelas dimensão "
        "armazenam os atributos descritivos pelos quais essas medições são "
        "filtradas, agrupadas e rotuladas. Kimball e Ross (2013) sintetizam a "
        "relação entre ambas afirmando que as tabelas fato guardam o que se "
        "mede e as dimensões guardam o contexto da medição.")

    par(doc,
        "Quando cada dimensão é representada por uma única tabela "
        "desnormalizada, ligada diretamente à tabela fato, o esquema resultante "
        "assume graficamente a forma de uma estrela — daí a denominação Star "
        "Schema. A alternativa, denominada Snowflake Schema, normaliza as "
        "hierarquias das dimensões em tabelas auxiliares. Vaisman e Zimányi "
        "(2022) observam que a normalização das dimensões produz economia de "
        "armazenamento marginal, porque as dimensões representam fração "
        "reduzida do volume total do repositório, ao custo de junções "
        "adicionais em toda consulta e de perda de legibilidade do modelo pelo "
        "usuário de negócio. Por essa razão, o padrão estrela é adotado neste "
        "trabalho.")

    par(doc,
        "Dois conceitos operacionais sustentam a construção do modelo estrela. "
        "O primeiro é a granularidade, definida por Kimball e Ross (2013) como "
        "a declaração do que representa uma única linha da tabela fato. A "
        "declaração de grão é a decisão de projeto mais consequente do modelo, "
        "pois estabelece o nível máximo de detalhe passível de análise: "
        "nenhuma agregação posterior recupera um detalhe que o grão descartou. "
        "O segundo é a chave substituta (surrogate key), identificador inteiro "
        "gerado pelo próprio Data Warehouse, independente das chaves naturais "
        "do sistema de origem. A chave substituta isola o repositório de "
        "mudanças de codificação na origem, viabiliza a integração de sistemas "
        "distintos e — condição indispensável — permite que uma mesma entidade "
        "de negócio possua múltiplas versões históricas simultâneas.")

    subsecao(doc, "2.4", "Dimensões conformadas")

    par(doc,
        "Quando uma organização modela mais de um processo de negócio, cada "
        "processo origina sua própria tabela fato, com granularidade própria. "
        "A integração entre eles se dá pelas dimensões conformadas: tabelas "
        "dimensão fisicamente compartilhadas por múltiplas tabelas fato, com "
        "chaves e atributos idênticos. Kimball e Ross (2013) sustentam que a "
        "conformidade das dimensões é o mecanismo que confere coerência ao "
        "Data Warehouse como um todo, permitindo que indicadores oriundos de "
        "processos diferentes sejam analisados lado a lado sobre o mesmo eixo "
        "— por exemplo, confrontar receita de vendas e custo de aquisição de um "
        "mesmo produto, em um mesmo período.")

    par(doc,
        "Caso particular de conformidade é a dimensão de múltiplos papéis "
        "(role-playing dimension), em que uma única tabela é referenciada "
        "diversas vezes pela mesma tabela fato, cada referência assumindo "
        "significado semântico distinto. A dimensão tempo é o exemplo "
        "recorrente: uma mesma linha de fato pode apontar para a data do "
        "pedido, a data prometida e a data de envio, todas oriundas da mesma "
        "tabela de calendário.")

    subsecao(doc, "2.5", "Dimensões de mudança lenta (Slowly Changing Dimensions)")

    par(doc,
        "Atributos dimensionais mudam ao longo do tempo: um produto é "
        "reclassificado de categoria, um cliente muda de endereço, um preço de "
        "tabela é reajustado. O tratamento dessas alterações constitui o "
        "problema das Slowly Changing Dimensions, para o qual Kimball e Ross "
        "(2013) catalogam respostas tipificadas. Três são relevantes a este "
        "trabalho.")

    par(doc,
        "No SCD Tipo 1, o novo valor sobrescreve o anterior. A implementação é "
        "trivial e o volume da dimensão permanece estável, mas a história se "
        "perde: após a atualização, o repositório passa a apresentar como se o "
        "valor corrente sempre tivesse vigorado. O tipo é adequado a correções "
        "de erro de digitação e a atributos cuja evolução não possui "
        "significado analítico.")

    par(doc,
        "No SCD Tipo 2, a alteração provoca a inserção de uma nova linha na "
        "dimensão, com nova chave substituta, enquanto a linha anterior é "
        "encerrada por meio de atributos de vigência. Os fatos carregados antes "
        "da mudança permanecem apontando para a versão antiga, e os "
        "posteriores apontam para a nova. Preserva-se, assim, a fidelidade "
        "histórica: o relatório de um período passado reproduz exatamente o "
        "contexto vigente naquele período. O custo é o crescimento da dimensão "
        "e a necessidade de resolver, na carga do fato, qual versão estava "
        "vigente na data da transação.")

    par(doc,
        "O SCD Tipo 3, que mantém em colunas paralelas o valor corrente e o "
        "imediatamente anterior, atende apenas a cenários de comparação "
        "limitada e não foi empregado neste projeto.")

    subsecao(doc, "2.6", "Processos de ETL")

    par(doc,
        "O processo de ETL constitui a camada que alimenta o Data Warehouse. "
        "Kimball e Caserta (2004) estimam que a construção e a manutenção da "
        "ETL consomem parcela majoritária do esforço total de um projeto de "
        "Business Intelligence, e atribuem a essa camada a responsabilidade "
        "por três entregas: obter os dados da origem com o menor impacto "
        "possível sobre o sistema transacional, submetê-los a limpeza e "
        "conformação, e entregá-los ao modelo dimensional de maneira "
        "auditável.")

    par(doc,
        "A etapa de extração pode operar em dois regimes. Na carga completa "
        "(full load), a totalidade dos dados de origem é lida e o destino é "
        "reconstruído a cada ciclo. A abordagem é simples e autocorretiva, "
        "porém seu custo cresce linearmente com o volume acumulado, tornando-se "
        "proibitiva à medida que o histórico se acumula. Na carga incremental, "
        "apenas os registros criados ou modificados desde o último ciclo são "
        "processados, o que mantém o custo proporcional ao movimento do período "
        "e não ao tamanho da base.")

    par(doc,
        "A viabilização da carga incremental depende de algum mecanismo de "
        "identificação de mudanças, genericamente designado Change Data "
        "Capture. Vaisman e Zimányi (2022) descrevem as alternativas usuais: "
        "leitura do log de transações do SGBD, gatilhos que registram "
        "alterações em tabelas auxiliares, comparação integral entre origem e "
        "destino, e uso de colunas de auditoria de data e hora. As três "
        "primeiras oferecem maior completude — capturam inclusive exclusões "
        "físicas — ao custo de intervenção no sistema de origem ou de leitura "
        "integral dos dados. A quarta é não intrusiva e computacionalmente "
        "econômica, exigindo em contrapartida que a origem mantenha "
        "disciplinadamente uma coluna de data de modificação.")

    par(doc,
        "A técnica associada a essa quarta alternativa é a marca d'água, ou "
        "high-water mark: o processo registra, ao final de cada ciclo, o maior "
        "valor da coluna de auditoria já processado, e restringe a extração "
        "seguinte aos registros que superem esse valor. Sua correção repousa "
        "sobre duas condições que o projeto da ETL precisa assegurar "
        "explicitamente — a marca só pode avançar após a confirmação "
        "transacional da carga, e a aplicação dos dados no destino precisa ser "
        "idempotente, de modo que o reprocessamento de uma mesma janela não "
        "produza duplicação.")

    # -------------------------------------------------- 3 DESENVOLVIMENTO
    secao(doc, "3", "Desenvolvimento")

    subsecao(doc, "3.1", "Análise do modelo transacional de origem")

    par(doc,
        "A base AdventureWorks, em sua versão 2022, foi restaurada em uma "
        "instância Microsoft SQL Server Express e submetida a análise "
        "estrutural. A base reúne 71 tabelas distribuídas em seis esquemas, "
        "dos quais cinco são funcionais — Sales, Purchasing, Production, "
        "Person e HumanResources — e correspondem aos macroprocessos da "
        "empresa modelada, enquanto o sexto (dbo) concentra objetos de "
        "controle do próprio banco.")

    par(doc,
        "A inspeção do catálogo do SQL Server revelou duas características "
        "determinantes para as decisões subsequentes. A primeira é que "
        "praticamente todas as tabelas de negócio mantêm a coluna de auditoria "
        "ModifiedDate, atualizada a cada alteração. Essa constatação viabilizou "
        "a adoção da estratégia de marca d'água, dispensando gatilhos ou "
        "leitura de log na origem. A segunda é a separação clássica entre "
        "cabeçalho e itens nas tabelas transacionais: Sales.SalesOrderHeader "
        "concentra os atributos do pedido, enquanto Sales.SalesOrderDetail "
        "armazena suas linhas. Essa separação define naturalmente a "
        "granularidade candidata do modelo dimensional e, como se discutirá na "
        "seção 3.7, impõe cuidado específico à detecção de mudanças.")

    quadro(
        doc,
        "Quadro 1 – Tabelas de origem selecionadas e respectivos volumes",
        ["Esquema.Tabela", "Registros", "Papel no modelo dimensional"],
        [
            ["Sales.SalesOrderDetail", "121.317", "Grão da fato de vendas"],
            ["Sales.SalesOrderHeader", "31.465", "Atributos do pedido de venda"],
            ["Purchasing.PurchaseOrderDetail", "8.845", "Grão da fato de compras"],
            ["Purchasing.PurchaseOrderHeader", "4.012", "Atributos da ordem de compra"],
            ["Production.Product", "504", "Dimensão produto"],
            ["Production.ProductCostHistory", "395", "Custo histórico do produto"],
            ["Sales.Customer", "19.820", "Dimensão cliente"],
            ["Person.Address", "19.614", "Dimensão geografia"],
            ["HumanResources.Employee", "290", "Dimensão funcionário"],
            ["Purchasing.Vendor", "104", "Dimensão fornecedor"],
            ["Sales.SalesTerritory", "10", "Dimensão território"],
            ["Sales.SpecialOffer", "16", "Dimensão promoção"],
        ],
        "Fonte: elaborado pelos autores a partir do catálogo do SQL Server (2026).",
        larguras=[6.0, 2.6, 6.9],
    )

    subsecao(doc, "3.2", "Definição dos indicadores")

    par(doc,
        "Os indicadores foram definidos antes da modelagem, e não depois dela. "
        "A ordem não é arbitrária: em modelagem dimensional, é o conjunto de "
        "perguntas que o negócio precisa responder que determina o grão da "
        "tabela fato e a composição das dimensões. Foram elaborados dez "
        "indicadores, distribuídos entre os processos de vendas e de compras, "
        "conforme o Quadro 2.")

    quadro(
        doc,
        "Quadro 2 – Indicadores propostos e respectivas fórmulas de cálculo",
        ["#", "Indicador", "Fórmula", "Dimensões de análise"],
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
            ["08", "Pontualidade de Entrega (OTD)",
             "itens no prazo / itens entregues × 100",
             "Tempo, Método de envio, Geografia"],
            ["09", "Desempenho da Força de Vendas",
             "receita do vendedor / cota × 100",
             "Tempo, Funcionário, Território"],
            ["10", "Custo e Rejeição por Fornecedor",
             "SUM(qt_rejeitada) / SUM(qt_recebida) × 100",
             "Tempo, Fornecedor, Produto"],
        ],
        "Fonte: elaborado pelos autores (2026).",
        tamanho=8.5,
        larguras=[0.9, 3.9, 5.4, 5.3],
    )

    par(doc,
        "A distribuição dos indicadores não é homogênea por acaso. Nove deles "
        "recaem sobre o processo de vendas, que concentra o interesse gerencial "
        "primário, e o décimo sobre o processo de compras. Essa inclusão não é "
        "ornamental: é precisamente o indicador de compras que exige a segunda "
        "tabela fato e, por consequência, torna necessária a conformidade das "
        "dimensões tempo, produto, funcionário, método de envio e status — "
        "demonstrando na prática o mecanismo de integração descrito na seção "
        "2.4.")

    subsecao(doc, "3.3", "Modelo estrela proposto")

    par(doc,
        "O modelo resultante compreende duas tabelas fato e onze dimensões, "
        "cinco delas conformadas. A Figura 1 apresenta sua estrutura, "
        "destacando em cores distintas as dimensões compartilhadas entre os "
        "dois processos e aquelas exclusivas de um deles.")

    if FIGURA_MODELO.exists():
        figura(
            doc, FIGURA_MODELO,
            "Figura 1 – Modelo estrela do Data Warehouse AdventureWorks",
            "Fonte: elaborado pelos autores (2026).",
        )

    par(doc,
        "A declaração de grão das duas tabelas fato foi estabelecida no nível "
        "mais atômico disponível na origem. Cada linha de dw.fato_vendas "
        "representa um item de um pedido de venda; cada linha de "
        "dw.fato_compras representa um item de uma ordem de compra. A escolha "
        "do grão atômico, e não de um nível pré-agregado, decorre da orientação "
        "de Kimball e Ross (2013) segundo a qual o grão mais fino confere ao "
        "modelo a máxima flexibilidade analítica, uma vez que qualquer "
        "agregação pode ser derivada do detalhe, mas nenhum detalhe pode ser "
        "recuperado a partir de uma agregação previamente consolidada.")

    par(doc,
        "As medidas armazenadas nas tabelas fato são predominantemente "
        "aditivas, isto é, podem ser somadas ao longo de qualquer dimensão sem "
        "perda de significado. Valores percentuais — como a taxa de desconto "
        "unitária — são não aditivos e, por essa razão, são armazenados em sua "
        "forma decomposta: registra-se o valor monetário do desconto, que é "
        "aditivo, e o percentual é recalculado no momento da consulta como "
        "razão entre somatórios. Essa decomposição evita o erro clássico de "
        "calcular a média aritmética de percentuais, que atribui peso idêntico "
        "a transações de magnitudes distintas.")

    quadro(
        doc,
        "Quadro 3 – Composição das tabelas do modelo dimensional",
        ["Tabela", "Tipo", "Grão / Chave natural", "Linhas"],
        [
            ["dw.fato_vendas", "Fato transacional",
             "Item de pedido de venda", "121.319"],
            ["dw.fato_compras", "Fato transacional",
             "Item de ordem de compra", "8.845"],
            ["dw.dim_tempo", "Dimensão conformada", "Data do calendário", "6.092"],
            ["dw.dim_produto", "Dimensão conformada (SCD 2)",
             "Versão de produto", "506"],
            ["dw.dim_funcionario", "Dimensão conformada (SCD 1)",
             "Funcionário", "291"],
            ["dw.dim_metodo_envio", "Dimensão conformada (SCD 1)",
             "Modalidade de frete", "6"],
            ["dw.dim_status_pedido", "Dimensão conformada (estática)",
             "Situação do pedido", "11"],
            ["dw.dim_cliente", "Dimensão (SCD 1)", "Cliente", "19.821"],
            ["dw.dim_geografia", "Dimensão (SCD 1)", "Endereço", "19.615"],
            ["dw.dim_territorio", "Dimensão (SCD 1)", "Território", "11"],
            ["dw.dim_fornecedor", "Dimensão (SCD 1)", "Fornecedor", "105"],
            ["dw.dim_promocao", "Dimensão (SCD 1)", "Oferta", "17"],
            ["dw.dim_canal_venda", "Dimensão (estática)", "Canal de venda", "3"],
        ],
        "Fonte: elaborado pelos autores a partir do banco implantado (2026). "
        "As contagens incluem o membro “Não Informado” de cada dimensão.",
        tamanho=8.5,
        larguras=[4.0, 4.6, 4.4, 2.5],
    )

    subsecao(doc, "3.4", "Implementação no PostgreSQL")

    par(doc,
        "O Data Warehouse foi implantado em PostgreSQL 16, executado em "
        "contêiner Docker descrito de forma declarativa em um arquivo "
        "docker-compose.yml versionado junto ao projeto. A opção pela "
        "conteinerização atende a um requisito prático de trabalho acadêmico "
        "em grupo: qualquer integrante levanta um ambiente idêntico com um "
        "único comando, e o esquema é recriado automaticamente na primeira "
        "inicialização, o que elimina divergências de configuração entre as "
        "máquinas.")

    par(doc,
        "O banco foi organizado em três esquemas com responsabilidades "
        "distintas. O esquema dw abriga o modelo dimensional propriamente "
        "dito, consumido pelas consultas analíticas. O esquema stg funciona "
        "como área de staging, recebendo a cada ciclo o recorte incremental "
        "extraído da origem, sem chaves nem índices, de modo a privilegiar a "
        "velocidade de ingestão. O esquema meta armazena os metadados de "
        "controle da ETL — as marcas d'água e o log de execuções.")

    par(doc,
        "A nomenclatura das colunas segue convenção de prefixos que explicita "
        "a natureza semântica de cada atributo: sk_ para chaves substitutas, "
        "id_ para chaves naturais herdadas da origem, vl_ para valores "
        "monetários, qt_ para quantidades, pc_ para percentuais, dt_ para "
        "datas e fl_ para indicadores lógicos. A convenção reduz a "
        "ambiguidade na escrita de consultas e permite inferir o "
        "comportamento agregativo de uma medida a partir de seu próprio nome.")

    par(doc,
        "A documentação do modelo foi registrada no próprio catálogo do "
        "PostgreSQL, por meio de instruções COMMENT ON aplicadas a todas as "
        "tabelas e colunas. O dicionário de dados do projeto é extraído desse "
        "catálogo por rotina automatizada, o que assegura que a documentação "
        "jamais divirja da estrutura efetivamente implantada — problema comum "
        "em dicionários mantidos manualmente em documentos apartados.")

    subsecao(doc, "3.5", "Estratégia de ETL incremental")

    par(doc,
        "A ETL foi desenvolvida em Python, com acesso à origem por meio da "
        "biblioteca pyodbc e ao destino por meio de psycopg. O ciclo de carga "
        "de cada entidade percorre cinco etapas encadeadas, descritas a "
        "seguir.")

    par(doc,
        "Na primeira etapa, o processo consulta a tabela meta.etl_controle "
        "para recuperar a marca d'água da entidade, isto é, o maior valor de "
        "ModifiedDate já processado com sucesso. Na implantação inicial, essa "
        "marca vale 1900-01-01, de modo que a primeira execução equivale "
        "naturalmente a uma carga completa, sem exigir código específico para "
        "esse caso.")

    par(doc,
        "Na segunda etapa, a marca recuperada é reduzida por uma janela de "
        "retrocesso (lookback) de poucos segundos antes de compor o predicado "
        "de extração. A medida protege contra uma condição de corrida "
        "conhecida: uma transação de longa duração pode gravar em "
        "ModifiedDate o instante em que se iniciou e tornar-se visível a "
        "outras sessões apenas depois que um ciclo de ETL já avançou a marca "
        "além daquele instante, o que faria o registro nunca ser capturado. O "
        "retrocesso amplia deliberadamente a janela, aceitando reprocessar "
        "registros já carregados — o que é inofensivo, dada a idempotência "
        "descrita adiante — em troca da garantia de não perder nenhum.")

    par(doc,
        "Na terceira etapa, os dados extraídos são gravados na tabela de "
        "staging correspondente por meio do comando COPY, que no PostgreSQL "
        "oferece desempenho de ingestão substancialmente superior ao de "
        "instruções INSERT individuais. A tabela de staging é truncada antes "
        "de cada carga, de modo que contenha exclusivamente o recorte do ciclo "
        "corrente.")

    par(doc,
        "Na quarta etapa, os dados são promovidos do staging para o modelo "
        "dimensional por meio de instruções SQL executadas integralmente "
        "dentro do PostgreSQL. Essa opção arquitetural — transformar no "
        "destino, e não em memória no processo Python — mantém o volume de "
        "dados trafegado pela rede restrito ao recorte incremental e delega ao "
        "otimizador do SGBD as junções de resolução de chaves substitutas.")

    par(doc,
        "Na quinta etapa, e somente após a confirmação bem-sucedida de todas "
        "as escritas, a marca d'água é avançada para o maior ModifiedDate "
        "observado no lote e a transação é confirmada. A ordem é essencial: "
        "avançar a marca antes da confirmação abriria a possibilidade de o "
        "processo falhar após o avanço, fazendo com que os registros da janela "
        "jamais fossem reprocessados. Cada entidade é processada em transação "
        "independente, de modo que a falha em uma delas não desfaz a carga já "
        "confirmada das demais, e a marca da entidade que falhou permanece "
        "inalterada — o que faz o ciclo seguinte reprocessar exatamente a "
        "janela pendente.")

    par(doc,
        "A idempotência da carga é assegurada pelo uso sistemático da cláusula "
        "ON CONFLICT do PostgreSQL. Nas tabelas fato, a chave de conflito é a "
        "dimensão degenerada que identifica a transação na origem, e a "
        "atualização é condicionada ao predicado apresentado a seguir, que "
        "impede que um reprocessamento sobrescreva um dado mais recente por um "
        "mais antigo.")

    codigo(doc, [
        "ON CONFLICT (id_item_venda) DO UPDATE",
        "   SET vl_liquido            = EXCLUDED.vl_liquido,",
        "       -- demais colunas ...",
        "       dt_atualizacao        = CURRENT_TIMESTAMP",
        " WHERE f.dt_modificacao_origem <= EXCLUDED.dt_modificacao_origem;",
    ])

    par(doc,
        "Nas dimensões de tipo 1, a atualização é adicionalmente condicionada "
        "à divergência de um resumo criptográfico MD5 calculado sobre os "
        "atributos monitorados. Registros que retornam do staging sem "
        "alteração efetiva de conteúdo não sofrem escrita alguma, o que evita "
        "inflar desnecessariamente o log de transações e preserva a "
        "fidedignidade da coluna dt_atualizacao como registro do último "
        "momento em que o dado de fato mudou.")

    par(doc,
        "A dimensão produto, historizada como SCD Tipo 2, exige tratamento em "
        "três passos sequenciais: identificação dos registros cujo resumo "
        "divergiu da versão vigente, encerramento dessa versão pelo "
        "preenchimento da data de fim de vigência, e inserção da nova versão. "
        "Os três passos são executados como instruções distintas dentro de uma "
        "mesma transação, e não como uma única instrução com expressões de "
        "tabela comuns modificadoras. A razão é técnica: no PostgreSQL, as "
        "sub-instruções de um mesmo comando enxergam o mesmo instantâneo de "
        "dados e não têm ordem de execução garantida, o que colocaria o "
        "encerramento da versão antiga e a inserção da nova em disputa pelo "
        "índice único parcial que assegura a existência de uma única versão "
        "corrente por produto.")

    par(doc,
        "Merece registro específico a detecção de mudanças nas tabelas fato. "
        "Como cabeçalho e itens são tabelas distintas na origem, alterações "
        "restritas ao cabeçalho — o preenchimento da data de envio de um pedido "
        "já registrado, por exemplo — atualizam apenas "
        "SalesOrderHeader.ModifiedDate, sem tocar nas linhas de detalhe. Uma "
        "extração que observasse somente a coluna de auditoria do detalhe "
        "perderia silenciosamente essas atualizações. A consulta de extração "
        "adotada, por isso, avalia o predicado sobre ambas as tabelas e adota "
        "como data de modificação do registro a maior entre as duas.")

    codigo(doc, [
        "WHERE d.ModifiedDate > ? OR h.ModifiedDate > ?",
        "-- e, na projecao:",
        "CASE WHEN h.ModifiedDate > d.ModifiedDate",
        "     THEN h.ModifiedDate ELSE d.ModifiedDate END AS dt_modificacao_origem",
    ])

    par(doc,
        "Cabe explicitar, por fim, a limitação inerente à estratégia adotada. "
        "A marca d'água sobre coluna de auditoria não detecta exclusões "
        "físicas: um registro removido da origem por DELETE permanece "
        "indefinidamente no Data Warehouse, pois não há alteração de "
        "ModifiedDate a ser observada. A limitação é aceitável no contexto "
        "deste trabalho, uma vez que sistemas transacionais de porte "
        "corporativo tipicamente praticam exclusão lógica; sua superação "
        "demandaria a adoção de Change Data Capture baseado em log de "
        "transações, alternativa discutida na seção 2.6 e registrada na seção "
        "4 como possibilidade de continuidade.")

    subsecao(doc, "3.6", "Justificativa das decisões de modelagem")

    par(doc,
        "Sete decisões de projeto merecem justificativa explícita, por não "
        "decorrerem automaticamente da aplicação do padrão estrela.")

    par(doc,
        "A primeira é a adoção de duas tabelas fato, e não de uma única tabela "
        "que abrangesse vendas e compras. Os dois processos possuem "
        "granularidades e conjuntos de medidas incompatíveis: uma linha de "
        "venda mede receita, desconto e margem; uma linha de compra mede "
        "quantidade recebida, rejeitada e custo de aquisição. Unificá-las "
        "produziria uma tabela esparsa, com metade das colunas nulas em cada "
        "linha, e imporia ao usuário a obrigação de filtrar por tipo de "
        "transação em toda consulta. A separação com dimensões conformadas "
        "preserva a clareza semântica de cada processo e mantém a integração "
        "pelos eixos comuns.")

    par(doc,
        "A segunda é a aplicação de SCD Tipo 2 exclusivamente à dimensão "
        "produto. Preço de tabela e custo padrão evoluem ao longo do tempo e "
        "sua evolução tem significado analítico direto: sem historização, um "
        "reajuste aplicado hoje reescreveria retroativamente a margem de todas "
        "as vendas passadas. Já a correção do endereço de correio eletrônico de "
        "um cliente ou a atualização do cargo de um funcionário não sustentam "
        "análise histórica que justifique o custo de versionamento, e por isso "
        "foram tratadas por sobrescrita.")

    par(doc,
        "A terceira é a unificação de vendedores e compradores em uma única "
        "dimensão de funcionários, referenciada em papéis distintos por cada "
        "tabela fato. Ambos são registros da mesma tabela de origem "
        "(HumanResources.Employee) e compartilham os mesmos atributos "
        "descritivos; mantê-los em dimensões separadas duplicaria dados e "
        "impediria análises que cruzem os dois papéis.")

    par(doc,
        "A quarta é a busca do custo do produto em Production.ProductCostHistory, "
        "tomando a versão vigente na data do pedido, em vez do custo corrente "
        "registrado no cadastro. Utilizar o custo atual para calcular a margem "
        "de uma venda realizada há três anos produziria um indicador "
        "historicamente falso. A decisão é coerente com a propriedade de "
        "variação no tempo enunciada por Inmon (2005).")

    par(doc,
        "A quinta é o rateio de frete e imposto do cabeçalho do pedido entre "
        "suas linhas, na proporção da receita líquida de cada uma. Medidas "
        "registradas no cabeçalho não pertencem ao grão da tabela fato; "
        "replicá-las integralmente em cada linha faria com que sua soma "
        "contabilizasse o mesmo valor tantas vezes quantos fossem os itens do "
        "pedido. O rateio proporcional torna a medida aditiva no grão adotado, "
        "conforme a orientação de Kimball e Ross (2013) para medidas de "
        "cabeçalho em fatos de linha.")

    par(doc,
        "A sexta é a criação, em cada dimensão, de um membro “Não "
        "Informado” identificado pela chave substituta −1. Chaves "
        "estrangeiras nulas em tabelas fato inviabilizariam junções internas e "
        "produziriam contagens divergentes conforme o tipo de junção "
        "empregado. Direcionar ao membro −1 as chaves ausentes na origem — "
        "como o vendedor de um pedido realizado pela internet — preserva a "
        "integridade referencial e torna a ausência de informação um dado "
        "explícito e mensurável, e não uma lacuna silenciosa.")

    par(doc,
        "A sétima é a adoção de chave substituta inteligente na dimensão "
        "tempo, no formato AAAAMMDD. A prática contraria a regra geral de que "
        "chaves substitutas devem ser destituídas de significado, e a exceção "
        "é justificada por Kimball e Ross (2013) para essa dimensão "
        "específica: o calendário é a única dimensão cujo conteúdo é "
        "inteiramente previsível e imutável, e a chave inteligente dispensa a "
        "junção de resolução durante a carga dos fatos, além de tornar as "
        "partições por período diretamente legíveis.")

    subsecao(doc, "3.7", "Resultados obtidos")

    par(doc,
        "A carga inicial processou 170.525 registros em 17,95 segundos. A "
        "conferência entre origem e destino, executada pela rotina de "
        "validação do projeto, confirmou a identidade das contagens em todas "
        "as tabelas e a equivalência dos somatórios monetários, com divergência "
        "residual de R$ 0,03 sobre um total de R$ 109.846.381,40 — resultado "
        "do arredondamento decimal decorrente do recálculo da receita líquida "
        "no destino, e não de perda de registros.")

    quadro(
        doc,
        "Quadro 4 – Comparativo entre os ciclos de carga executados",
        ["Ciclo", "Situação", "Registros processados", "Duração"],
        [
            ["1º", "Carga inicial (completa)", "170.525", "17,95 s"],
            ["2º", "Sem alterações na origem", "20.023", "1,03 s"],
            ["3º", "Após movimento simulado no OLTP", "20.027", "1,62 s"],
        ],
        "Fonte: elaborado pelos autores a partir de meta.etl_execucao (2026).",
        larguras=[1.6, 6.0, 4.4, 3.5],
    )

    par(doc,
        "A redução de 17,95 para 1,03 segundo entre o primeiro e o segundo "
        "ciclo — 94,3% menos tempo — evidencia o ganho da estratégia "
        "incremental. Observa-se, contudo, que o segundo ciclo ainda extraiu "
        "20.023 registros apesar de nada ter mudado na origem. O fenômeno "
        "decorre da distribuição dos valores de ModifiedDate na base de "
        "demonstração: as 19.820 linhas de Sales.Customer compartilham a mesma "
        "data de modificação, de modo que a janela de retrocesso as recaptura "
        "integralmente. Nenhuma escrita efetiva ocorreu, porque a comparação de "
        "resumo MD5 identificou a ausência de alteração de conteúdo — "
        "demonstrando que os dois mecanismos operam em camadas complementares: "
        "o retrocesso privilegia a completude da extração, e a verificação de "
        "resumo protege o destino do custo de escritas inúteis.")

    par(doc,
        "Para comprovar empiricamente o comportamento incremental, um script "
        "de simulação provocou na base de origem três eventos distintos: o "
        "reajuste de 10% no preço de tabela de um produto, a alteração "
        "cadastral de um fornecedor e a inserção de um pedido de venda com "
        "dois itens. O ciclo subsequente processou corretamente os três "
        "eventos, conforme o Quadro 5.")

    quadro(
        doc,
        "Quadro 5 – Efeitos do movimento simulado na origem sobre o Data Warehouse",
        ["Evento na origem", "Tratamento", "Efeito observado no DW"],
        [
            ["Reajuste de preço do produto 707",
             "SCD Tipo 2",
             "Versão 1 encerrada em 27/08; versão 2 criada, vigente e com o novo preço"],
            ["Alteração do nível de crédito do fornecedor 1492",
             "SCD Tipo 1",
             "Linha única sobrescrita; dt_carga preservada e dt_atualizacao renovada"],
            ["Inserção de pedido com dois itens",
             "MERGE na fato",
             "Duas linhas acrescentadas a dw.fato_vendas"],
        ],
        "Fonte: elaborado pelos autores (2026).",
        tamanho=8.5,
        larguras=[4.4, 2.8, 8.3],
    )

    par(doc,
        "O efeito prático da historização merece destaque. Após o reajuste, as "
        "3.083 linhas de venda do produto 707 registradas entre 2011 e 2014 "
        "permaneceram vinculadas à versão de preço R$ 34,99, enquanto a venda "
        "posterior à alteração vinculou-se à versão de R$ 42,34. É essa "
        "propriedade que permite reconstruir com fidelidade o contexto vigente "
        "em qualquer período passado, e que se perderia integralmente sob "
        "tratamento por sobrescrita.")

    par(doc,
        "Quanto aos indicadores, as dez consultas foram executadas sobre o "
        "modelo carregado, sem qualquer acesso à base transacional. O Quadro 6 "
        "consolida os principais resultados apurados.")

    quadro(
        doc,
        "Quadro 6 – Resultados consolidados dos indicadores",
        ["Indicador", "Resultado apurado"],
        [
            ["Receita líquida total", "R$ 109.846.549,38"],
            ["Pedidos distintos", "31.466"],
            ["Ticket médio por pedido", "R$ 3.490,96"],
            ["Margem bruta percentual", "11,43%"],
            ["Taxa média de desconto", "0,4779%"],
            ["Mix por canal", "Revenda 73,3% e Internet 26,7% da receita"],
            ["Curva ABC", "23,7% dos produtos (classe A) concentram 79,9% da receita"],
            ["Pontualidade de entrega (OTD)", "100,00% em ambas as transportadoras"],
            ["Maior receita individual por vendedor", "R$ 10.367.007,43 (Linda C. Mitchell)"],
            ["Volume total adquirido de fornecedores", "R$ 63.791.994,84"],
            ["Maior taxa de rejeição de fornecedor", "5,88%"],
        ],
        "Fonte: elaborado pelos autores a partir do Data Warehouse implantado (2026).",
        larguras=[7.0, 8.5],
    )

    par(doc,
        "Dois resultados merecem leitura crítica. O primeiro é o indicador de "
        "pontualidade de entrega, que apresentou 100% em todas as "
        "transportadoras e territórios. O valor não descreve excelência "
        "logística, e sim uma característica da base de demonstração, na qual "
        "as datas de envio e de vencimento são geradas por regra determinística "
        "— sete e doze dias após o pedido, respectivamente —, de modo que "
        "nenhum atraso pode ocorrer. O indicador permanece no modelo por sua "
        "validade metodológica: a estrutura que o sustenta produziria "
        "resultados significativos sobre dados reais. O segundo é a curva ABC, "
        "cuja aderência ao princípio de Pareto se confirmou de forma nítida — "
        "63 dos 266 produtos comercializados, ou 23,7% do catálogo, respondem "
        "por praticamente 80% da receita, ao passo que 137 produtos, mais da "
        "metade do catálogo, somam apenas 5,1%.")

    par(doc,
        "Registre-se ainda a variação da margem bruta ao longo dos anos "
        "analisados — 15,1% em 2011, 9,0% em 2012, 9,6% em 2013 e 17,2% em "
        "2014 —, resultado que só é apurável porque o custo utilizado no "
        "cálculo é o vigente na data de cada pedido. Sob a alternativa de "
        "empregar o custo corrente do cadastro, a série apresentaria "
        "comportamento uniforme e artificial, ilustrando concretamente a "
        "consequência analítica de uma decisão de modelagem.")

    subsecao(doc, "3.8", "Repositório do projeto")

    par(doc,
        "O código-fonte da ETL, os scripts SQL do Data Warehouse, o arquivo de "
        "orquestração do contêiner, o dicionário de dados e os scripts de "
        "geração do diagrama estão disponíveis no repositório público indicado "
        "a seguir.", recuo=False)

    paragrafo = doc.add_paragraph()
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragrafo.paragraph_format.space_before = Pt(6)
    paragrafo.paragraph_format.space_after = Pt(6)
    _fonte(paragrafo.add_run(
        "https://github.com/[usuario]/dw-adventureworks-produto1"), 12,
        negrito=True)

    par(doc,
        "O repositório inclui instruções completas de reprodução do ambiente, "
        "abrangendo a subida do contêiner PostgreSQL, a configuração das "
        "credenciais de acesso à origem e a execução das cargas completa e "
        "incremental.")

    # ------------------------------------------- 4 CONSIDERAÇÕES FINAIS
    secao(doc, "4", "Considerações finais")

    par(doc,
        "Este artigo apresentou o projeto e a implementação de um Data "
        "Warehouse construído a partir da base transacional AdventureWorks, "
        "abrangendo a análise do modelo de origem, a definição de dez "
        "indicadores gerenciais, o desenho de um modelo estrela com duas "
        "tabelas fato e onze dimensões, sua implantação em PostgreSQL e o "
        "desenvolvimento de um processo de ETL incremental em Python.")

    par(doc,
        "Os objetivos propostos foram integralmente atendidos. O modelo "
        "dimensional sustenta os dez indicadores por meio de consultas que "
        "operam exclusivamente sobre a camada analítica. A ETL demonstrou "
        "comportamento incremental verificável, reduzindo o tempo de "
        "processamento em 94,3% entre a carga inicial e os ciclos subsequentes, "
        "e a conferência entre origem e destino confirmou a consistência dos "
        "dados carregados.")

    par(doc,
        "Do percurso, extraem-se três aprendizados de natureza conceitual. O "
        "primeiro é que a definição dos indicadores precede necessariamente a "
        "modelagem: foi a inclusão de um indicador de qualidade de "
        "fornecimento que impôs a segunda tabela fato e, com ela, a "
        "necessidade de dimensões conformadas. O segundo é que a carga "
        "incremental correta não se resume a filtrar a extração por data de "
        "modificação; ela exige o encadeamento disciplinado de três "
        "propriedades — extração conservadora por janela de retrocesso, "
        "aplicação idempotente no destino e avanço da marca d'água somente "
        "após confirmação transacional —, cuja ausência isolada compromete "
        "todo o mecanismo. O terceiro é que decisões aparentemente técnicas "
        "possuem consequências analíticas diretas, como evidenciou o uso do "
        "custo histórico em lugar do custo corrente no cálculo da margem.")

    par(doc,
        "O trabalho apresenta limitações que delimitam o alcance de seus "
        "resultados. A estratégia de detecção de mudanças não captura "
        "exclusões físicas na origem. A base utilizada é sintética, o que se "
        "manifestou de forma explícita no indicador de pontualidade de "
        "entrega. Não foram implementadas tabelas agregadas nem "
        "particionamento, recursos cuja necessidade só se manifesta em volumes "
        "substancialmente superiores aos aqui processados.")

    par(doc,
        "Como continuidade, identificam-se quatro direções. A substituição da "
        "marca d'água por Change Data Capture baseado em log de transações "
        "permitiria capturar exclusões e reduzir ainda mais o volume extraído. "
        "A introdução de uma fato de estoque com granularidade de instantâneo "
        "periódico exercitaria a modelagem de medidas semiaditivas, ausente do "
        "escopo atual. A construção de tabelas agregadas com atualização "
        "incremental atenderia a cenários de volume elevado. Por fim, a "
        "orquestração do pipeline por ferramenta especializada, como Apache "
        "Airflow, adicionaria escalonamento, monitoramento e política "
        "automatizada de repetição em caso de falha.")

    # ------------------------------------------------------- REFERÊNCIAS
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
        (": the definitive guide to dimensional modeling. 3. ed. "
         "Indianapolis: John Wiley & Sons, 2013.", False),
    ])

    referencia(doc, [
        ("MACHADO, F. N. R. ", False),
        ("Tecnologia e projeto de data warehouse", True),
        (": uma visão multidimensional. 6. ed. São Paulo: Érica, 2013.", False),
    ])

    referencia(doc, [
        ("MICROSOFT. ", False),
        ("AdventureWorks sample databases", True),
        (". [S. l.]: Microsoft Learn, 2024. Disponível em: "
         "https://learn.microsoft.com/pt-br/sql/samples/adventureworks-install-configure. "
         "Acesso em: 28 ago. 2026.", False),
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

    # -------------------------------------------------- APENDICES
    apendice(doc, "A", "Scripts SQL dos indicadores")

    par(doc,
        "Reproduzem-se a seguir, na integra, as consultas que implementam os "
        "dez indicadores apresentados no Quadro 2. Todas operam exclusivamente "
        "sobre o modelo dimensional, sem qualquer acesso ao sistema "
        "transacional de origem.", recuo=False)

    linhas_sql = _ler_scripts_kpi()
    if linhas_sql:
        codigo(doc, linhas_sql)

    apendice(doc, "B", "Dicionário de dados do Data Warehouse")

    par(doc,
        "O dicionário abaixo é extraído do catálogo do próprio PostgreSQL "
        "(pg_class, pg_attribute e pg_description), o que assegura sua "
        "correspondência exata com a estrutura implantada. A coluna Chave "
        "identifica chaves primárias (PK) e estrangeiras (FK), com a "
        "respectiva tabela referenciada.", recuo=False)

    for nome_tabela, descricao_tabela, colunas in _ler_dicionario():
        subtitulo = doc.add_paragraph()
        subtitulo.paragraph_format.space_before = Pt(12)
        subtitulo.paragraph_format.space_after = Pt(3)
        subtitulo.paragraph_format.keep_with_next = True
        _fonte(subtitulo.add_run(nome_tabela), 11, negrito=True)

        if descricao_tabela:
            texto = doc.add_paragraph()
            texto.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            texto.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
            texto.paragraph_format.space_after = Pt(3)
            texto.paragraph_format.keep_with_next = True
            _fonte(texto.add_run(descricao_tabela), 10, italico=True)

        quadro(doc, "", ["Coluna", "Tipo", "Nulo", "Chave", "Descrição"],
               colunas,
               "",
               tamanho=7.5, larguras=[3.6, 2.6, 1.1, 3.0, 5.2])

    doc.save(SAIDA)
    return SAIDA


if __name__ == "__main__":
    print(f"Artigo gerado em: {montar()}")
