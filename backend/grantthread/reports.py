"""PDF/export rendering from frozen confirmed report projections only."""
import io
import json
from xml.sax.saxutils import escape


def money(value, currency="EUR"):
    return f"{currency} {value // 100:,}.{value % 100:02d}"


def manifest(report, attachments=None):
    return {"synthetic": True, "reportId": report["id"], "grantId": report["grantId"], "grantName": report["grantName"],
            "reportVersion": report["version"], "template": report["template"], "templateVersion": report.get("templateVersion", 1),
            "currency": report["currency"], "allocatedMinor": report["allocatedMinor"],
            "sources": report.get("sourceRefs", []), "attachments": attachments if attachments is not None else report.get("availableAttachments", []),
            "factsOrigin": "Confirmed records and exact calculations. Source existence does not prove interpretation."}


def pdf_bytes(report):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_RIGHT
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether

    output = io.BytesIO()
    document = SimpleDocTemplate(output, pagesize=(210 * mm, 297 * mm), rightMargin=18 * mm, leftMargin=18 * mm,
                                 topMargin=18 * mm, bottomMargin=20 * mm, title=report["grantName"] + " report", author="GrantThread")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Brand", fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=colors.HexColor("#172D35"), spaceAfter=10))
    styles.add(ParagraphStyle(name="Copy", fontName="Helvetica", fontSize=10, leading=15, textColor=colors.HexColor("#172D35"), spaceAfter=8))
    styles.add(ParagraphStyle(name="Meta", fontName="Helvetica", fontSize=8, leading=12, textColor=colors.HexColor("#637680"), spaceAfter=6))
    styles.add(ParagraphStyle(name="Section", fontName="Helvetica-Bold", fontSize=13, leading=18, textColor=colors.HexColor("#0A7C78"), spaceBefore=14, spaceAfter=7))
    paragraph = lambda value, style="Copy": Paragraph(escape(str(value)), styles[style])
    story = [paragraph("GrantThread", "Brand"), paragraph("SYNTHETIC DEMONSTRATION DATA • FICTIONAL ORGANISATIONS", "Meta"),
             paragraph(report["grantName"], "Heading1"), paragraph(f"{report['granteeName']}  |  {report['funderName']}", "Copy"),
             paragraph(f"Report version {report['version']}  •  Template {report['template']} v{report.get('templateVersion', 1)}", "Meta")]
    if report.get("status") == "incomplete":
        story += [paragraph("DRAFT — requirements still need attention", "Section"),
                  paragraph("; ".join(report.get("readiness", {}).get("missing", [])))]
    if report.get("status") == "stale":
        story += [paragraph("EARLIER DRAFT — source records changed", "Section"),
                  paragraph("This export preserves an earlier report version. Prepare a new version before sharing.")]
    story += [paragraph(report["narrative"]), paragraph("Confirmed figures", "Section")]
    summary = [["Awarded budget", money(report["awardMinor"])], ["Allocated expenses", money(report["allocatedMinor"])], ["Confirmed receipts", "Not provided"]]
    table = Table(summary, colWidths=[105 * mm, 65 * mm])
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F6F7F4")), ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                               ("FONTSIZE", (0, 0), (-1, -1), 10), ("PADDING", (0, 0), (-1, -1), 10), ("ALIGN", (1, 0), (1, -1), "RIGHT")]))
    story += [table]

    def activities():
        parts = [paragraph("Activities and outcomes", "Section")]
        if not report["activities"]:
            parts.append(paragraph("No confirmed activities provided."))
        for activity in report["activities"]:
            parts.append(paragraph(f"{activity['title']} • {activity['date']} • {activity['participants']} participants"))
        parts.append(paragraph("Activity-level participant counts are not a claim of unique people across grants. One shared workshop counts once in the organisation total.", "Meta"))
        return parts

    def expenses():
        parts = [paragraph("Expense allocations", "Section")]
        rows = [[paragraph("Expense"), paragraph("Date"), paragraph("Allocated")]]
        rows += [[paragraph(e["description"]), paragraph(e["date"]), paragraph(money(e["amountMinor"]))] for e in report["expenses"]]
        if not report["expenses"]:
            parts.append(paragraph("No confirmed expense allocations provided."))
        else:
            table = Table(rows, colWidths=[86 * mm, 36 * mm, 48 * mm], repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E9F3F1")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                       ("BOTTOMPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 7),
                                       ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#D9E1DE"))]))
            parts.append(table)
        parts.append(paragraph("Allocation, payment status and report evidence status are separate. Missing payment dates are not inferred.", "Meta"))
        return parts

    if report["template"] == "northstar-outcomes":
        story += activities() + expenses()
    else:
        story += expenses() + activities()
    story.append(paragraph("Source manifest", "Section"))
    refs = report.get("sourceRefs", [])
    for ref in refs:
        story.append(paragraph(f"{ref['evidenceId']} • version {ref['version']} • page {ref['page']}", "Meta"))
    if not refs:
        story.append(paragraph("No source attachments selected for this copy.", "Meta"))
    story.append(paragraph("Sources are available only within the viewer's authorised workspace or selected sharing manifest. This report is not a compliance certification.", "Meta"))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#637680"))
        canvas.drawString(18 * mm, 11 * mm, "GrantThread | Synthetic demonstration data")
        canvas.drawRightString(192 * mm, 11 * mm, str(doc.page))
        canvas.restoreState()
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
