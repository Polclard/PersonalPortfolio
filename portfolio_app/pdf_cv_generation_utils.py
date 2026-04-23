from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    PageTemplate,
    NextPageTemplate,
    Frame,
    FrameBreak,
    PageBreak,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib.utils import ImageReader
import math


# ──────────────────────────────────────────────────────────────────────────────
# MOCK DATA (replaces DB queries during standalone testing)
# ──────────────────────────────────────────────────────────────────────────────
class _Obj:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)

import datetime
_skills       = [_Obj(name=n) for n in ["Python","Django","REST APIs","PostgreSQL","Docker","Git","React","TypeScript"]]
_technologies = [_Obj(name=n) for n in ["AWS","Redis","Nginx","Linux","CI/CD","GraphQL"]]
_languages    = [_Obj(language_name=n) for n in ["Macedonian (Native)","English (C1)"]]
_work = [
    _Obj(title="Backend Developer",company="TechCorp",
         start_date=datetime.date(2022,6,1),end_date=None,is_current_working_place=True,
         description="Designed and maintained REST APIs serving 50k+ users. Led migration of monolith to microservices using Docker and Kubernetes, cutting deploy time by 40%."),
    _Obj(title="Junior Developer",company="StartupXYZ",
         start_date=datetime.date(2021,1,1),end_date=datetime.date(2022,5,31),is_current_working_place=False,
         description="Built full-stack features with Django + React. Integrated third-party payment APIs and improved test coverage from 30% to 85%."),
]
_projects = [
    _Obj(title="Portfolio & CV Builder",link="https://github.com/Polclard/cv-builder",
         description="A Django web app that lets users build professional CVs and export them as PDFs. Supports live preview, custom themes, and one-click PDF generation via ReportLab."),
    _Obj(title="Real-Time Chat App",link="https://github.com/Polclard/chat",
         description="WebSocket-based chat application with Django Channels, Redis pub/sub, and a React frontend. Supports rooms, DMs, and file sharing."),
]
_education = [
    _Obj(title="BSc Software Engineering & Information Systems",
         school="FINKI – Ss. Cyril and Methodius University",
         start_date=datetime.date(2018,9,1),end_date=datetime.date(2022,7,1)),
]


