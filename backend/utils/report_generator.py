"""
utils/report_generator.py — Enhanced PDF Report Generator for DeepScanX AI
Generates detailed clinical-grade PDF reports with embedded visualizations.
"""
import io
import base64
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image as RLImage, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from PIL import Image as PILImage


# ─── Color constants ──────────────────────────────────────────
BRAND_COLOR = colors.HexColor('#dc143c')
BRAND_DARK = colors.HexColor('#8b0000')
HEADER_BG = colors.HexColor('#dc143c')
LIGHT_BG = colors.HexColor('#fff5f5')
GRAY_TEXT = colors.HexColor('#888888')
DARK_TEXT = colors.HexColor('#222222')
BORDER_COLOR = colors.HexColor('#e0e0e0')


def _b64_to_rl_image(b64_str, max_width=14*cm, max_height=8*cm):
    """Convert a base64-encoded image string to a ReportLab Image."""
    if not b64_str:
        return None
    # Strip data URI prefix if present
    if ',' in b64_str:
        b64_str = b64_str.split(',', 1)[1]
    try:
        img_data = base64.b64decode(b64_str)
        buf = io.BytesIO(img_data)
        pil = PILImage.open(buf)
        
        # If the image is transparent (like the dark-mode prob plot), give it a dark background
        # so white text doesn't disappear on the white PDF page.
        if pil.mode in ('RGBA', 'LA') or (pil.mode == 'P' and 'transparency' in pil.info):
            bg = PILImage.new('RGBA', pil.size, (25, 25, 25, 255))
            bg.paste(pil, (0, 0), pil)
            pil = bg.convert('RGB')
            buf = io.BytesIO()
            pil.save(buf, format='PNG')
            buf.seek(0)
            
        w, h = pil.size
        aspect = w / h
        
        target_w = max_width
        target_h = target_w / aspect
        if target_h > max_height:
            target_h = max_height
            target_w = target_h * aspect
            
        buf.seek(0)
        return RLImage(buf, width=target_w, height=target_h)
    except Exception:
        return None


