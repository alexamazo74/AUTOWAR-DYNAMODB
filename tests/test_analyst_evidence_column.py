"""Pruebas de regresion del BUG 1: columna 'Evidencia' angosta en la vista de analista.

El reporte en pantalla del pilar de Seguridad (frontend-new/analyst.html) mostraba
la columna 'Evidencia' demasiado angosta. La causa era que el ancho se controlaba
unicamente dentro del div .evidence-text (con un max-width) y la tabla no fijaba su
layout ni repartia anchos por columna a nivel de <th>.

Estas pruebas leen el HTML con la libreria estandar (sin dependencias nuevas) y
afirman el contrato de la solucion a nivel de tabla/columna:
  (a) .findings-table declara table-layout: fixed;
  (b) el <th> de 'Evidencia' declara width explicito a nivel de celda;
  (c) los 7 <th> del <thead> declaran width;
  (d) anti-regresion: el width de 'Evidencia' vive en el <th>, no solo en .evidence-text.
"""

import os
import re

# Misma convencion de ruta que conftest.py: la raiz del repo es dos niveles arriba.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYST_HTML = os.path.join(REPO_ROOT, "frontend-new", "analyst.html")


def _leer_html():
    with open(ANALYST_HTML, "r", encoding="utf-8") as fh:
        return fh.read()


def _bloque_regla_css(html, selector):
    """Devuelve el cuerpo ({...}) de la primera regla CSS cuyo selector coincide.

    `selector` es el texto literal del selector (p.ej. '.findings-table'). Se busca
    el selector seguido de '{' y se captura hasta la '}' de cierre.
    """
    patron = re.compile(re.escape(selector) + r"\s*\{([^}]*)\}")
    m = patron.search(html)
    return m.group(1) if m else None


def _ths_del_thead(html):
    """Extrae la lista de <th ...>...</th> del primer <thead> de la tabla de hallazgos."""
    thead_m = re.search(r"<thead\b[^>]*>(.*?)</thead>", html, re.DOTALL | re.IGNORECASE)
    assert thead_m, "No se encontro el <thead> de la tabla de hallazgos en analyst.html."
    return re.findall(r"<th\b([^>]*)>(.*?)</th>", thead_m.group(1), re.DOTALL | re.IGNORECASE)


def _tiene_width(atributos):
    """True si la cadena de atributos del <th> declara un width explicito (% o px) via style."""
    style_m = re.search(r'style\s*=\s*"([^"]*)"', atributos, re.IGNORECASE)
    if not style_m:
        return False
    return re.search(r"\bwidth\s*:\s*\d+(?:\.\d+)?\s*(?:%|px)", style_m.group(1), re.IGNORECASE) is not None


def test_findings_table_usa_table_layout_fixed():
    """(a) La regla .findings-table debe declarar table-layout: fixed."""
    html = _leer_html()
    bloque = _bloque_regla_css(html, ".findings-table")
    assert bloque is not None, "No se encontro la regla CSS .findings-table en analyst.html."
    assert re.search(r"table-layout\s*:\s*fixed", bloque, re.IGNORECASE), (
        "La regla .findings-table debe declarar 'table-layout: fixed;' para que los "
        "anchos por columna se respeten y la columna Evidencia no quede angosta."
    )


def test_th_evidencia_declara_width_explicito():
    """(b) El <th> de 'Evidencia' debe declarar width explicito a nivel de celda."""
    ths = _ths_del_thead(_leer_html())
    evidencia = [attrs for attrs, texto in ths if "Evidencia" in texto]
    assert evidencia, "No se encontro el <th> de 'Evidencia' en el <thead>."
    assert _tiene_width(evidencia[0]), (
        "El <th> de 'Evidencia' debe declarar un width explicito (% o px) a nivel de "
        "celda para ampliar la columna; no basta con el ancho del div .evidence-text."
    )


def test_los_siete_th_declaran_width():
    """(c) Los 7 <th> del <thead> deben declarar width (y Evidencia ser el mayor)."""
    ths = _ths_del_thead(_leer_html())
    assert len(ths) == 7, f"Se esperaban 7 <th> en el <thead>, se encontraron {len(ths)}."

    sin_width = [texto.strip() for attrs, texto in ths if not _tiene_width(attrs)]
    assert not sin_width, (
        "Todos los <th> del <thead> deben declarar width para repartir el ancho de la "
        f"tabla; sin width: {sin_width}."
    )

    # Evidencia debe ser la columna mas ancha (solo se comparan widths en %).
    anchos = {}
    for attrs, texto in ths:
        m = re.search(r"\bwidth\s*:\s*(\d+(?:\.\d+)?)\s*%", attrs, re.IGNORECASE)
        if m:
            anchos[texto.strip()] = float(m.group(1))
    evidencia_key = next((k for k in anchos if "Evidencia" in k), None)
    assert evidencia_key is not None, (
        "El <th> de 'Evidencia' debe declarar su width en porcentaje para compararlo."
    )
    assert anchos[evidencia_key] == max(anchos.values()), (
        f"La columna 'Evidencia' ({anchos[evidencia_key]}%) debe ser la mas ancha; "
        f"anchos actuales: {anchos}."
    )


def test_width_evidencia_vive_en_el_th_no_solo_en_evidence_text():
    """(d) Anti-regresion: el ancho de Evidencia esta en el <th>, no solo en .evidence-text."""
    html = _leer_html()

    ths = _ths_del_thead(html)
    evidencia = [attrs for attrs, texto in ths if "Evidencia" in texto]
    assert evidencia and _tiene_width(evidencia[0]), (
        "El width de la columna 'Evidencia' debe declararse en su <th> (no unicamente "
        "dentro de .evidence-text), que fue la causa del bug original."
    )

    bloque = _bloque_regla_css(html, ".evidence-text")
    assert bloque is not None, "No se encontro la regla CSS .evidence-text en analyst.html."
    assert not re.search(r"max-width\s*:", bloque, re.IGNORECASE), (
        "La regla .evidence-text no debe fijar max-width: el ancho lo controla ahora la "
        "columna (<th>) con table-layout: fixed."
    )
