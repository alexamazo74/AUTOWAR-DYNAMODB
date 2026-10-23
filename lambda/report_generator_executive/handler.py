"""
Executive Report Generator Lambda
Generates business-oriented reports in DOCX format
"""

import json
import logging
import io
import os
from datetime import datetime

import matplotlib
matplotlib.use('Agg')  # headless backend (Lambda has no display)
import matplotlib.pyplot as plt

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from autowar_common.report_storage import upload_report, generate_signed_url

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# GFourmis corporate palette
GF_ORANGE = RGBColor(0xF0, 0x60, 0x00)  # primary orange
GF_RED = RGBColor(0xC0, 0x10, 0x10)     # corporate red
GF_BLACK = RGBColor(0x1A, 0x1A, 0x1A)   # text black

# matplotlib hex strings for the palette and semantic status colors.
MPL_ORANGE = '#F06000'
MPL_RED = '#C01010'
MPL_BLACK = '#1A1A1A'
# Cumple = green, No cumple = red, Pendiente = amber, No aplica = neutral gray.
MPL_STATUS = {
    'COMPLIANT': '#2E7D32',
    'NON_COMPLIANT': '#C01010',
    'PENDING_REVIEW': '#F0A500',
    'NOT_APPLICABLE': '#9E9E9E',
}

# Scoring weights. NOT_APPLICABLE is intentionally absent (applicable only).
_SCORE_MAP = {'COMPLIANT': 100.0, 'NON_COMPLIANT': 0.0, 'PENDING_REVIEW': 50.0}

PILLAR_NAMES = {
    'security': 'Seguridad',
    'reliability': 'Fiabilidad',
    'performance': 'Rendimiento',
    'cost': 'Optimización de Costos',
    'operationalExcellence': 'Excelencia Operacional',
    'sustainability': 'Sostenibilidad',
}


def resolve_asset_path(filename):
    """Resolve a branding asset path with a Lambda-first fallback.

    Tries the Lambda layer mount (/opt/python/autowar_assets/<filename>) first,
    then falls back to the project-relative path computed from this handler's
    location so it also works in local tests. Returns the first existing path
    or None.
    """
    lambda_path = os.path.join('/opt/python', 'autowar_assets', filename)
    if os.path.exists(lambda_path):
        return lambda_path

    handler_dir = os.path.dirname(os.path.abspath(__file__))
    local_path = os.path.abspath(os.path.join(
        handler_dir, '..', 'layers', 'reports', 'python', 'autowar_assets', filename
    ))
    if os.path.exists(local_path):
        return local_path

    logger.info(f"Branding asset not found: {filename} (tried {lambda_path} and {local_path})")
    return None


def compliance_percentage(bps):
    """Compliance percentage EXCLUDING NOT_APPLICABLE from the denominator."""
    applicable = [bp for bp in bps if bp.get('status') != 'NOT_APPLICABLE']
    if not applicable:
        return 0.0
    total = sum(_SCORE_MAP.get(bp.get('status', ''), 0.0) for bp in applicable)
    return round(total / len(applicable), 1)


def count_statuses(bps):
    """Count best practices by status (4 categories + total)."""
    return {
        'compliant': sum(1 for bp in bps if bp.get('status') == 'COMPLIANT'),
        'non_compliant': sum(1 for bp in bps if bp.get('status') == 'NON_COMPLIANT'),
        'pending': sum(1 for bp in bps if bp.get('status') == 'PENDING_REVIEW'),
        'not_applicable': sum(1 for bp in bps if bp.get('status') == 'NOT_APPLICABLE'),
        'total': len(bps),
    }


