"""Regenerate the submission PDF from SUBMISSION.md; requires reportlab."""
from pathlib import Path
import re
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'output/pdf/Alpenrecht_Submission_Report.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleR', fontName='Helvetica-Bold', fontSize=30, leading=34, textColor=colors.HexColor('#153D40'), spaceAfter=14))
styles.add(ParagraphStyle(name='BodyR', fontName='Helvetica', fontSize=10, leading=14, spaceAfter=8))
styles.add(ParagraphStyle(name='HeadR', fontName='Helvetica-Bold', fontSize=15, leading=19, textColor=colors.HexColor('#153D40'), spaceBefore=10, spaceAfter=9))
styles.add(ParagraphStyle(name='BulletR', parent=styles['BodyR'], leftIndent=11, firstLineIndent=-8, spaceAfter=6))

def rich(text):
    text = escape(text).replace('\u2014', '-').replace('\u2013', '-').replace('\u2011', '-')
    return re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)

story = [Paragraph('Alpenrecht AI', styles['TitleR']), Paragraph('Hack Apertus 2026 | Track 2B | 16 October 2026', styles['BodyR']), Paragraph('One legal question. Three levels of Swiss law.', styles['HeadR'])]
for block in (ROOT / 'SUBMISSION.md').read_text(encoding='utf-8-sig').split('\n\n'):
    block = block.strip()
    if not block:
        continue
    if block.startswith('<!-- PAGE -->'):
        story.append(PageBreak())
    elif block.startswith('## '):
        story.append(Paragraph(rich(block[3:]), styles['HeadR']))
    elif block.startswith('- '):
        for line in block.splitlines():
            story.append(Paragraph('&#8226; ' + rich(line.removeprefix('- ')), styles['BulletR']))
    else:
        story.append(Paragraph(rich(block.replace('\n', ' ')), styles['BodyR']))

def footer(canvas, doc):
    canvas.setStrokeColor(colors.HexColor('#2F8A7A'))
    canvas.line(44, 42, A4[0]-44, 42)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#536568'))
    canvas.drawString(44, 29, 'ALPENRECHT AI | HACK APERTUS 2026 | TRACK 2B')
    canvas.drawRightString(A4[0]-44, 29, str(doc.page))

SimpleDocTemplate(str(OUT), pagesize=A4, rightMargin=44, leftMargin=44, topMargin=36, bottomMargin=58, title='Alpenrecht AI - Technical Submission Report', author='Alpenrecht project').build(story, onFirstPage=footer, onLaterPages=footer)
print(OUT)
