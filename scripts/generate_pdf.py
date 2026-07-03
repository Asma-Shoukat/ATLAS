import os
import sys

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

# Colors
NAVY = colors.HexColor("#0F172A")      # Dark Slate/Navy
GOLD = colors.HexColor("#B45309")      # Gold/Amber
CHARCOAL = colors.HexColor("#1E293B")  # Primary Text
LIGHT_GRAY = colors.HexColor("#F8FAFC")# Backgrounds
BORDER_GRAY = colors.HexColor("#E2E8F0")# Borders
SLATE_GRAY = colors.HexColor("#64748B") # Captions/Headers

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, page_count):
        self.saveState()
        
        # Header on later pages
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(NAVY)
            self.drawString(54, 745, "ATLAS: Adaptive Trustworthy Language-Augmented Search")
            self.setFont("Helvetica", 8)
            self.setFillColor(SLATE_GRAY)
            self.drawRightString(558, 745, "Multi-Turn Search Report")
            self.setStrokeColor(BORDER_GRAY)
            self.setLineWidth(0.75)
            self.line(54, 737, 558, 737)
            
        # Footer on all pages
        self.setFont("Helvetica", 8)
        self.setFillColor(SLATE_GRAY)
        self.drawString(54, 40, "Air University, Islamabad | Course: Information Retrieval (IR) | Session: June 2026")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 40, page_text)
        self.setStrokeColor(BORDER_GRAY)
        self.setLineWidth(0.75)
        self.line(54, 52, 558, 52)
        
        self.restoreState()