# Ordered keyword rules mapping a best practice to a business risk scenario.
# Source of truth: .agents/tasks/riesgos_negocio.md (paraphrased, Spanish,
# managerial language). First rule with any keyword present in the haystack
# (bpId + description + finding, lowercased) wins.
RISK_RULES = [
    (
        ['mfa', 'multi-factor', 'sin mfa', 'root'],
        {
            'amenaza': 'Toma de control de la cuenta AWS.',
            'actor': 'Atacante con credenciales robadas (phishing o fuga de secretos).',
            'consecuencia': 'Control total de la nube del cliente: creación de recursos para '
                            'minería o fraude, borrado masivo de información y acceso a todos los '
                            'datos. Impacto crítico en continuidad, costos y confidencialidad.',
        },
    ),
    (
        ['s3', 'bucket', 'publico', 'público', 'public access', 'sin cifrado', 'encryption'],
        {
            'amenaza': 'Exfiltración (robo) de información sensible o exposición pública de datos.',
            'actor': 'Cualquiera en Internet (bots que escanean buckets abiertos) o un insider.',
            'consecuencia': 'Robo y publicación de datos de clientes y del negocio, con multas por '
                            'protección de datos (Ley 1581 de Habeas Data / SIC en Colombia), daño '
                            'reputacional y riesgo de extorsión con la información robada.',
        },
    ),
    (
        ['security group', 'puerto', '0.0.0.0', 'ssh', 'rdp', '22', '3389', 'ingress', 'abierto'],
        {
            'amenaza': 'Acceso no autorizado a servidores expuestos a Internet.',
            'actor': 'Atacante que escanea puertos abiertos y fuerza credenciales (fuerza bruta).',
            'consecuencia': 'Intrusión en los servidores, instalación de malware y pivote hacia la '
                            'red interna, con robo o cifrado de datos. Es el punto de entrada típico '
                            'de un ataque de ransomware (secuestro de información).',
        },
    ),
    (
        ['cloudtrail', 'log', 'logging', 'sin registro', 'auditoria', 'auditoría',
         'guardduty', 'deteccion', 'detección'],
        {
            'amenaza': 'Actividad maliciosa invisible: resulta imposible detectar o investigar un '
                       'incidente.',
            'actor': 'Atacante que opera sin dejar rastro o un insider que borra evidencias.',
            'consecuencia': 'Los ataques pasan desapercibidos durante meses, no hay forense tras una '
                            'brecha y se incumplen requisitos de auditoría y de respuesta a incidentes.',
        },
    ),
    (
        ['kms', 'cifrado', 'encryption', 'en reposo', 'en transito', 'en tránsito',
         'tls', 'certificado', 'acm'],
        {
            'amenaza': 'Interceptación o lectura de datos en tránsito o en reposo.',
            'actor': 'Atacante en la red (man-in-the-middle) o con acceso a discos y backups.',
            'consecuencia': 'Robo de datos confidenciales, credenciales y secretos; suplantación de '
                            'servicios e incumplimiento regulatorio por no cifrar datos personales '
                            '(Ley 1581 de Habeas Data / SIC).',
        },
    ),
    (
        ['waf', 'cloudfront', 'frontend', 'web', 'inyeccion', 'inyección', 'xss', 'sql'],
        {
            'amenaza': 'Suplantación del frontend, defacement, inyección de código y robo de sesiones.',
            'actor': 'Atacante web automatizado o dirigido.',
            'consecuencia': 'Suplantación de la aplicación para engañar a los usuarios (phishing con '
                            'su marca), robo de credenciales de clientes, manipulación de contenido '
                            'y caída del sitio.',
        },
    ),
    (
        ['iam', 'permiso', 'privilegio', 'politica', 'política', '*:*', 'admin', 'acceso'],
        {
            'amenaza': 'Abuso de permisos excesivos y escalada de privilegios.',
            'actor': 'Insider malicioso, cuenta comprometida o un error que un atacante aprovecha.',
            'consecuencia': 'Un único acceso comprometido se convierte en control total, con '
                            'movimiento lateral y acceso a datos y recursos más allá de lo necesario.',
        },
    ),
    (
        ['backup', 'snapshot', 'pitr', 'recuperacion', 'recuperación', 'retention', 'retención', 'dr'],
        {
            'amenaza': 'Pérdida irreversible de datos e incapacidad de recuperarse de un incidente.',
            'actor': 'Ransomware que cifra datos y backups, o un borrado accidental o malicioso.',
            'consecuencia': 'Pérdida permanente de información del negocio, parada prolongada de la '
                            'operación y pago de rescate sin garantía de recuperación.',
        },
    ),
    (
        ['multi-az', 'alta disponibilidad', 'single point', 'failover', 'autoscaling', 'auto scaling'],
        {
            'amenaza': 'Caída total del servicio ante el fallo de un componente o una zona.',
            'actor': 'Fallo de infraestructura, pico de demanda o un ataque de denegación (DoS).',
            'consecuencia': 'Indisponibilidad del servicio, pérdida de ventas y operación, '
                            'incumplimiento de SLA y daño reputacional.',
        },
    ),
    (
        ['vulnerab', 'parche', 'patch', 'cve', 'imagen', 'hardening', 'inspector'],
        {
            'amenaza': 'Explotación de vulnerabilidades conocidas sin parchar.',
            'actor': 'Atacante que usa exploits públicos contra software desactualizado.',
            'consecuencia': 'Compromiso de servidores, ransomware y robo de datos; es el vector más '
                            'común de brechas masivas.',
        },
    ),
]

# Fallback scenarios by pilar (normalized key) when no keyword rule matches.
RISK_FALLBACK_BY_PILAR = {
    'security': {
        'amenaza': 'Exposición de datos y sistemas a accesos no autorizados.',
        'actor': 'Actor malicioso externo o interno.',
        'consecuencia': 'Riesgo de robo o secuestro de información, suplantación y fraude.',
    },
    'reliability': {
        'amenaza': 'Interrupciones del servicio y pérdida de datos ante fallos.',
        'actor': 'Fallo de infraestructura o de componentes de la carga de trabajo.',
        'consecuencia': 'Impacto en la continuidad del negocio y en la experiencia del cliente.',
    },
    'performance': {
        'amenaza': 'Degradación de la experiencia por recursos mal dimensionados.',
        'actor': 'Picos de demanda o configuración ineficiente.',
        'consecuencia': 'Mala experiencia de usuario que ahuyenta clientes y reduce ingresos, '
                        'además de sobrecostos operativos por recursos mal ajustados.',
    },
    'cost': {
        'amenaza': 'Fuga de dinero por recursos ociosos o sobredimensionados.',
        'actor': 'Configuración ineficiente y falta de gobierno de costos.',
        'consecuencia': 'Gasto innecesario que erosiona el margen del negocio y desvía presupuesto '
                        'que podría invertirse en crecimiento.',
    },
    'operationalExcellence': {
        'amenaza': 'Incidentes mal gestionados y cambios riesgosos.',
        'actor': 'Procesos manuales y falta de visibilidad operativa.',
        'consecuencia': 'Mayor tiempo de resolución, errores recurrentes y baja previsibilidad.',
    },
    'sustainability': {
        'amenaza': 'Uso ineficiente de recursos en la nube.',
        'actor': 'Dimensionamiento y patrones de consumo subóptimos.',
        'consecuencia': 'Impacto ambiental y de costo evitable.',
    },
}


