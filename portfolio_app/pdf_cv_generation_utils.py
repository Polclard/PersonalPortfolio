
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from .models import Skill, WorkExperience, Project, Education, Languages, Technologies

def generate_cv():
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="Alen Jangelov CV",
        author="Alen Jangelov",
    )

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="NameStyle",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#1f3c88"),
            alignment=TA_CENTER,
            spaceAfter=6,
        )
    )

    styles.add(
        ParagraphStyle(
            name="RoleStyle",
            parent=styles["Normal"],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#555555"),
            alignment=TA_CENTER,
            spaceAfter=12,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionTitle",
            parent=styles["Heading2"],
            fontSize=12,
            leading=14,
            textColor=colors.HexColor("#1f3c88"),
            spaceBefore=8,
            spaceAfter=6,
        )
    )

    styles.add(
        ParagraphStyle(
            name="BodySmall",
            parent=styles["Normal"],
            fontSize=10,
            leading=13,
            textColor=colors.black,
            alignment=TA_LEFT,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Muted",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#666666"),
        )
    )

    story = []

    skills = Skill.objects.all()
    technologies = Technologies.objects.all()
    work_experience = WorkExperience.objects.all().order_by("-start_date")
    projects = Project.objects.all()
    education = Education.objects.all().order_by("-start_date")
    languages = Languages.objects.all()

    full_name = "Alen Jangelov"
    title = "Software Engineering and Information Systems Graduate"
    email = "alenjang2@gmail.com"
    github = "https://github.com/Polclard"
    linkedin = "https://www.linkedin.com/in/alen-jangelov-7b4743271/"
    summary = (
        "Graduate in Software Engineering & Information Systems from FINKI."
        " Passionate about building efficient systems, elegant web applications,"
        " and data-driven solutions that solve real-world problems."
    )

    story.append(Paragraph(full_name, styles["NameStyle"]))
    story.append(Paragraph(title, styles["RoleStyle"]))
    story.append(
        Paragraph(
            f"{email} | {github} | {linkedin}",
            styles["RoleStyle"]
        )
    )
    story.append(Spacer(1, 8))

    story.append(Paragraph("Profile", styles["SectionTitle"]))
    story.append(Paragraph(summary, styles["BodySmall"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Skills", styles["SectionTitle"]))
    skills_text = ", ".join(skill.name for skill in skills) or "No skills added yet."
    story.append(Paragraph(skills_text, styles["BodySmall"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Technologies", styles["SectionTitle"]))
    technologies_text = ", ".join(technology.name for technology in technologies)
    story.append(Paragraph(technologies_text, styles["BodySmall"]))

    story.append(Paragraph("Work Experience", styles["SectionTitle"]))
    if work_experience:
        for job in work_experience:
            end_date = "Present" if job.is_current_working_place else (
                job.end_date.strftime("%b %Y") if job.end_date else "Present"
            )
            start_date = job.start_date.strftime("%b %Y")
            story.append(
                Paragraph(
                    f"<b>{job.title}</b> — {job.company} {'- <b>Current</b>' if job.is_current_working_place and job.is_current_working_place else ''}",
                    styles["BodySmall"]
                )
            )
            story.append(
                Paragraph(
                    f"{start_date} - {end_date}",
                    styles["Muted"]
                )
            )
            story.append(Paragraph(job.description, styles["BodySmall"]))
            story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("No work experience added yet.", styles["BodySmall"]))

    story.append(Paragraph("Projects", styles["SectionTitle"]))
    if projects:
        for project in projects:
            story.append(
                Paragraph(f"<b>{project.title}</b>", styles["BodySmall"])
            )
            if hasattr(project, "link") and project.link:
                story.append(Paragraph(project.link, styles["Muted"]))
            story.append(Paragraph(project.description, styles["BodySmall"]))
            story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("No projects added yet.", styles["BodySmall"]))

    story.append(Paragraph("Education", styles["SectionTitle"]))
    if education:
        for edu in education:
            start_date = edu.start_date.strftime("%b %Y") if edu.start_date else ""
            end_date = edu.end_date.strftime("%b %Y") if edu.end_date else "Present"

            school_name = getattr(edu, "school", None) or getattr(edu, "institution", None) or ""
            title_name = getattr(edu, "title", None) or getattr(edu, "degree", None) or "Education"

            story.append(
                Paragraph(f"<b>{title_name}</b>", styles["BodySmall"])
            )
            if school_name:
                story.append(Paragraph(school_name, styles["BodySmall"]))
            story.append(Paragraph(f"{start_date} - {end_date}", styles["Muted"]))
            story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("No education added yet.", styles["BodySmall"]))

    story.append(Paragraph("Languages", styles["SectionTitle"]))
    if languages:
        language_rows = [["Language"]]
        for language in languages:
            language_rows.append([language.language_name])

        table = Table(language_rows, colWidths=[70 * mm, 40 * mm])
        table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbe4ff")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1f3c88")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ])
        )
        story.append(table)
    else:
        story.append(Paragraph("No languages added yet.", styles["BodySmall"]))

    doc.build(story)

    pdf = buffer.getvalue()
    buffer.close()

    return pdf