def build_pdf(filename="docs/ATLAS_Academic_Report.pdf"):
    # Target page width/height (Letter: 612 x 792)
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    styles.add(ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=NAVY,
        alignment=1, # Center
        spaceAfter=4
    ))
    
    styles.add(ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=GOLD,
        alignment=1,
        spaceAfter=12
    ))

    styles.add(ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=SLATE_GRAY,
        alignment=1,
        spaceAfter=12
    ))

    styles.add(ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=NAVY,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        'SubSectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12,
        textColor=GOLD,
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        'ReportBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9,
        leading=12.5,
        textColor=CHARCOAL,
        spaceAfter=4
    ))

    styles.add(ParagraphStyle(
        'ReportBodyBold',
        parent=styles['ReportBody'],
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        'ReportList',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12.5,
        textColor=CHARCOAL,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    ))
    
    styles.add(ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=10,
        textColor=colors.white,
        alignment=0
    ))
    
    styles.add(ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=CHARCOAL,
        alignment=0
    ))

    styles.add(ParagraphStyle(
        'TableCellBold',
        parent=styles['TableCell'],
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        'QueryLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=NAVY,
        leftIndent=8,
        spaceBefore=2,
        spaceAfter=1
    ))

    styles.add(ParagraphStyle(
        'QueryText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=11,
        textColor=CHARCOAL,
        leftIndent=16,
        spaceAfter=2
    ))

    styles.add(ParagraphStyle(
        'QueryOutput',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=CHARCOAL,
        leftIndent=16,
        spaceAfter=2
    ))

    story = []

    # Cover Header Block
    story.append(Spacer(1, 10))
    story.append(Paragraph("ATLAS: Adaptive Trustworthy Language-Augmented Search", styles['DocTitle']))
    story.append(Paragraph("Multi-Turn Conversational Search Evaluation Report", styles['DocSubtitle']))
    
    meta_text = (
        "<b>Department of Creative Technologies, Air University, Islamabad</b><br/>"
        "Course: Information Retrieval (IR) | Session: June 2026<br/>"
        "<b>Group Members:</b> Asma Shoukat (241418), Amna-tuz-Zahra (241382)"
    )
    story.append(Paragraph(meta_text, styles['DocMeta']))
    
    # Gold divider line
    line_table = Table([[""]], colWidths=[504], rowHeights=[2])
    line_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), GOLD),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(line_table)
    story.append(Spacer(1, 8))

    # ================================================================
    # 1. Problem Statement & Dataset (MERGED)
    # ================================================================
    story.append(Paragraph("1. Problem Statement &amp; Dataset", styles['SectionHeading']))
    p1_text = (
        "Traditional Retrieval-Augmented Generation (RAG) models suffer from significant performance degradation "
        "in multi-turn conversational search. ATLAS addresses three core operational issues: "
        "<b>(1) Contextual Pronoun Dependency &amp; Query Drift</b> \u2014 follow-up queries contain pronouns "
        "(<i>\"it\"</i>, <i>\"they\"</i>, <i>\"them\"</i>) that naive retrieval systems cannot resolve, while "
        "naively concatenating history causes vector drift; "
        "<b>(2) Hallucination Risk</b> \u2014 standard systems lack confidence filters and fabricate answers when "
        "evidence is insufficient; and "
        "<b>(3) Black-Box Opacity</b> \u2014 conventional neural pipelines provide no verifiable citations or audit trails."
    )
    story.append(Paragraph(p1_text, styles['ReportBody']))
    
    p1b_text = (
        "ATLAS was evaluated on the <b>IBM Research Mt-RAG (SemEval 2026)</b> conversational benchmark "
        "spanning <b>366,479 plaintext passages</b> across four domains:"
    )
    story.append(Paragraph(p1b_text, styles['ReportBody']))
    
    # Table data
    table_data = [
        [
            Paragraph("Domain", styles['TableHeader']),
            Paragraph("Document Source Type", styles['TableHeader']),
            Paragraph("Passages", styles['TableHeader'])
        ],
        [
            Paragraph("<b>Government (GOVT)</b>", styles['TableCell']),
            Paragraph("NASA Space Missions, FEMA Disaster Safety &amp; Public Policy", styles['TableCell']),
            Paragraph("49,607", styles['TableCell'])
        ],
        [
            Paragraph("<b>Finance (FIQA)</b>", styles['TableCell']),
            Paragraph("Financial News Analyst Reports &amp; Q&amp;A Forums", styles['TableCell']),
            Paragraph("61,022", styles['TableCell'])
        ],
        [
            Paragraph("<b>Cloud (CLOUD)</b>", styles['TableCell']),
            Paragraph("IBM Cloudant Technical Manuals &amp; Cloud Developer Docs", styles['TableCell']),
            Paragraph("72,442", styles['TableCell'])
        ],
        [
            Paragraph("<b>Wikipedia (CLAPNQ)</b>", styles['TableCell']),
            Paragraph("General Knowledge Factoid Q&amp;A &amp; World History", styles['TableCell']),
            Paragraph("183,408", styles['TableCell'])
        ],
        [
            Paragraph("<b>Total Corpus</b>", styles['TableCellBold']),
            Paragraph("<b>Multi-Domain Mt-RAG Database Pool</b>", styles['TableCellBold']),
            Paragraph("<b>366,479</b>", styles['TableCellBold'])
        ]
    ]
    
    data_table = Table(table_data, colWidths=[120, 264, 120])
    data_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [LIGHT_GRAY, colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_GRAY),
        ('BACKGROUND', (0,-1), (-1,-1), LIGHT_GRAY),
    ]))
    story.append(data_table)
    story.append(Spacer(1, 4))
    
    p1c_text = (
        "<b>Preprocessing:</b> Source documents are sentence-chunked via regex segmenters; dense 384-dimensional "
        "vectors are generated using <i>all-MiniLM-L6-v2</i> SentenceTransformers; a FAISS Inner Product (IP) index "
        "is compiled. For CPU efficiency, an active local index of ~1,091 passages (250 per domain + gold reference "
        "documents from tasks 10\u201360) is used, achieving 0.3s retrieval latency."
    )
    story.append(Paragraph(p1c_text, styles['ReportBody']))

    # ================================================================
    # 2. Methodology — 7-Pillar Pipeline
    # ================================================================
    story.append(Paragraph("2. Methodology \u2014 7-Pillar Pipeline", styles['SectionHeading']))
    
    story.append(Paragraph("Pillars 1 &amp; 2: Conversational Understanding &amp; Query Rewriting", styles['SubSectionHeading']))
    p2a_text = (
        "ATLAS maintains a <b>Dual-Channel Context Tracker</b>: (1) a <i>User Subjects Channel</i> extracting noun "
        "phrases from user inputs (filtering noise words, truncating to last 3 terms), and (2) a <i>Proper Nouns Channel</i> "
        "tracking capitalized terms across all turns. When a query contains general pronouns (<i>\"it\"</i>, <i>\"they\"</i>, "
        "<i>\"them\"</i>, <i>\"its\"</i>, <i>\"their\"</i>) or is very short (&lt;5 words), the system resolves the pronoun "
        "to the most recent subject (e.g., <i>\"What causes them?\"</i> \u2192 <i>\"What causes wildfires?\"</i>) or enriches "
        "short queries by appending context (e.g., <i>\"Which is more important?\"</i> \u2192 "
        "<i>\"Which is more important regarding Market Cap and NAV?\"</i>)."
    )
    story.append(Paragraph(p2a_text, styles['ReportBody']))

    story.append(Paragraph("Pillar 3: Dual-Channel Hybrid Retrieval", styles['SubSectionHeading']))
    p2b_text = (
        "ATLAS runs two parallel retrieval channels: <i>Lexical Search (BM25 Okapi)</i> evaluates term frequencies "
        "across the corpus and returns the top 50 keyword-matched hits; <i>Dense Vector Search (FAISS)</i> encodes the "
        "query into 384-D space and performs Inner Product search, returning the top 50 semantic matches."
    )
    story.append(Paragraph(p2b_text, styles['ReportBody']))

    story.append(Paragraph("Pillar 4: Reciprocal Rank Fusion (RRF)", styles['SubSectionHeading']))
    p2c_text = (
        "Candidates from both channels are merged using: <b>RRF_Score(d) = &sum;<sub>m</sub> 1/(60 + Rank<sub>m</sub>(d))</b>. "
        "Documents retrieved by both channels are marked <i>HYBRID</i>. The top 20 fused candidates are retained."
    )
    story.append(Paragraph(p2c_text, styles['ReportBody']))

    story.append(Paragraph("Pillar 5: Neural Cross-Encoder Reranking", styles['SubSectionHeading']))
    p2d_text = (
        "The top 10 candidates are reranked using <i>ms-marco-MiniLM-L-6-v2</i>, a Cross-Encoder that processes the "
        "query and document text jointly via full cross-attention, producing a logit confidence score (range: \u221210.0 to +10.0)."
    )
    story.append(Paragraph(p2d_text, styles['ReportBody']))

    story.append(Paragraph("Pillar 6: Anti-Hallucination Decision Agent", styles['SubSectionHeading']))
    p2e_text = (
        "Four safety gates verify evidence sufficiency: (1) <i>Domain-Calibrated Thresholds</i> \u2014 logit must exceed "
        "per-domain thresholds (CLOUD: \u22122.0, GOVT: \u22121.5, CLAPNQ: \u22122.0, FIQA: +2.0); "
        "(2) <i>Score-Gap Ambiguity</i> \u2014 if the gap between top two candidates is &lt;0.5 with logit &lt;0, the query is flagged; "
        "(3) <i>Semantic Overlap</i> \u2014 at least 2 content words must overlap (1 for \u22642-word queries); "
        "(4) <i>Named-Entity Consistency</i> \u2014 2+ missing capitalized entities trigger interception. "
        "Failure produces a safe fallback: <i>\"I'm sorry, but I cannot find sufficient evidence...\"</i>"
    )
    story.append(Paragraph(p2e_text, styles['ReportBody']))

    story.append(Paragraph("Pillar 7: Extractive Sliding-Window Sentence Scorer", styles['SubSectionHeading']))
    p2f_text = (
        "The approved passage is split into sentences, each scored by query-token overlap, and the contiguous 2\u20133 "
        "sentence window with the highest cumulative score (plus position bias toward earlier content) is extracted. "
        "This strictly extractive method guarantees zero generative hallucinations."
    )
    story.append(Paragraph(p2f_text, styles['ReportBody']))

    # System Workflow (compact text-based)
    story.append(Paragraph("System Workflow", styles['SubSectionHeading']))
    workflow_text = (
        "<b>User Query</b> \u2192 <b>Dual-Channel Tracker</b> \u2192 <b>Query Rewriter</b> \u2192 "
        "<b>BM25 + FAISS Retrieval</b> \u2192 <b>RRF Fusion</b> \u2192 <b>Cross-Encoder Reranking</b> \u2192 "
        "<b>Decision Agent Guards</b> \u2192 <i>(if passed)</i> \u2192 <b>Extractive Sentence Scorer</b> \u2192 "
        "<b>Output + Citations</b>"
    )
    story.append(Paragraph(workflow_text, styles['ReportBody']))

    # Page Break before results
    story.append(PageBreak())

    # ================================================================
    # 3. Evaluation Results
    # ================================================================
    story.append(Paragraph("3. Evaluation Results", styles['SectionHeading']))
    p3_intro = (
        "The ATLAS pipeline was stress-tested across domains. Results demonstrate accurate retrieval, "
        "pronoun resolution, short-query enrichment, and anti-hallucination interception:"
    )
    story.append(Paragraph(p3_intro, styles['ReportBody']))

    # Scenario A: Government
    story.append(Paragraph("Scenario A: Wildfire Follow-Up (GOVT Domain)", styles['SubSectionHeading']))
    story.append(Paragraph("<b>Turn 1:</b> \"Which state has more wildfires?\"", styles['QueryLabel']))
    story.append(Paragraph(
        "<b>Verdict:</b> APPROVED (Confidence: 3.847, threshold: \u22121.5). "
        "<b>Output:</b> California wildfire data from 'CAL FIRE' citing 4.2 million acres burned in 2020. "
        "<b>Citation:</b> <font face='Courier' size='7'>2806a7d8f0775d28-14422-16441</font>", styles['QueryOutput']))
    
    story.append(Paragraph("<b>Turn 2:</b> \"What causes them?\"", styles['QueryLabel']))
    story.append(Paragraph(
        "<b>Rewritten:</b> \"What causes wildfires?\" (pronoun \"them\" \u2192 \"wildfires\"). "
        "<b>Verdict:</b> APPROVED (3.363). "
        "<b>Output:</b> Lightning and human activities as primary causes, from 'Wildfire Hazard Mitigation'. "
        "<b>Citation:</b> <font face='Courier' size='7'>8bb77f30210c5f4b-277-2698</font>", styles['QueryOutput']))

    # Scenario B: Finance
    story.append(Paragraph("Scenario B: Market Cap vs NAV (FIQA Domain)", styles['SubSectionHeading']))
    story.append(Paragraph("<b>Turn 1:</b> \"What's the difference between Market Cap and NAV?\"", styles['QueryLabel']))
    story.append(Paragraph(
        "<b>Verdict:</b> APPROVED (7.431, threshold: 2.0). "
        "Retrieves definition of market capitalization vs. net asset value. "
        "<b>Citation:</b> <font face='Courier' size='7'>414940-0-474</font>", styles['QueryOutput']))
    
    story.append(Paragraph("<b>Turn 2:</b> \"Which is more important?\"", styles['QueryLabel']))
    story.append(Paragraph(
        "<b>Rewritten:</b> \"Which is more important regarding Market Cap and NAV?\" "
        "<b>Verdict:</b> APPROVED (4.652). Retrieves fund valuation comparison context.", styles['QueryOutput']))

    # Scenario C: Anti-Hallucination
    story.append(Paragraph("Scenario C: Out-of-Domain Interception", styles['SubSectionHeading']))
    story.append(Paragraph("<b>Query:</b> \"How do you bake a vanilla wedding cake with buttercream frosting?\" (GOVT)", styles['QueryLabel']))
    story.append(Paragraph(
        "<b>Verdict:</b> INTERCEPTED. Reranker score: \u221210.161 (below \u22121.5 threshold); "
        "score gap: 0.272 (ambiguous); 1 matching term (below 2-term minimum). "
        "Safe fallback message returned: <i>\"I'm sorry, but I cannot find sufficient evidence...\"</i>", styles['QueryOutput']))

    # Scenario D: Entity Guard
    story.append(Paragraph("Scenario D: Named-Entity Guard (FIQA)", styles['SubSectionHeading']))
    story.append(Paragraph("<b>Query:</b> \"What is the NAV of Apple?\"", styles['QueryLabel']))
    story.append(Paragraph(
        "<b>Verdict:</b> INTERCEPTED. Confidence: \u22120.856 (below +2.0 threshold). "
        "Named-entity \"Apple\" absent from retrieved passage (which discusses Amazon).", styles['QueryOutput']))

    # ================================================================
    # 4. Limitations & Individual Contribution (MERGED)
    # ================================================================
    story.append(Paragraph("4. Limitations &amp; Individual Contribution", styles['SectionHeading']))
    
    lim_text = (
        "<b>Limitations:</b> (1) <i>Extractive-Only Generation</i> \u2014 the sliding-window scorer cannot paraphrase or "
        "combine multiple documents; poorly structured source sentences may reduce readability. "
        "(2) <i>Short Context Window</i> \u2014 rapid topic shifts over 10+ turns may cause pronoun resolution to reference "
        "stale subjects. (3) <i>No Cross-Document Synthesis</i> \u2014 answers are drawn from a single passage; multi-document "
        "reasoning is unsupported. (4) <i>CPU Latency</i> \u2014 global-index retrieval (366,479 passages) requires GPU "
        "acceleration for real-time performance; CPU mode is optimized via active sub-indexing."
    )
    story.append(Paragraph(lim_text, styles['ReportBody']))

    story.append(Spacer(1, 4))

    story.append(Paragraph("Individual Contributions", styles['SubSectionHeading']))
    c_asma = (
        "<b>Asma Shoukat (241418):</b> Core backend search architecture \u2014 hybrid retrieval engine "
        "(BM25 + FAISS), Reciprocal Rank Fusion merger, Cross-Encoder neural reranker integration, "
        "and domain safety threshold calibration."
    )
    c_amna = (
        "<b>Amna-tuz-Zahra (241382):</b> Dialogue state tracking and UI development \u2014 dual-channel "
        "context tracker for coreference resolution, responsive glassmorphic web interface with live "
        "pipeline telemetry, and sliding-window sentence extractor for citation highlighting."
    )
    story.append(Paragraph(c_asma, styles['ReportBody']))
    story.append(Paragraph(c_amna, styles['ReportBody']))

    # Build the document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully generated: {filename}")

if __name__ == "__main__":
    build_pdf()