def map_risk_scenarios(bp):
    """Map a best practice to a business risk scenario.

    Returns a dict {'amenaza', 'actor', 'consecuencia'} based on keyword rules
    (searched across bpId + description + finding, case-insensitive). If no rule
    matches, falls back to the pilar-level generic scenario (defaulting to
    'security' as a last resort for unknown pilares).
    """
    haystack = f"{bp.get('bpId', '')} {bp.get('description', '')} {bp.get('finding', '')}".lower()

    for keywords, scenario in RISK_RULES:
        if any(kw in haystack for kw in keywords):
            return scenario

    pilar_normalized = bp.get('pilar', '').replace('_', '').lower()
    pilar_key_map = {
        'security': 'security',
        'reliability': 'reliability',
        'performance': 'performance',
        'cost': 'cost',
        'operationalexcellence': 'operationalExcellence',
        'sustainability': 'sustainability',
    }
    key = pilar_key_map.get(pilar_normalized, 'security')
    return RISK_FALLBACK_BY_PILAR[key]


def lambda_handler(event, context):
    """
    Generate executive report in DOCX format
    
    Input:
    {
        "accountId": "...",
        "evaluationTimestamp": "...",
        "evaluationData": {...},
        "selectedPilares": ["security", "reliability", ...]
    }
    
    Output:
    {
        "s3Key": "...",
        "signedUrl": "...",
        "expiresIn": 3600
    }
    """
    try:
        # Parse input
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        account_id = body.get('accountId')
        evaluation_timestamp = body.get('evaluationTimestamp')
        evaluation_data = body.get('evaluationData')
        selected_pilares = body.get('selectedPilares', [])
        user_info = body.get('userInfo', {})
        
        logger.info(f"Generating executive report for account {account_id}")
        
        # Generate DOCX report
        docx_content = generate_executive_report(
            evaluation_data,
            selected_pilares,
            account_id,
            evaluation_timestamp,
            user_info
        )
        
        # Upload to S3
        s3_key = upload_report(
            account_id,
            evaluation_timestamp,
            'executive',
            docx_content,
            'docx'
        )
        
        # Generate signed URL
        signed_url = generate_signed_url(s3_key, expiration_seconds=3600)
        
        logger.info(f"Executive report generated: {s3_key}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                's3Key': s3_key,
                'signedUrl': signed_url,
                'expiresIn': 3600
            })
        }
        
    except Exception as e:
        logger.error(f"Error generating executive report: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to generate executive report',
                'message': str(e)
            })
        }


def generate_executive_report(evaluation_data, selected_pilares, account_id, evaluation_timestamp, user_info=None):
    """Generate executive report DOCX content"""
    
    doc = Document()
    
    # Title page
    add_title_page(doc, account_id, evaluation_timestamp, user_info)
    
    # Executive summary (with embedded charts)
    add_executive_summary(doc, evaluation_data, selected_pilares)
    
    # Pillar analysis sections
    for pilar in selected_pilares:
        add_pilar_section(doc, evaluation_data, pilar)
    
    # Deep business impact and real cases
    add_business_impact_section(doc, evaluation_data, selected_pilares)
    add_real_cases_section(doc)
    
    # Conclusions and recommendations
    add_conclusions(doc, evaluation_data, selected_pilares)
    
    # Save to bytes
    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    
    return output.read()


def _color_heading(heading, color):
    """Apply a font color to all runs of a heading (defensive if it has none)."""
    for run in heading.runs:
        run.font.color.rgb = color


