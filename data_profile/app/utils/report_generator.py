from io import BytesIO
from docx import Document
from docx.shared import Pt


def create_word_report(profile):

    doc = Document()

    title = doc.add_heading(
        "Sigmatic Data Profiling Report",
        level=1,
    )
    title.runs[0].font.size = Pt(24)

    doc.add_heading("Executive Summary", level=2)

    doc.add_paragraph(
        f"Row Count: {profile['row_count']:,}"
    )

    doc.add_paragraph(
        f"Column Count: {profile['column_count']}"
    )

    doc.add_paragraph(
        f"Duplicate Count: {profile['duplicate_count']}"
    )

    doc.add_paragraph(
        f"Quality Score: {profile['quality_score']} / 100"
    )

    doc.add_heading("Schema", level=2)

    table = doc.add_table(rows=1, cols=4)
    table.style = "Table Grid"

    hdr = table.rows[0].cells

    hdr[0].text = "Column"
    hdr[1].text = "Type"
    hdr[2].text = "Nullable"
    hdr[3].text = "Position"

    for row in profile["schema"]:

        cells = table.add_row().cells

        cells[0].text = str(row["column_name"])
        cells[1].text = str(row["data_type"])
        cells[2].text = str(row["is_nullable"])
        cells[3].text = str(row["ordinal_position"])

    doc.add_page_break()

    doc.add_heading("Null Percentages", level=2)

    table = doc.add_table(rows=1, cols=2)
    table.style = "Table Grid"

    hdr = table.rows[0].cells

    hdr[0].text = "Column"
    hdr[1].text = "Null %"

    for col, value in profile["null_percentages"].items():

        cells = table.add_row().cells

        cells[0].text = col
        cells[1].text = str(value)

    doc.add_heading("Cardinality", level=2)

    table = doc.add_table(rows=1, cols=2)
    table.style = "Table Grid"

    hdr = table.rows[0].cells

    hdr[0].text = "Column"
    hdr[1].text = "Unique Count"

    for col, value in profile["unique_counts"].items():

        cells = table.add_row().cells

        cells[0].text = col
        cells[1].text = str(value)

    doc.add_heading("Numeric Statistics", level=2)

    stats = profile["numeric_statistics"]

    if stats:

        table = doc.add_table(rows=1, cols=5)
        table.style = "Table Grid"

        hdr = table.rows[0].cells

        hdr[0].text = "Column"
        hdr[1].text = "Min"
        hdr[2].text = "Max"
        hdr[3].text = "Average"
        hdr[4].text = "Sum"

        for row in stats:

            cells = table.add_row().cells

            cells[0].text = str(row["column_name"])
            cells[1].text = str(row["min_value"])
            cells[2].text = str(row["max_value"])
            cells[3].text = str(row["avg_value"])
            cells[4].text = str(row["sum_value"])

    doc.add_page_break()

    doc.add_heading("Candidate Primary Keys", level=2)

    if profile.get("candidate_primary_keys"):
        doc.add_paragraph(", ".join(profile["candidate_primary_keys"]))
    else:
        doc.add_paragraph("No candidate primary keys identified.")

    doc.add_heading("Data Type Issues", level=2)

    data_type_issues = profile.get("data_type_issues", [])

    if data_type_issues:

        table = doc.add_table(rows=1, cols=2)
        table.style = "Table Grid"

        hdr = table.rows[0].cells

        hdr[0].text = "Column"
        hdr[1].text = "Issue"

        for issue in data_type_issues:

            cells = table.add_row().cells

            cells[0].text = str(issue.get("column_name", ""))
            cells[1].text = str(issue.get("issue", ""))

    else:
        doc.add_paragraph("No data type issues detected.")

    doc.add_heading("Quality Warnings", level=2)

    quality_warnings = profile.get("quality_warnings", [])

    if quality_warnings:

        table = doc.add_table(rows=1, cols=2)
        table.style = "Table Grid"

        hdr = table.rows[0].cells

        hdr[0].text = "Warning"
        hdr[1].text = "Details"

        for warning in quality_warnings:

            cells = table.add_row().cells

            cells[0].text = str(warning.get("warning_type", ""))
            cells[1].text = str(warning.get("details", ""))

    else:
        doc.add_paragraph("No quality warnings detected.")

    doc.add_heading("Recommendations", level=2)

    for recommendation in profile["recommendations"]:
        doc.add_paragraph(
            recommendation,
            style="List Bullet",
        )

    output = BytesIO()

    doc.save(output)

    output.seek(0)

    return output