def generate_detailed_report(data: dict, module_name: str) -> bytes:
    """
    Build a comprehensive, styled PDF report.

    data keys:
        - predicted_class, confidence, cancer_status, filename
        - explanation_text
        - probabilities: [(class, prob), ...]
        - doctor_notes: str (optional)
        - patient_name, patient_age, patient_gender (optional)
        - ensemble_results: dict (optional)
        - gradcam_b64: base64 image string (optional)
        - prob_chart_b64: base64 image string (optional)
        - results_plot_b64: base64 image string (optional)
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
    )

    styles = getSampleStyleSheet()

    # ── Custom styles ──
    title_style = ParagraphStyle(
        'ReportTitle', parent=styles['Title'],
        fontSize=24, textColor=BRAND_COLOR,
        spaceAfter=4, alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    )
    subtitle_style = ParagraphStyle(
        'ReportSub', parent=styles['Normal'],
        fontSize=10, textColor=GRAY_TEXT,
        spaceAfter=12, alignment=TA_CENTER,
    )
    heading_style = ParagraphStyle(
        'ReportH2', parent=styles['Heading2'],
        fontSize=14, textColor=BRAND_COLOR,
        spaceBefore=16, spaceAfter=6,
        fontName='Helvetica-Bold',
    )
    subheading_style = ParagraphStyle(
        'ReportH3', parent=styles['Heading3'],
        fontSize=11, textColor=BRAND_DARK,
        spaceBefore=10, spaceAfter=4,
        fontName='Helvetica-Bold',
    )
    normal_style = ParagraphStyle(
        'ReportNormal', parent=styles['Normal'],
        fontSize=10, leading=15, spaceAfter=6,
        textColor=DARK_TEXT,
    )
    notes_style = ParagraphStyle(
        'DoctorNotes', parent=styles['Normal'],
        fontSize=10, leading=16, spaceAfter=6,
        textColor=DARK_TEXT,
        backColor=colors.HexColor('#fffbe6'),
        borderPadding=8,
        borderWidth=1, borderColor=colors.HexColor('#ffe0b2'),
    )
    disclaimer_style = ParagraphStyle(
        'Disclaimer', parent=styles['Normal'],
        fontSize=7.5, textColor=colors.HexColor('#999999'),
        alignment=TA_CENTER, spaceBefore=20,
    )
    right_style = ParagraphStyle(
        'RightAlign', parent=styles['Normal'],
        fontSize=9, textColor=GRAY_TEXT, alignment=TA_RIGHT,
    )

    story = []

    # ════════════════════════════════════════════
    # HEADER
    # ════════════════════════════════════════════
    story.append(Paragraph("DeepScanX AI", title_style))
    story.append(Paragraph(
        "AI Unified Radiology Assistant — Comprehensive Diagnostic Report", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_COLOR))
    story.append(Spacer(1, 8))

    # Report metadata row
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    report_id = datetime.datetime.utcnow().strftime("DSX-%Y%m%d-%H%M%S")
    meta_data = [
        [f"<b>Report ID:</b> {report_id}", f"<b>Module:</b> {module_name}", f"<b>Generated:</b> {now}"]
    ]
    meta_tbl = Table(meta_data, colWidths=[6*cm, 5.5*cm, 6*cm])
    meta_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('TEXTCOLOR', (0, 0), (-1, -1), DARK_TEXT),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 12))

    # ════════════════════════════════════════════
    # PATIENT INFORMATION (if available)
    # ════════════════════════════════════════════
    patient_name = data.get('patient_name')
    patient_age = data.get('patient_age')
    patient_gender = data.get('patient_gender')

    if any([patient_name, patient_age, patient_gender]):
        story.append(Paragraph("Patient Information", heading_style))
        patient_rows = [["Field", "Value"]]
        if patient_name:
            patient_rows.append(["Patient Name", patient_name])
        if patient_age:
            patient_rows.append(["Age", str(patient_age)])
        if patient_gender:
            patient_rows.append(["Gender", patient_gender])
        pt_tbl = Table(patient_rows, colWidths=[6*cm, 11.5*cm])
        pt_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BRAND_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_BG, colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(pt_tbl)
        story.append(Spacer(1, 10))

    # ════════════════════════════════════════════
    # PREDICTION SUMMARY
    # ════════════════════════════════════════════
    story.append(Paragraph("Prediction Summary", heading_style))

    predicted_class = (
        data.get("predicted_class") or
        data.get("pred_class") or "N/A"
    )
    confidence_raw = data.get("confidence", "N/A")
    try:
        conf_val = float(confidence_raw)
        conf_display = f"{conf_val * 100:.2f}%" if conf_val <= 1 else f"{conf_val:.2f}%"
    except (ValueError, TypeError):
        conf_display = str(confidence_raw)

    cancer_status = data.get("cancer_status") or data.get("status", "N/A")
    filename = data.get("filename", "N/A")

    summary_data = [
        ["Field", "Value"],
        ["File Name", filename],
        ["Predicted Class", predicted_class],
        ["Diagnosis Status", cancer_status],
        ["Model Confidence", conf_display],
    ]

    s_tbl = Table(summary_data, colWidths=[6*cm, 11.5*cm])
    s_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_BG, colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(s_tbl)
    story.append(Spacer(1, 10))

    # ════════════════════════════════════════════
    # PROBABILITY BREAKDOWN
    # ════════════════════════════════════════════
    probabilities = data.get("probabilities")
    if probabilities:
        story.append(Paragraph("Class Probability Breakdown", heading_style))
        prob_rows = [["Class", "Probability", "Bar"]]
        for cls, prob in probabilities:
            percent = f"{float(prob) * 100:.2f}%"
            bar_width = int(float(prob) * 20)
            bar = "█" * bar_width + "░" * (20 - bar_width)
            prob_rows.append([cls, percent, bar])
        prob_tbl = Table(prob_rows, colWidths=[7*cm, 4*cm, 6.5*cm])
        prob_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BRAND_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_BG, colors.white]),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('FONTNAME', (2, 1), (2, -1), 'Courier'),
        ]))
        story.append(prob_tbl)
        story.append(Spacer(1, 10))

    # ════════════════════════════════════════════
    # PROBABILITY CHART IMAGE (if available)
    # ════════════════════════════════════════════
    prob_chart = data.get('prob_chart_b64') or data.get('prob_plot')
    if prob_chart:
        story.append(Paragraph("Probability Distribution Chart", heading_style))
        img = _b64_to_rl_image(prob_chart, max_width=15*cm, max_height=8*cm)
        if img:
            story.append(img)
            story.append(Spacer(1, 10))

    # ════════════════════════════════════════════
    # GRAD-CAM VISUALIZATION (if available)
    # ════════════════════════════════════════════
    gradcam_img = data.get('gradcam_b64') or data.get('results_plot') or data.get('results_plot_b64')
    if gradcam_img:
        story.append(Paragraph("Grad-CAM Visualization", heading_style))
        story.append(Paragraph(
            "The heatmap below highlights regions the AI model focused on for its prediction. "
            "Red/warm areas indicate high importance regions.",
            normal_style
        ))
        img = _b64_to_rl_image(gradcam_img, max_width=16*cm, max_height=9*cm)
        if img:
            story.append(img)
            story.append(Spacer(1, 10))

    # ════════════════════════════════════════════
    # CLINICAL INTERPRETATION
    # ════════════════════════════════════════════
    explanation = data.get("explanation_text") or data.get("explanation") or ""
    if explanation:
        story.append(Paragraph("AI Clinical Interpretation", heading_style))
        explanation_clean = explanation.replace("**", "").replace("*", "")
        story.append(Paragraph(explanation_clean, normal_style))
        story.append(Spacer(1, 8))

    # ════════════════════════════════════════════
    # ENSEMBLE RESULTS (if available)
    # ════════════════════════════════════════════
    ensemble = data.get('ensemble_results')
    if ensemble:
        story.append(Paragraph("Model Ensemble Analysis", heading_style))
        story.append(Paragraph(
            f"<b>Ensemble Prediction:</b> {ensemble.get('ensemble_prediction', 'N/A')}<br/>"
            f"<b>Ensemble Confidence:</b> {ensemble.get('ensemble_confidence', 0)*100:.2f}%<br/>"
            f"<b>Model Agreement:</b> {ensemble.get('agreement_ratio', 0)*100:.0f}% "
            f"({ensemble.get('num_models', 0)} models)",
            normal_style
        ))
        story.append(Spacer(1, 6))

        # Individual model results
        indiv = ensemble.get('individual', [])
        if indiv:
            story.append(Paragraph("Individual Model Breakdown", subheading_style))
            ens_rows = [["Model Architecture", "Predicted Class", "Confidence"]]
            for r in indiv:
                ens_rows.append([
                    r.get('model', ''),
                    r.get('predicted_class', ''),
                    f"{r.get('confidence', 0)*100:.2f}%"
                ])
            ens_tbl = Table(ens_rows, colWidths=[6*cm, 6.5*cm, 5*cm])
            ens_tbl.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), BRAND_COLOR),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_BG, colors.white]),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(ens_tbl)
            story.append(Spacer(1, 10))

    # ════════════════════════════════════════════
    # DOCTOR'S NOTES (if available)
    # ════════════════════════════════════════════
    doctor_notes = data.get('doctor_notes', '').strip()
    if doctor_notes:
        story.append(Paragraph("Physician's Clinical Notes", heading_style))
        story.append(Paragraph(
            f"<i>Added by reviewing physician at {now}</i>",
            ParagraphStyle('NoteTime', parent=styles['Normal'], fontSize=8, textColor=GRAY_TEXT)
        ))
        story.append(Spacer(1, 4))
        # Wrap long notes
        for line in doctor_notes.split('\n'):
            line = line.strip()
            if line:
                story.append(Paragraph(line, notes_style))
        story.append(Spacer(1, 10))

    # ════════════════════════════════════════════
    # TECHNICAL DETAILS
    # ════════════════════════════════════════════
    story.append(Paragraph("Technical Details", heading_style))
    tech_data = [
        ["Parameter", "Value"],
        ["AI Platform", "DeepScanX AI v2.0"],
        ["Analysis Module", module_name],
        ["Base Architecture", "ResNet-18 / EfficientNet-B0 / DenseNet-121"],
        ["Input Resolution", "224 × 224 px"],
        ["Confidence Threshold", "65%"],
        ["Report Format", "PDF/A Compatible"],
    ]
    tech_tbl = Table(tech_data, colWidths=[6*cm, 11.5*cm])
    tech_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8f8f8'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(tech_tbl)
    story.append(Spacer(1, 12))

    # ════════════════════════════════════════════
    # DISCLAIMER
    # ════════════════════════════════════════════
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER_COLOR))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "⚠  IMPORTANT DISCLAIMER: This report is generated by an AI-powered diagnostic assistance "
        "system for research and educational purposes ONLY. It is NOT a clinical diagnosis and must "
        "NOT be used as the sole basis for medical decisions. All results MUST be validated and "
        "interpreted by a board-certified pathologist, radiologist, or appropriate medical specialist. "
        "The AI models used have inherent limitations and may produce false positives or negatives. "
        "Always consider the full clinical context when evaluating these results.",
        disclaimer_style
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f"© {datetime.datetime.utcnow().year} DeepScanX AI — AI Unified Radiology Assistant | "
        f"Report generated on {now}",
        ParagraphStyle('Footer', parent=styles['Normal'],
                       fontSize=7, textColor=colors.HexColor('#bbbbbb'),
                       alignment=TA_CENTER)
    ))

    doc.build(story)
    return buf.getvalue()