def _fig_to_doc(doc, fig, caption):
    """Embed a matplotlib figure into the document and add an italic caption."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    doc.add_picture(buf, width=Inches(6))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap_run = cap.add_run(caption)
    cap_run.italic = True
    cap_run.font.size = Pt(9)
    cap_run.font.color.rgb = GF_BLACK


# ---------------------------------------------------------------------------
# Charts (matplotlib)
# ---------------------------------------------------------------------------

def chart_scores_por_pilar(pillar_scores, selected_pilares):
    """Vertical bar chart of score per pilar in corporate orange."""
    labels = [PILLAR_NAMES.get(p, p) for p in selected_pilares]
    values = [pillar_scores.get(p, 0) for p in selected_pilares]
    if not labels:
        return None
    fig, ax = plt.subplots(figsize=(8, 4.2))
    bars = ax.bar(labels, values, color=MPL_ORANGE, edgecolor=MPL_BLACK, linewidth=0.5)
    ax.set_ylim(0, 100)
    ax.set_ylabel('Score (%)')
    ax.set_title('Score por Pilar', color=MPL_BLACK, fontweight='bold')
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f'{v}', ha='center', va='bottom', fontsize=9)
    ax.tick_params(axis='x', rotation=20)
    fig.tight_layout()
    return fig


def chart_cumplimiento_global(counts):
    """Donut chart of the 4 status categories with semantic colors."""
    labels = ['Cumplen', 'No Cumplen', 'Pendientes', 'No Aplican']
    sizes = [counts['compliant'], counts['non_compliant'], counts['pending'], counts['not_applicable']]
    colors = [MPL_STATUS['COMPLIANT'], MPL_STATUS['NON_COMPLIANT'],
              MPL_STATUS['PENDING_REVIEW'], MPL_STATUS['NOT_APPLICABLE']]
    # Drop zero slices to keep the donut clean.
    data = [(l, s, c) for l, s, c in zip(labels, sizes, colors) if s > 0]
    if not data:
        return None
    labels, sizes, colors = zip(*data)
    fig, ax = plt.subplots(figsize=(6.5, 4.6))
    wedges, _texts, _auto = ax.pie(
        sizes, labels=labels, colors=colors, autopct='%1.0f%%',
        startangle=90, wedgeprops=dict(width=0.42, edgecolor='white'),
        pctdistance=0.78,
    )
    ax.set_title('Distribución Global de Cumplimiento', color=MPL_BLACK, fontweight='bold')
    ax.axis('equal')
    fig.tight_layout()
    return fig


def chart_severidad_hallazgos(non_compliant_bps):
    """Bar chart of NON_COMPLIANT counts by severity (crimson -> neutral)."""
    order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
    labels_es = {'CRITICAL': 'Crítica', 'HIGH': 'Alta', 'MEDIUM': 'Media', 'LOW': 'Baja'}
    counts = {s: 0 for s in order}
    for bp in non_compliant_bps:
        sev = bp.get('severity')
        if sev in counts:
            counts[sev] += 1
    if sum(counts.values()) == 0:
        return None
    colors = ['#C01010', '#E53935', '#F0A500', '#9E9E9E']
    fig, ax = plt.subplots(figsize=(7.5, 4))
    bars = ax.bar([labels_es[s] for s in order], [counts[s] for s in order], color=colors,
                  edgecolor=MPL_BLACK, linewidth=0.5)
    ax.set_ylabel('Hallazgos No Conformes')
    ax.set_title('Hallazgos No Conformes por Severidad', color=MPL_BLACK, fontweight='bold')
    for b in bars:
        h = b.get_height()
        if h > 0:
            ax.text(b.get_x() + b.get_width() / 2, h + 0.1, f'{int(h)}', ha='center', va='bottom', fontsize=9)
    fig.tight_layout()
    return fig


def chart_ranking_pilares(pillar_scores, selected_pilares):
    """Horizontal 'traffic light' ranking of pilares by score (ascending)."""
    pairs = [(PILLAR_NAMES.get(p, p), pillar_scores.get(p, 0)) for p in selected_pilares]
    if not pairs:
        return None
    pairs.sort(key=lambda x: x[1])  # worst first
    labels = [p[0] for p in pairs]
    values = [p[1] for p in pairs]

    def band_color(v):
        if v < 40:
            return '#C01010'
        if v < 60:
            return '#F0A500'
        if v < 80:
            return '#C0CA33'
        return '#2E7D32'

    colors = [band_color(v) for v in values]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    bars = ax.barh(labels, values, color=colors, edgecolor=MPL_BLACK, linewidth=0.5)
    ax.set_xlim(0, 100)
    ax.set_xlabel('Score (%)')
    ax.set_title('Semáforo de Pilares por Criticidad', color=MPL_BLACK, fontweight='bold')
    for b, v in zip(bars, values):
        ax.text(v + 1.5, b.get_y() + b.get_height() / 2, f'{v}', va='center', fontsize=9)
    fig.tight_layout()
    return fig


def add_title_page(doc, account_id, evaluation_timestamp, user_info=None):
    """Add title page"""
    
    # GFourmis logo centered at the top
    logo_path = resolve_asset_path('gfourmis-logo.png')
    if logo_path:
        try:
            doc.add_picture(logo_path, width=Inches(2.5))
            doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        except Exception as e:
            logger.info(f"Could not embed logo in title page: {e}")
    
    # Title
    title = doc.add_heading('Reporte Ejecutivo', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _color_heading(title, GF_ORANGE)
    
    subtitle = doc.add_heading('AWS Well-Architected Review', level=2)
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Brand footer line
    brand = doc.add_paragraph()
    brand.alignment = WD_ALIGN_PARAGRAPH.CENTER
    brand_run = brand.add_run('GFourmis — Strategic & digital solutions')
    brand_run.font.size = Pt(11)
    brand_run.font.color.rgb = GF_RED
    brand_run.italic = True
    
    # Metadata
    doc.add_paragraph()
    doc.add_paragraph()
    
    metadata = doc.add_paragraph()
    metadata.add_run(f'Cuenta AWS: ').bold = True
    metadata.add_run(account_id)
    
    metadata = doc.add_paragraph()
    metadata.add_run(f'Fecha de Evaluación: ').bold = True
    metadata.add_run(evaluation_timestamp)
    
    metadata = doc.add_paragraph()
    metadata.add_run(f'Fecha de Generación: ').bold = True
    metadata.add_run(datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S UTC'))
    
    # User information
    if user_info:
        metadata = doc.add_paragraph()
        metadata.add_run(f'Usuario: ').bold = True
        metadata.add_run(f"{user_info.get('user_name', 'Unknown')} ({user_info.get('user_type', 'Unknown')})")
        
        metadata = doc.add_paragraph()
        metadata.add_run(f'User ID: ').bold = True
        metadata.add_run(user_info.get('user_id', 'Unknown'))
    
    # Page break
    doc.add_page_break()


def add_executive_summary(doc, evaluation_data, selected_pilares):
    """Add executive summary section with embedded charts"""
    
    _color_heading(doc.add_heading('Resumen Ejecutivo', level=1), GF_ORANGE)
    
    pillar_scores = evaluation_data.get('pillarScores', {})
    best_practices = evaluation_data.get('bestPractices', [])
    
    # Metrics over the selected pilares only.
    selected_pilares_normalized = [p.replace('_', '').lower() for p in selected_pilares]
    filtered_bps = [
        bp for bp in best_practices 
        if bp.get('pilar', '').replace('_', '').lower() in selected_pilares_normalized
    ]
    counts = count_statuses(filtered_bps)
    total_bps = counts['total']
    applicable = total_bps - counts['not_applicable']

    # Overall score EXCLUDING NOT_APPLICABLE from the denominator.
    overall_score = compliance_percentage(filtered_bps)

    doc.add_paragraph(
        f'Este reporte presenta un análisis estratégico de la evaluación Well-Architected '
        f'realizada para la cuenta AWS {evaluation_data.get("metadata", {}).get("accountId", "N/A")}. '
        f'Se evaluaron {len(selected_pilares)} pilares con un total de {total_bps} mejores prácticas '
        f'({applicable} aplicables).'
    )
    
    doc.add_paragraph()
    
    # Key findings
    doc.add_heading('Hallazgos Clave', level=2)

    def _pct(n):
        return round(n / applicable * 100, 1) if applicable > 0 else 0

    findings_para = doc.add_paragraph()
    findings_para.add_run('• Score Global (sobre prácticas aplicables): ').bold = True
    findings_para.add_run(f'{overall_score}%')
    
    findings_para = doc.add_paragraph()
    findings_para.add_run('• Prácticas Conformes: ').bold = True
    findings_para.add_run(f'{counts["compliant"]} de {applicable} aplicables ({_pct(counts["compliant"])}%)')
    
    findings_para = doc.add_paragraph()
    findings_para.add_run('• Prácticas No Conformes: ').bold = True
    findings_para.add_run(f'{counts["non_compliant"]} de {applicable} aplicables ({_pct(counts["non_compliant"])}%)')
    
    findings_para = doc.add_paragraph()
    findings_para.add_run('• Prácticas Pendientes de Revisión: ').bold = True
    findings_para.add_run(f'{counts["pending"]} de {applicable} aplicables ({_pct(counts["pending"])}%)')

    findings_para = doc.add_paragraph()
    findings_para.add_run('• Prácticas No Aplicables: ').bold = True
    findings_para.add_run(f'{counts["not_applicable"]} de {total_bps} (excluidas del cálculo de cumplimiento)')
    
    doc.add_paragraph()

    # Embedded charts (only when there is data).
    if total_bps > 0:
        doc.add_heading('Tablero Visual', level=2)
        non_compliant_bps = [bp for bp in filtered_bps if bp.get('status') == 'NON_COMPLIANT']

        fig = chart_scores_por_pilar(pillar_scores, selected_pilares)
        if fig is not None:
            _fig_to_doc(doc, fig, 'Figura 1. Score de cumplimiento por pilar (mayor es mejor).')

        fig = chart_cumplimiento_global(counts)
        if fig is not None:
            _fig_to_doc(doc, fig, 'Figura 2. Distribución global de estados de las mejores prácticas evaluadas.')

        fig = chart_severidad_hallazgos(non_compliant_bps)
        if fig is not None:
            _fig_to_doc(doc, fig, 'Figura 3. Hallazgos no conformes agrupados por severidad.')

        fig = chart_ranking_pilares(pillar_scores, selected_pilares)
        if fig is not None:
            _fig_to_doc(doc, fig, 'Figura 4. Semáforo de pilares ordenados por criticidad (rojo = acción inmediata).')

    doc.add_paragraph()
    
    # Pillar scores (textual)
    doc.add_heading('Scores por Pilar', level=2)

    for pilar in selected_pilares:
        score = pillar_scores.get(pilar, 0)
        score_para = doc.add_paragraph()
        score_para.add_run(f'• {PILLAR_NAMES.get(pilar, pilar)}: ').bold = True
        score_para.add_run(f'{score}/100')
        
        if score >= 80:
            score_para.add_run(' - Excelente')
        elif score >= 60:
            score_para.add_run(' - Bueno, con oportunidades de mejora')
        elif score >= 40:
            score_para.add_run(' - Requiere atención')
        else:
            score_para.add_run(' - Requiere acción inmediata')
    
    doc.add_page_break()


def add_pilar_section(doc, evaluation_data, pilar):
    """Add analysis section for a specific pilar"""
    
    pillar_descriptions = {
        'security': 'La seguridad es fundamental para proteger la información, sistemas y activos de su organización.',
        'reliability': 'La Fiabilidad asegura que su carga de trabajo funcione correctamente y de manera consistente.',
        'performance': 'El rendimiento eficiente permite utilizar los recursos de manera óptima.',
        'cost': 'La optimización de costos permite ejecutar sistemas para entregar valor de negocio al menor precio.',
        'operationalExcellence': 'La excelencia operacional permite ejecutar y monitorear sistemas para entregar valor de negocio.',
        'sustainability': 'La sostenibilidad minimiza los impactos ambientales de ejecutar cargas de trabajo en la nube.'
    }
    
    _color_heading(doc.add_heading(f'Análisis: {PILLAR_NAMES.get(pilar, pilar)}', level=1), GF_ORANGE)
    
    doc.add_paragraph(pillar_descriptions.get(pilar, ''))
    doc.add_paragraph()
    
    pillar_scores = evaluation_data.get('pillarScores', {})
    score = pillar_scores.get(pilar, 0)
    
    score_para = doc.add_paragraph()
    score_para.add_run('Score del Pilar: ').bold = True
    score_para.add_run(f'{score}/100')
    
    doc.add_paragraph()
    
    doc.add_heading('Hallazgos Principales', level=2)
    
    best_practices = evaluation_data.get('bestPractices', [])
    pilar_normalized = pilar.replace('_', '').lower()
    pilar_bps = [
        bp for bp in best_practices 
        if bp.get('pilar', '').replace('_', '').lower() == pilar_normalized
    ]
    
    non_compliant_bps = [bp for bp in pilar_bps if bp.get('status') == 'NON_COMPLIANT']
    
    if non_compliant_bps:
        doc.add_paragraph(f'Se identificaron {len(non_compliant_bps)} áreas que requieren atención:')
        for bp in non_compliant_bps[:5]:
            bp_para = doc.add_paragraph(style='List Bullet')
            bp_para.add_run(f'{bp.get("bpId", "")}: ').bold = True
            bp_para.add_run(bp.get('finding', ''))
    else:
        doc.add_paragraph('Este pilar cumple con todas las mejores prácticas evaluadas.')
    
    doc.add_paragraph()
    
    # Risk scenarios and consequences (for ALL pilares with non-compliant BPs,
    # using keyword rules + the pilar fallback for Performance/Cost/etc.).
    add_risk_scenarios_subsection(doc, non_compliant_bps, pilar)
    
    # Business impact
    doc.add_heading('Impacto de Negocio', level=2)
    
    if score < 60:
        doc.add_paragraph(
            f'El score actual de {score}/100 indica riesgos significativos que pueden afectar '
            f'la continuidad del negocio, la seguridad de los datos, o los costos operacionales. '
            f'Se recomienda priorizar las remediaciones identificadas.'
        )
    elif score < 80:
        doc.add_paragraph(
            f'El score de {score}/100 es aceptable, pero existen oportunidades de mejora que '
            f'pueden optimizar la operación y reducir riesgos potenciales.'
        )
    else:
        doc.add_paragraph(
            f'El score de {score}/100 indica un excelente nivel de madurez en este pilar. '
            f'Se recomienda mantener las prácticas actuales y revisar periódicamente.'
        )
    
    doc.add_page_break()


def add_risk_scenarios_subsection(doc, non_compliant_bps, pilar=None):
    """Add the 'Escenarios de Riesgo y Consecuencias' subsection for a pilar.

    For each NON_COMPLIANT best practice with CRITICAL or HIGH severity (criticals
    first, limited to the first ~8), writes a readable block describing the
    threat, actor and business consequence in managerial Spanish. When there are
    no high/critical non-compliant findings but the pilar has other non-compliant
    findings (e.g. Performance/Cost with MEDIUM severity), it still emits the
    pilar-level fallback scenario so every affected pilar is covered.
    """
    doc.add_heading('Escenarios de Riesgo y Consecuencias', level=2)

    severity_order = {'CRITICAL': 0, 'HIGH': 1}
    high_risk_bps = [bp for bp in non_compliant_bps if bp.get('severity') in severity_order]
    high_risk_bps.sort(key=lambda bp: severity_order.get(bp.get('severity'), 99))
    high_risk_bps = high_risk_bps[:8]

    if high_risk_bps:
        for bp in high_risk_bps:
            scenario = map_risk_scenarios(bp)

            threat_para = doc.add_paragraph()
            threat_run = threat_para.add_run(f'{bp.get("bpId", "")} — {scenario["amenaza"]}')
            threat_run.bold = True

            actor_para = doc.add_paragraph()
            actor_para.add_run('Actor: ').bold = True
            actor_para.add_run(scenario['actor'])

            consequence_para = doc.add_paragraph()
            consequence_para.add_run('Consecuencia: ').bold = True
            consequence_para.add_run(scenario['consecuencia'])

            doc.add_paragraph()
    elif non_compliant_bps:
        # Lower-severity non-compliant findings (common in Performance/Cost):
        # still surface the pilar-level business risk via the fallback scenario.
        sample = non_compliant_bps[0]
        scenario = map_risk_scenarios(sample)
        intro = doc.add_paragraph()
        intro.add_run(
            f'Se identificaron {len(non_compliant_bps)} hallazgos no conformes de severidad media '
            f'o baja. Aunque no representan riesgo crítico inmediato, su acumulación impacta al '
            f'negocio de la siguiente forma:'
        )
        threat_para = doc.add_paragraph()
        threat_para.add_run(scenario['amenaza']).bold = True
        actor_para = doc.add_paragraph()
        actor_para.add_run('Actor / Causa: ').bold = True
        actor_para.add_run(scenario['actor'])
        consequence_para = doc.add_paragraph()
        consequence_para.add_run('Consecuencia: ').bold = True
        consequence_para.add_run(scenario['consecuencia'])
        doc.add_paragraph()
    else:
        doc.add_paragraph(
            'No se identificaron escenarios de riesgo (hallazgos no conformes) en este pilar.'
        )
        return

    note_para = doc.add_paragraph()
    note_run = note_para.add_run(
        'Nota: estos escenarios describen el riesgo potencial si el hallazgo no se remedia; '
        'no implican que el ataque haya ocurrido.'
    )
    note_run.italic = True

    doc.add_paragraph()


def add_business_impact_section(doc, evaluation_data, selected_pilares):
    """Global 'Impacto de Negocio y Costo de No Actuar' section.

    Describes concrete, POTENTIAL business consequences for the critical/high
    NON_COMPLIANT findings across all evaluated pilares, using the concepts in
    .agents/tasks/casos_impacto_negocio.md (loss of information assets, revenue
    loss from reputation damage, ransomware interruption, SIC/Ley 1581 fines,
    up to business closure).
    """
    heading = doc.add_heading('Impacto de Negocio y Costo de No Actuar', level=1)
    _color_heading(heading, GF_RED)

    best_practices = evaluation_data.get('bestPractices', [])
    selected_norm = [p.replace('_', '').lower() for p in selected_pilares]
    filtered = [bp for bp in best_practices
                if bp.get('pilar', '').replace('_', '').lower() in selected_norm]
    critical_high = [bp for bp in filtered
                     if bp.get('status') == 'NON_COMPLIANT' and bp.get('severity') in ('CRITICAL', 'HIGH')]

    doc.add_paragraph(
        'Los hallazgos no conformes de mayor severidad no son solo un asunto técnico: representan '
        'un riesgo de negocio con costo real y potencial si no se remedian. A continuación se '
        'traduce ese riesgo a términos de negocio.'
    )
    doc.add_paragraph()

    doc.add_heading('Consecuencias potenciales si no se actúa', level=2)
    impactos = [
        ('Pérdida de patrimonio y activos de información',
         'El robo o la destrucción de datos críticos del negocio (clientes, operación, propiedad '
         'intelectual) equivale a perder parte del patrimonio de la empresa.'),
        ('Pérdida de la mayoría de los ingresos por daño reputacional',
         'Una brecha pública genera fuga de clientes y pérdida de confianza; para muchas empresas '
         'esto se traduce en la caída de la mayor parte de sus ingresos.'),
        ('Interrupción operativa por ransomware',
         'Un ataque de ransomware cifra datos y backups y detiene la operación por días o semanas, '
         'con pago de rescate sin garantía de recuperación.'),
        ('Sanciones regulatorias en Colombia',
         'El incumplimiento en protección de datos personales (Ley 1581 de Habeas Data) puede '
         'derivar en multas de la SIC de hasta ~COP 2.320 millones (2.000 SMMLV) y suspensión de '
         'actividades, además de litigios.'),
        ('Costo directo de respuesta y recuperación',
         'La referencia global de IBM sitúa el costo promedio de una brecha de datos en USD 4.88 '
         'millones (USD 6.08 millones en el sector financiero).'),
        ('Cierre del negocio en el peor escenario',
         'Hasta ~60% de las pymes que sufren un ciberataque grave se ven forzadas a cerrar en '
         'menos de 6 meses.'),
    ]
    for titulo, texto in impactos:
        p = doc.add_paragraph(style='List Bullet')
        p.add_run(f'{titulo}: ').bold = True
        p.add_run(texto)

    doc.add_paragraph()

    if critical_high:
        doc.add_heading('Hallazgos críticos/altos y su traducción a negocio', level=2)
        for bp in critical_high[:10]:
            scenario = map_risk_scenarios(bp)
            pilar_label = PILLAR_NAMES.get(bp.get('pilar', ''), bp.get('pilar', ''))
            block = doc.add_paragraph()
            block.add_run(f'{bp.get("bpId", "")} ({pilar_label}, {bp.get("severity", "")}): ').bold = True
            block.add_run(scenario['consecuencia'])
    else:
        doc.add_paragraph(
            'No se identificaron hallazgos críticos o altos no conformes en los pilares evaluados; '
            'aun así, se recomienda remediar los hallazgos de menor severidad para evitar que se '
            'acumulen en un riesgo mayor.'
        )

    doc.add_paragraph()
    nota = doc.add_paragraph()
    nota_run = nota.add_run(
        'Importante: todas las consecuencias descritas son riesgos POTENCIALES si los hallazgos no '
        'se remedian; no representan incidentes ya ocurridos en la cuenta evaluada.'
    )
    nota_run.italic = True

    doc.add_page_break()


def add_real_cases_section(doc):
    """'Casos Reales y Costo de No Actuar' section with verified cases + sources.

    Content curated from .agents/tasks/casos_impacto_negocio.md. Sources shown as
    visible text (literal URLs). Figures preserved; wording paraphrased.
    """
    heading = doc.add_heading('Casos Reales y Costo de No Actuar', level=1)
    _color_heading(heading, GF_RED)

    doc.add_paragraph(
        'Los siguientes casos reales ilustran lo que ha ocurrido cuando organizaciones no cumplieron '
        'mejores prácticas equivalentes a las evaluadas en este reporte. Las cifras corresponden a '
        'empresas afectadas reales; el riesgo para su organización es potencial si no se remedia.'
    )
    doc.add_paragraph()

    # Caso 1 — Capital One 2019
    doc.add_heading('Caso 1 — Capital One (configuración incorrecta en la nube)', level=2)
    p = doc.add_paragraph()
    p.add_run('Qué pasó: ').bold = True
    p.add_run('un atacante aprovechó una configuración incorrecta (firewall/WAF mal configurado y '
              'permisos excesivos) para acceder a más de 700 buckets y robar datos de ~106 millones '
              'de solicitantes de crédito.')
    p = doc.add_paragraph()
    p.add_run('Impacto de negocio: ').bold = True
    p.add_run('multa regulatoria de USD 80 millones (OCC) más un acuerdo de demanda colectiva de '
              'USD 190 millones, además de órdenes de remediación.')
    p = doc.add_paragraph()
    p.add_run('Mejor práctica incumplida: ').bold = True
    p.add_run('Seguridad — protección de red (WAF/SSRF), privilegios mínimos (IAM) y protección de '
              'datos (S3).')
    doc.add_paragraph('Fuente: ZDNet — https://www.zdnet.com/article/capital-one-fined-80-million-for-2019-hack/')
    doc.add_paragraph('Fuente: MVA Law — https://www.mvalaw.com/data-points/capital-one-reaches-190-million-settlement-in-connection-with')
    doc.add_paragraph()

    # Caso 2 — MOVEit / CL0P 2023
    doc.add_heading('Caso 2 — MOVEit / CL0P (vulnerabilidad sin parchar)', level=2)
    p = doc.add_paragraph()
    p.add_run('Qué pasó: ').bold = True
    p.add_run('el grupo de ransomware CL0P explotó una vulnerabilidad de inyección SQL '
              '(CVE-2023-34362) en software de transferencia de archivos, comprometiendo a más de '
              '2.700 organizaciones y ~93 millones de personas a nivel mundial.')
    p = doc.add_paragraph()
    p.add_run('Impacto de negocio: ').bold = True
    p.add_run('litigios masivos, acuerdos millonarios por organización (por ejemplo, un banco '
              'acordó USD 2.4 millones) y daño reputacional en cadena de proveedores.')
    p = doc.add_paragraph()
    p.add_run('Mejor práctica incumplida: ').bold = True
    p.add_run('Seguridad — gestión de vulnerabilidades y parches, protección de datos; mantener los '
              'servicios actualizados (Rendimiento/Operación).')
    doc.add_paragraph('Fuente: Wikipedia — https://en.wikipedia.org/wiki/2023_MOVEit_data_breach')
    doc.add_paragraph('Fuente: American Banker — https://www.americanbanker.com/news/nebraska-bank-to-settle-moveit-data-breach-for-2-4m')
    doc.add_paragraph()

    # Ancla de costo IBM 2024
    doc.add_heading('Referencia de costo global', level=2)
    p = doc.add_paragraph()
    p.add_run('El costo promedio mundial de una brecha de datos alcanzó USD 4.88 millones (máximo '
              'histórico), y ~USD 6.08 millones en el sector financiero.')
    doc.add_paragraph('Fuente: IBM Cost of a Data Breach 2024 — https://www.ibm.com/reports/data-breach')
    doc.add_paragraph()

    # Contexto Colombia / LatAm
    doc.add_heading('Contexto Colombia y Latinoamérica', level=2)
    p = doc.add_paragraph(style='List Bullet')
    p.add_run('En Colombia, 73% de las empresas sufrió al menos un incidente de seguridad '
              'significativo (frente a 61% el año anterior).')
    p = doc.add_paragraph(style='List Bullet')
    p.add_run('La SIC puede imponer multas de hasta ~COP 2.320 millones (2.000 SMMLV) y suspensión '
              'de actividades por incumplir la protección de datos personales (Ley 1581).')
    p = doc.add_paragraph(style='List Bullet')
    p.add_run('Hasta ~60% de las pymes que sufren un ciberataque grave cierra en menos de 6 meses.')
    doc.add_paragraph('Fuente: Informe de Ciberseguridad Colombia — https://star-ti.com/informe-ciberseguridad-colombia-2026/')
    doc.add_paragraph('Fuente: BDO Colombia — https://www.bdo.com.co/es-co/publicaciones/boletines-advisory/implicaciones-del-incumplimiento-de-las-normas-de-proteccion-de-datos-en-colombia')
    doc.add_paragraph('Fuente: Cybersecurity News — https://cybersecuritynews.es/el-60-de-las-pymes-que-sufren-un-ciberataque-grave-se-ve-obligada-a-cerrar-en-menos-de-seis-meses/')

    doc.add_page_break()


def add_conclusions(doc, evaluation_data, selected_pilares):
    """Add conclusions and recommendations section"""
    
    _color_heading(doc.add_heading('Conclusiones y Recomendaciones', level=1), GF_ORANGE)
    
    pillar_scores = evaluation_data.get('pillarScores', {})
    
    scores = [pillar_scores.get(p, 0) for p in selected_pilares]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    doc.add_paragraph(
        f'La evaluación Well-Architected ha identificado el estado actual de la arquitectura '
        f'con un score promedio de {round(avg_score, 1)}/100 en los pilares evaluados.'
    )
    
    doc.add_paragraph()
    
    doc.add_heading('Recomendaciones Prioritarias', level=2)
    
    if scores:
        min_score = min(scores)
        min_pilar = selected_pilares[scores.index(min_score)]
        
        doc.add_paragraph(
            f'1. Priorizar remediaciones en el pilar de {PILLAR_NAMES.get(min_pilar, min_pilar)} '
            f'(score: {min_score}/100), ya que presenta el mayor número de oportunidades de mejora.'
        )
    
    doc.add_paragraph(
        '2. Establecer un plan de remediación con plazos definidos para cada hallazgo identificado.'
    )
    
    doc.add_paragraph(
        '3. Implementar revisiones periódicas (trimestrales) para monitorear el progreso y '
        'mantener la arquitectura alineada con las mejores prácticas.'
    )
    
    doc.add_paragraph(
        '4. Considerar la implementación de automatización para mantener el cumplimiento continuo '
        'de las mejores prácticas.'
    )
    
    doc.add_paragraph()
    
    doc.add_heading('Próximos Pasos', level=2)
    
    doc.add_paragraph(
        '• Revisar el reporte técnico detallado para obtener información específica sobre cada hallazgo'
    )
    
    doc.add_paragraph(
        '• Asignar responsables y plazos para cada remediación prioritaria'
    )
    
    doc.add_paragraph(
        '• Establecer métricas de seguimiento para medir el progreso'
    )
    
    doc.add_paragraph(
        '• Programar la próxima evaluación Well-Architected'
    )
