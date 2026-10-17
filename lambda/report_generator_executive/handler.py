"""
Executive Report Generator Lambda
Generates business-oriented reports in DOCX format
"""

import json
import logging
import io
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from autowar_common.report_storage import upload_report, generate_signed_url

logger = logging.getLogger()
logger.setLevel(logging.INFO)


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
    
    # Executive summary
    add_executive_summary(doc, evaluation_data, selected_pilares)
    
    # Pillar analysis sections
    for pilar in selected_pilares:
        add_pilar_section(doc, evaluation_data, pilar)
    
    # Conclusions and recommendations
    add_conclusions(doc, evaluation_data, selected_pilares)
    
    # Save to bytes
    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    
    return output.read()


def add_title_page(doc, account_id, evaluation_timestamp, user_info=None):
    """Add title page"""
    
    # Title
    title = doc.add_heading('Reporte Ejecutivo', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    subtitle = doc.add_heading('AWS Well-Architected Review', level=2)
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
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
    metadata.add_run(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'))
    
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
    """Add executive summary section"""
    
    doc.add_heading('Resumen Ejecutivo', level=1)
    
    pillar_scores = evaluation_data.get('pillarScores', {})
    best_practices = evaluation_data.get('bestPractices', [])
    
    # Calculate overall metrics
    # Normalize pilar names for comparison
    selected_pilares_normalized = [p.replace('_', '').lower() for p in selected_pilares]
    filtered_bps = [
        bp for bp in best_practices 
        if bp.get('pilar', '').replace('_', '').lower() in selected_pilares_normalized
    ]
    total_bps = len(filtered_bps)
    non_compliant = sum(1 for bp in filtered_bps if bp.get('status') == 'NON_COMPLIANT')
    compliant = sum(1 for bp in filtered_bps if bp.get('status') == 'COMPLIANT')
    pending = sum(1 for bp in filtered_bps if bp.get('status') == 'PENDING_REVIEW')
    
    # Calculate overall score using same formula as evaluator
    score_map = {'COMPLIANT': 100.0, 'NON_COMPLIANT': 0.0, 'PENDING_REVIEW': 50.0}
    overall_score = round(sum(score_map.get(bp.get('status', ''), 0.0) for bp in filtered_bps) / total_bps, 1) if total_bps > 0 else 0
    
    # Overall assessment
    doc.add_paragraph(
        f'Este reporte presenta un análisis estratégico de la evaluación Well-Architected '
        f'realizada para la cuenta AWS {evaluation_data.get("metadata", {}).get("accountId", "N/A")}. '
        f'Se evaluaron {len(selected_pilares)} pilares con un total de {total_bps} mejores prácticas.'
    )
    
    doc.add_paragraph()
    
    # Key findings
    doc.add_heading('Hallazgos Clave', level=2)
    
    findings_para = doc.add_paragraph()
    findings_para.add_run(f'• Score Global: ').bold = True
    findings_para.add_run(f'{overall_score}%')
    
    findings_para = doc.add_paragraph()
    findings_para.add_run(f'• Prácticas Conformes: ').bold = True
    findings_para.add_run(f'{compliant} de {total_bps} ({round(compliant/total_bps*100, 1) if total_bps > 0 else 0}%)')
    
    findings_para = doc.add_paragraph()
    findings_para.add_run(f'• Prácticas No Conformes: ').bold = True
    findings_para.add_run(f'{non_compliant} de {total_bps} ({round(non_compliant/total_bps*100, 1) if total_bps > 0 else 0}%)')
    
    findings_para = doc.add_paragraph()
    findings_para.add_run(f'• Prácticas Pendientes de Revisión: ').bold = True
    findings_para.add_run(f'{pending} de {total_bps} ({round(pending/total_bps*100, 1) if total_bps > 0 else 0}%)')
    
    doc.add_paragraph()
    
    # Pillar scores
    doc.add_heading('Scores por Pilar', level=2)
    
    pillar_names = {
        'security': 'Seguridad',
        'reliability': 'Fiabilidad',
        'performance': 'Rendimiento',
        'cost': 'Optimización de Costos',
        'operationalExcellence': 'Excelencia Operacional',
        'sustainability': 'Sostenibilidad'
    }
    
    for pilar in selected_pilares:
        score = pillar_scores.get(pilar, 0)
        score_para = doc.add_paragraph()
        score_para.add_run(f'• {pillar_names.get(pilar, pilar)}: ').bold = True
        score_para.add_run(f'{score}/100')
        
        # Add assessment
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
    
    pillar_names = {
        'security': 'Seguridad',
        'reliability': 'Fiabilidad',
        'performance': 'Rendimiento',
        'cost': 'Optimización de Costos',
        'operationalExcellence': 'Excelencia Operacional',
        'sustainability': 'Sostenibilidad'
    }
    
    pillar_descriptions = {
        'security': 'La seguridad es fundamental para proteger la información, sistemas y activos de su organización.',
        'reliability': 'La Fiabilidad asegura que su carga de trabajo funcione correctamente y de manera consistente.',
        'performance': 'El rendimiento eficiente permite utilizar los recursos de manera óptima.',
        'cost': 'La optimización de costos permite ejecutar sistemas para entregar valor de negocio al menor precio.',
        'operationalExcellence': 'La excelencia operacional permite ejecutar y monitorear sistemas para entregar valor de negocio.',
        'sustainability': 'La sostenibilidad minimiza los impactos ambientales de ejecutar cargas de trabajo en la nube.'
    }
    
    doc.add_heading(f'Análisis: {pillar_names.get(pilar, pilar)}', level=1)
    
    # Description
    doc.add_paragraph(pillar_descriptions.get(pilar, ''))
    doc.add_paragraph()
    
    # Score
    pillar_scores = evaluation_data.get('pillarScores', {})
    score = pillar_scores.get(pilar, 0)
    
    score_para = doc.add_paragraph()
    score_para.add_run('Score del Pilar: ').bold = True
    score_para.add_run(f'{score}/100')
    
    doc.add_paragraph()
    
    # Key findings for this pilar
    doc.add_heading('Hallazgos Principales', level=2)
    
    best_practices = evaluation_data.get('bestPractices', [])
    # Normalize pilar name for comparison
    pilar_normalized = pilar.replace('_', '').lower()
    pilar_bps = [
        bp for bp in best_practices 
        if bp.get('pilar', '').replace('_', '').lower() == pilar_normalized
    ]
    
    # Count by status
    non_compliant_bps = [bp for bp in pilar_bps if bp.get('status') == 'NON_COMPLIANT']
    
    if non_compliant_bps:
        doc.add_paragraph(f'Se identificaron {len(non_compliant_bps)} áreas que requieren atención:')
        
        # Show top 5 non-compliant items
        for bp in non_compliant_bps[:5]:
            bp_para = doc.add_paragraph(style='List Bullet')
            bp_para.add_run(f'{bp.get("bpId", "")}: ').bold = True
            bp_para.add_run(bp.get('finding', ''))
    else:
        doc.add_paragraph('Este pilar cumple con todas las mejores prácticas evaluadas.')
    
    doc.add_paragraph()
    
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


def add_conclusions(doc, evaluation_data, selected_pilares):
    """Add conclusions and recommendations section"""
    
    doc.add_heading('Conclusiones y Recomendaciones', level=1)
    
    pillar_scores = evaluation_data.get('pillarScores', {})
    
    # Calculate average score
    scores = [pillar_scores.get(p, 0) for p in selected_pilares]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    doc.add_paragraph(
        f'La evaluación Well-Architected ha identificado el estado actual de la arquitectura '
        f'con un score promedio de {round(avg_score, 1)}/100 en los pilares evaluados.'
    )
    
    doc.add_paragraph()
    
    # Priority recommendations
    doc.add_heading('Recomendaciones Prioritarias', level=2)
    
    # Find pillar with lowest score
    if scores:
        min_score = min(scores)
        min_pilar = selected_pilares[scores.index(min_score)]
        
        pillar_names = {
            'security': 'Seguridad',
            'reliability': 'Fiabilidad',
            'performance': 'Rendimiento',
            'cost': 'Optimización de Costos',
            'operationalExcellence': 'Excelencia Operacional',
            'sustainability': 'Sostenibilidad'
        }
        
        doc.add_paragraph(
            f'1. Priorizar remediaciones en el pilar de {pillar_names.get(min_pilar, min_pilar)} '
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
    
    # Next steps
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