def generate_cv():
    buffer = BytesIO()

    # ══════════════════════════════════════════════════════════════════
    # LAYOUT
    # ══════════════════════════════════════════════════════════════════
    PAGE_W, PAGE_H = A4
    LM = 14 * mm        # left margin
    RM = 14 * mm        # right margin
    TM = 14 * mm
    BM = 14 * mm
    HEADER_H    = 42 * mm
    SIDEBAR_W   = 56 * mm
    GAP         =  6 * mm
    CONTENT_TOP = PAGE_H - HEADER_H

    MAIN_W = PAGE_W - LM - RM - SIDEBAR_W - GAP

    # ══════════════════════════════════════════════════════════════════
    # PALETTE  – deep navy + gold accent
    # ══════════════════════════════════════════════════════════════════
    NAVY        = colors.HexColor("#0D1B2A")
    NAVY_MID    = colors.HexColor("#1B2E45")
    GOLD        = colors.HexColor("#C9A84C")
    GOLD_LIGHT  = colors.HexColor("#F5E6C0")
    SIDEBAR_BG  = colors.HexColor("#F2F5F9")
    TEXT_DARK   = colors.HexColor("#1A1A2E")
    TEXT_MID    = colors.HexColor("#4A5568")
    TEXT_LIGHT  = colors.HexColor("#718096")
    BORDER_CLR  = colors.HexColor("#CBD5E0")
    WHITE       = colors.white

    # ══════════════════════════════════════════════════════════════════
    # DOCUMENT
    # ══════════════════════════════════════════════════════════════════
    doc = BaseDocTemplate(
        buffer, pagesize=A4,
        leftMargin=LM, rightMargin=RM,
        topMargin=TM, bottomMargin=BM,
        title="Alen Jangelov CV", author="Alen Jangelov",
    )

    sidebar_frame = Frame(
        LM, BM, SIDEBAR_W, CONTENT_TOP - BM,
        id="sidebar",
        leftPadding=8, rightPadding=8, topPadding=10, bottomPadding=0,
        showBoundary=0,
    )
    main_frame = Frame(
        LM + SIDEBAR_W + GAP, BM, MAIN_W, CONTENT_TOP - BM,
        id="main",
        leftPadding=6, rightPadding=6, topPadding=10, bottomPadding=0,
        showBoundary=0,
    )
    later_frame = Frame(
        LM + SIDEBAR_W + GAP, BM, MAIN_W, CONTENT_TOP - BM,
        id="later_main",
        leftPadding=6, rightPadding=6, topPadding=10, bottomPadding=0,
        showBoundary=0,
    )

    # ── canvas helpers ──────────────────────────────────────────────
    def _draw_header(c, is_first):
        c.saveState()
        # full-bleed header rectangle
        c.setFillColor(NAVY)
        c.rect(0, PAGE_H - HEADER_H, PAGE_W, HEADER_H, fill=1, stroke=0)

        # gold accent bar at very top
        c.setFillColor(GOLD)
        c.rect(0, PAGE_H - 3*mm, PAGE_W, 3*mm, fill=1, stroke=0)

        if is_first:
            # decorative circle watermark top-right
            c.setFillColor(NAVY_MID)
            cx, cy, r = PAGE_W - 18*mm, PAGE_H - 14*mm, 28*mm
            c.circle(cx, cy, r, fill=1, stroke=0)
            c.setFillColor(NAVY)
            c.circle(cx, cy, r - 5*mm, fill=1, stroke=0)

            # name
            c.setFillColor(WHITE)
            c.setFont("Helvetica-Bold", 26)
            c.drawString(LM + SIDEBAR_W + GAP, PAGE_H - 19*mm, "Alen Jangelov")

            # role
            c.setFillColor(GOLD)
            c.setFont("Helvetica", 11)
            c.drawString(LM + SIDEBAR_W + GAP, PAGE_H - 27*mm, "Software Engineering & Information Systems Graduate")

            # contact row
            c.setFillColor(colors.HexColor("#A0AEC0"))
            c.setFont("Helvetica", 8.5)
            contact = "alenjang2@gmail.com   |   github.com/Polclard   |   linkedin.com/in/alen-jangelov-7b4743271"
            c.drawString(LM + SIDEBAR_W + GAP, PAGE_H - 35*mm, contact)

            # gold underline below name area
            c.setStrokeColor(GOLD)
            c.setLineWidth(1.5)
            c.line(LM + SIDEBAR_W + GAP, PAGE_H - HEADER_H + 6*mm,
                   PAGE_W - RM, PAGE_H - HEADER_H + 6*mm)
        else:
            # continuation header – smaller
            c.setFillColor(NAVY)
            c.rect(0, PAGE_H - 14*mm, PAGE_W, 14*mm, fill=1, stroke=0)
            c.setFillColor(GOLD)
            c.rect(0, PAGE_H - 3*mm, PAGE_W, 3*mm, fill=1, stroke=0)
            c.setFillColor(WHITE)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(LM, PAGE_H - 10*mm, "Alen Jangelov")
            c.setFillColor(GOLD)
            c.setFont("Helvetica", 8)
            c.drawRightString(PAGE_W - RM, PAGE_H - 10*mm, "Software Engineer")

        c.restoreState()

    def _draw_sidebar_bg(c):
        c.saveState()
        # sidebar background
        c.setFillColor(SIDEBAR_BG)
        c.rect(LM - 2, BM, SIDEBAR_W + 4, CONTENT_TOP - BM, fill=1, stroke=0)
        # left gold accent strip
        c.setFillColor(GOLD)
        c.rect(LM - 2, BM, 3, CONTENT_TOP - BM, fill=1, stroke=0)
        c.restoreState()

    def draw_first_page(c, doc):
        _draw_sidebar_bg(c)
        _draw_header(c, is_first=True)

    def draw_later_pages(c, doc):
        c.saveState()
        c.setFillColor(WHITE)
        c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        c.restoreState()
        _draw_header(c, is_first=False)

    doc.addPageTemplates([
        PageTemplate(id="first_page",  frames=[sidebar_frame, main_frame], onPage=draw_first_page),
        PageTemplate(id="later_pages", frames=[later_frame],               onPage=draw_later_pages),
    ])

    # ══════════════════════════════════════════════════════════════════
    # STYLES
    # ══════════════════════════════════════════════════════════════════
    S = getSampleStyleSheet()

    def _add(name, **kw):
        S.add(ParagraphStyle(name=name, parent=S["Normal"], **kw))

    _add("SidebarSection",
         fontName="Helvetica-Bold", fontSize=8.5, leading=11,
         textColor=GOLD, spaceBefore=4, spaceAfter=5,
         letterSpacing=1.5)

    _add("SidebarBody",
         fontName="Helvetica", fontSize=8.8, leading=12.5,
         textColor=TEXT_DARK, alignment=TA_JUSTIFY, spaceAfter=2)

    _add("SidebarMuted",
         fontName="Helvetica", fontSize=8, leading=10,
         textColor=TEXT_LIGHT, spaceAfter=2)

    _add("TagLabel",
         fontName="Helvetica", fontSize=7.8, leading=9,
         textColor=NAVY, alignment=TA_CENTER)

    _add("MainSection",
         fontName="Helvetica-Bold", fontSize=11, leading=14,
         textColor=NAVY, spaceBefore=2, spaceAfter=5, letterSpacing=1.2)

    _add("JobTitle",
         fontName="Helvetica-Bold", fontSize=10.2, leading=13,
         textColor=TEXT_DARK, spaceAfter=1)

    _add("Company",
         fontName="Helvetica-Bold", fontSize=9, leading=11,
         textColor=TEXT_MID, spaceAfter=1)

    _add("DateRange",
         fontName="Helvetica", fontSize=8.2, leading=10,
         textColor=TEXT_LIGHT, spaceAfter=3)

    _add("CVBodyText",
         fontName="Helvetica", fontSize=9.2, leading=13.5,
         textColor=TEXT_MID, alignment=TA_JUSTIFY, spaceAfter=3)

    _add("BulletItem",
         fontName="Helvetica", fontSize=9.2, leading=13.5,
         textColor=TEXT_MID, leftIndent=10, spaceAfter=1)

    # ══════════════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════════════
    def section_title_main(text):
        """Gold-accented section title for main column."""
        title_row = [[Paragraph(text, S["MainSection"])]]
        t = Table(title_row, colWidths=[MAIN_W])
        t.setStyle(TableStyle([
            ("LINEBELOW", (0,0), (-1,-1), 1.2, GOLD),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("TOPPADDING", (0,0), (-1,-1), 0),
            ("LEFTPADDING", (0,0), (-1,-1), 0),
        ]))
        return [t, Spacer(1, 4)]

    def section_title_sidebar(text):
        items = []
        items.append(Paragraph(text.upper(), S["SidebarSection"]))
        t = Table([[""]], colWidths=[SIDEBAR_W - 16], rowHeights=[1])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), GOLD),
            ("BOX", (0,0), (-1,-1), 0, WHITE),
            ("TOPPADDING", (0,0), (-1,-1), 0),
            ("BOTTOMPADDING", (0,0), (-1,-1), 0),
        ]))
        items.append(t)
        items.append(Spacer(1, 5))
        return items

    def make_tag(text, w=24):
        cell = Paragraph(text, S["TagLabel"])
        t = Table([[cell]], colWidths=[w*mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), GOLD_LIGHT),
            ("BOX", (0,0), (-1,-1), 0.6, GOLD),
            ("LEFTPADDING", (0,0), (-1,-1), 5),
            ("RIGHTPADDING", (0,0), (-1,-1), 5),
            ("TOPPADDING", (0,0), (-1,-1), 3),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))
        return t

    def tag_grid(items, cols=2, w=24):
        if not items:
            return Paragraph("—", S["SidebarBody"])
        tags = [make_tag(i, w) for i in items if i]
        rows = []
        for i in range(0, len(tags), cols):
            row = tags[i:i+cols]
            while len(row) < cols:
                row.append("")
            rows.append(row)
        t = Table(rows, colWidths=[w*mm]*cols)
        t.setStyle(TableStyle([
            ("LEFTPADDING", (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 3),
            ("TOPPADDING", (0,0), (-1,-1), 2),
            ("BOTTOMPADDING", (0,0), (-1,-1), 2),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
        ]))
        return t

    def divider():
        t = Table([[""]], colWidths=[MAIN_W], rowHeights=[0.5])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), BORDER_CLR),
            ("BOX", (0,0), (-1,-1), 0, WHITE),
            ("TOPPADDING", (0,0), (-1,-1), 0),
            ("BOTTOMPADDING", (0,0), (-1,-1), 0),
        ]))
        return t

    def bullet(text):
        return Paragraph(f"<bullet>&bull;</bullet> {text}", S["BulletItem"])

    def safe_date(d):
        return d.strftime("%b %Y") if d else ""

    # ══════════════════════════════════════════════════════════════════
    # DATA  (use DB querysets; mock data used when running standalone)
    # ══════════════════════════════════════════════════════════════════
    try:
        from .models import Skill, WorkExperience, Project, Education, Languages, Technologies
        skills        = Skill.objects.all()
        technologies  = Technologies.objects.all()
        work_experience = WorkExperience.objects.all().order_by("-start_date")
        projects      = Project.objects.all()
        education     = Education.objects.all().order_by("-start_date")
        languages     = Languages.objects.all()
    except Exception:
        skills          = _skills
        technologies    = _technologies
        work_experience = _work
        projects        = _projects
        education       = _education
        languages       = _languages

    full_name   = "Alen Jangelov"
    title_str   = "Software Engineering and Information Systems Graduate"
    email       = "alenjang2@gmail.com"
    github      = "https://github.com/Polclard"
    linkedin    = "https://www.linkedin.com/in/alen-jangelov-7b4743271/"
    summary     = (
        "Graduate in Software Engineering & Information Systems from FINKI. "
        "Passionate about building efficient systems, elegant web applications, "
        "and data-driven solutions that solve real-world problems."
    )

    # ══════════════════════════════════════════════════════════════════
    # STORY
    # ══════════════════════════════════════════════════════════════════
    story = []

    # ── HEADER spacer (header drawn on canvas) ───────────────────────
    story.append(Spacer(1, 4 * mm))

    # ── SIDEBAR ──────────────────────────────────────────────────────
    # Profile
    for item in section_title_sidebar("Profile"):
        story.append(item)
    story.append(Paragraph(summary, S["SidebarBody"]))
    story.append(Spacer(1, 6))

    # Skills
    for item in section_title_sidebar("Skills"):
        story.append(item)
    story.append(tag_grid([s.name for s in skills], cols=2, w=22))
    story.append(Spacer(1, 6))

    # Technologies
    for item in section_title_sidebar("Technologies"):
        story.append(item)
    story.append(tag_grid([t.name for t in technologies], cols=2, w=22))
    story.append(Spacer(1, 6))

    # Languages
    for item in section_title_sidebar("Languages"):
        story.append(item)
    if languages:
        for lang in languages:
            story.append(Paragraph(f"• {lang.language_name}", S["SidebarBody"]))
    else:
        story.append(Paragraph("—", S["SidebarBody"]))

    # ── switch to right column ────────────────────────────────────────
    story.append(FrameBreak())
    story.append(NextPageTemplate("later_pages"))

    # ── WORK EXPERIENCE ──────────────────────────────────────────────
    story.extend(section_title_main("WORK EXPERIENCE"))

    if work_experience:
        for idx, job in enumerate(work_experience):
            end_date = ("Present" if job.is_current_working_place
                        else (job.end_date.strftime("%b %Y") if job.end_date else "Present"))
            start_date = job.start_date.strftime("%b %Y")

            # Title + date on same row
            title_cell = Paragraph(f"<b>{job.title}</b>", S["JobTitle"])
            date_style = ParagraphStyle("_d", parent=S["DateRange"], alignment=TA_RIGHT)
            date_cell  = Paragraph(f"{start_date} – {end_date}", date_style)
            row = Table([[title_cell, date_cell]], colWidths=[MAIN_W*0.65, MAIN_W*0.35])
            row.setStyle(TableStyle([
                ("VALIGN", (0,0), (-1,-1), "BOTTOM"),
                ("LEFTPADDING", (0,0), (-1,-1), 0),
                ("RIGHTPADDING", (0,0), (-1,-1), 0),
                ("TOPPADDING", (0,0), (-1,-1), 0),
                ("BOTTOMPADDING", (0,0), (-1,-1), 2),
            ]))
            story.append(row)

            # Company
            label = f"{job.company}"
            if job.is_current_working_place:
                label += '  <font color="#C9A84C"><b>● Current</b></font>'
            story.append(Paragraph(label, S["Company"]))
            story.append(Paragraph(job.description, S["CVBodyText"]))

            if idx != len(list(work_experience)) - 1:
                story.append(Spacer(1, 4))
                story.append(divider())
                story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("No work experience added yet.", S["CVBodyText"]))

    story.append(Spacer(1, 10))

    # ── PROJECTS ─────────────────────────────────────────────────────
    story.extend(section_title_main("PROJECTS"))

    if projects:
        for idx, project in enumerate(projects):
            story.append(Paragraph(f"<b>{project.title}</b>", S["JobTitle"]))
            if hasattr(project, "link") and project.link:
                link_style = ParagraphStyle("_l", parent=S["DateRange"],
                                            textColor=colors.HexColor("#4A90D9"))
                story.append(Paragraph(project.link, link_style))
            story.append(Paragraph(project.description, S["CVBodyText"]))
            if idx != len(list(projects)) - 1:
                story.append(Spacer(1, 4))
                story.append(divider())
                story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("No projects added yet.", S["CVBodyText"]))

    story.append(Spacer(1, 10))

    # ── EDUCATION ────────────────────────────────────────────────────
    story.extend(section_title_main("EDUCATION"))

    if education:
        for idx, edu in enumerate(education):
            start = safe_date(edu.start_date)
            end   = safe_date(edu.end_date) if getattr(edu, "end_date", None) else "Present"
            school_name = getattr(edu, "school", None) or getattr(edu, "institution", None) or ""
            title_name  = getattr(edu, "title", None) or getattr(edu, "degree", None) or "Education"

            title_cell = Paragraph(f"<b>{title_name}</b>", S["JobTitle"])
            date_style = ParagraphStyle("_d2", parent=S["DateRange"], alignment=TA_RIGHT)
            date_cell  = Paragraph(f"{start} – {end}", date_style)
            row = Table([[title_cell, date_cell]], colWidths=[MAIN_W*0.65, MAIN_W*0.35])
            row.setStyle(TableStyle([
                ("VALIGN", (0,0), (-1,-1), "BOTTOM"),
                ("LEFTPADDING", (0,0), (-1,-1), 0),
                ("RIGHTPADDING", (0,0), (-1,-1), 0),
                ("TOPPADDING", (0,0), (-1,-1), 0),
                ("BOTTOMPADDING", (0,0), (-1,-1), 2),
            ]))
            story.append(row)

            if school_name:
                story.append(Paragraph(school_name, S["Company"]))

            if idx != len(list(education)) - 1:
                story.append(Spacer(1, 4))
                story.append(divider())
                story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("No education added yet.", S["CVBodyText"]))

    # ── BUILD ─────────────────────────────────────────────────────────
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


if __name__ == "__main__":
    data = generate_cv()
    with open("/mnt/user-data/outputs/cv_alen_jangelov.pdf", "wb") as f:
        f.write(data)
    print("Done →", len(data), "bytes")