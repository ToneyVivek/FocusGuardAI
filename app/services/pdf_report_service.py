"""
PDF Report Service for FocusGuard.

Generates PDF reports for employee productivity analytics using ReportLab.
"""
from datetime import datetime, date
from typing import Optional
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.platypus import PageBreak, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from sqlalchemy.orm import Session

from app.models.models import User
from app.analytics.services.analytics_service import (
    get_user_summary,
    get_user_category_breakdown,
    get_user_domain_breakdown,
    get_user_timeline,
)


class PageNumberCanvas(canvas.Canvas):
    """Custom canvas to add page numbers and footer."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages = []
    
    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()
    
    def save(self):
        page_count = len(self.pages)
        for page_num, page in enumerate(self.pages, start=1):
            self.__dict__.update(page)
            self.draw_footer(page_num, page_count)
            super().showPage()
        super().save()
    
    def draw_footer(self, page_num, page_count):
        """Draw professional footer with page numbers and timestamp."""
        self.saveState()
        
        # Draw horizontal line
        self.setStrokeColor(colors.HexColor('#1e40af'))
        self.setLineWidth(1)
        self.line(72, 36, self._pagesize[0] - 72, 36)
        
        # Footer text
        self.setFont('Helvetica', 8)
        self.setFillColor(colors.grey)
        
        # Left: FocusGuard Analytics
        self.drawString(72, 24, "FocusGuard Analytics")
        
        # Center: Confidential
        footer_text = "Confidential"
        text_width = self.stringWidth(footer_text, 'Helvetica', 8)
        self.drawCentredString(self._pagesize[0] / 2, 24, footer_text)
        
        # Right: Page X of Y
        page_text = f"Page {page_num} of {page_count}"
        page_width = self.stringWidth(page_text, 'Helvetica', 8)
        self.drawString(self._pagesize[0] - 72 - page_width, 24, page_text)
        
        # Generated timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        timestamp_width = self.stringWidth(timestamp, 'Helvetica', 8)
        self.drawString(self._pagesize[0] - 72 - timestamp_width, 14, timestamp)
        
        self.restoreState()


def generate_employee_report_pdf(
    db: Session,
    employee: User,
    start_date: date,
    end_date: date
) -> BytesIO:
    """
    Generate a professional PDF report for an employee's productivity analytics.
    
    Args:
        db: Database session
        employee: Employee user object
        start_date: Report start date
        end_date: Report end date
        
    Returns:
        BytesIO buffer containing the PDF
    """
    # Fetch analytics data (reuse existing analytics services)
    summary = get_user_summary(db, employee, start_date, end_date)
    categories = get_user_category_breakdown(db, employee, start_date, end_date)
    domains = get_user_domain_breakdown(db, employee, start_date, end_date)
    timeline = get_user_timeline(db, employee, start_date, end_date, limit=100)
    
    # Extract top category from existing category breakdown data
    topCategory = None
    if categories.categories:
        # Find category with highest duration
        topCategory = max(categories.categories, key=lambda c: c.duration_seconds).category
    
    # Extract most used website from existing domain breakdown data
    topDomain = None
    if domains.domains:
        # Find domain with highest duration
        topDomain = max(domains.domains, key=lambda d: d.duration_seconds).domain
    
    # Determine report type
    report_type = _get_report_type(start_date, end_date)
    
    # Create PDF buffer with landscape pages for charts
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=48,
        pageCanvas=PageNumberCanvas
    )
    
    # Create styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='ReportTitle',
        parent=styles['Heading1'],
        fontSize=32,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))
    styles.add(ParagraphStyle(
        name='ReportSubtitle',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#6b7280'),
        spaceAfter=24,
        alignment=TA_CENTER,
        fontName='Helvetica'
    ))
    styles.add(ParagraphStyle(
        name='SectionHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=10,
        fontName='Helvetica-Bold'
    ))
    styles.add(ParagraphStyle(
        name='CustomBodyText',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        fontName='Helvetica'
    ))
    styles.add(ParagraphStyle(
        name='CustomSmallText',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=4,
        fontName='Helvetica'
    ))
    styles.add(ParagraphStyle(
        name='CoverLabel',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#6b7280'),
        fontName='Helvetica-Bold',
        spaceAfter=2
    ))
    styles.add(ParagraphStyle(
        name='CoverValue',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.black,
        fontName='Helvetica',
        spaceAfter=12
    ))
    
    # Build content
    story = []
    
    # ==================== PAGE 1: HEADER + KPI CARDS + SUMMARY ====================
    
    # Centered Title
    story.append(Paragraph("FocusGuard Analytics", ParagraphStyle('TitleSubtitle', parent=styles['Normal'], fontSize=14, textColor=colors.HexColor('#6b7280'), alignment=TA_CENTER, fontName='Helvetica')))
    story.append(Spacer(1, 0.05 * inch))
    story.append(Paragraph("Employee Productivity Report", styles['ReportTitle']))
    story.append(Spacer(1, 0.25 * inch))
    
    # Horizontal separator
    story.append(Table([['']], colWidths=[6.5 * inch], style=TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#e5e7eb'))
    ])))
    story.append(Spacer(1, 0.2 * inch))
    
    # Employee Information (Compact key-value pairs)
    org_name = employee.organization.name if employee.organization else 'N/A'
    generated_time = datetime.now().strftime('%d %b %Y %I:%M %p')
    
    # Format date range
    if start_date == end_date:
        period_str = start_date.strftime('%d %b %Y')
    else:
        period_str = f"{start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}"
    
    employee_info_data = [
        ['Employee', employee.full_name],
        ['Email', employee.email],
        ['Organization', org_name],
    ]
    
    employee_table = Table(employee_info_data, colWidths=[1.5 * inch, 5 * inch])
    employee_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(employee_table)
    
    # Report info on same row
    report_info_data = [
        ['Report Type', report_type],
        ['Report Period', period_str],
        ['Generated On', generated_time],
    ]
    
    report_table = Table(report_info_data, colWidths=[1.5 * inch, 5 * inch])
    report_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(report_table)
    story.append(Spacer(1, 0.2 * inch))
    
    # Horizontal separator
    story.append(Table([['']], colWidths=[6.5 * inch], style=TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#e5e7eb'))
    ])))
    story.append(Spacer(1, 0.25 * inch))
    
    # Productivity Overview - Dashboard Style KPI Cards
    story.append(Paragraph("Productivity Overview", styles['SectionHeading']))
    story.append(Spacer(1, 0.15 * inch))
    
    # Calculate productivity percentage
    total_time = summary.metrics.productive_time + summary.metrics.idle_time
    productivity_percent = (summary.metrics.productive_time / total_time * 100) if total_time > 0 else 0
    
    # Create KPI cards - Compact 4x2 layout with equal size and light borders
    kpi_data = [
        ['Focus Score', f"{summary.focus_score.score:.1f}", colors.HexColor('#8b5cf6')],  # Purple
        ['Productive Time', _format_seconds(summary.metrics.productive_time), colors.HexColor('#10b981')],  # Green
        ['Idle Time', _format_seconds(summary.metrics.idle_time), colors.HexColor('#ef4444')],  # Red
        ['Active Time', _format_seconds(summary.focus_score.total_active_time), colors.HexColor('#3b82f6')],  # Blue
        ['Sessions', str(summary.metrics.completed_sessions), colors.HexColor('#f59e0b')],  # Orange
        ['Tab Switches', str(summary.metrics.activity_events), colors.HexColor('#eab308')],  # Yellow
        ['Productivity %', f"{productivity_percent:.1f}%", colors.HexColor('#10b981')],  # Green
        ['Top Category', (topCategory or 'N/A')[:15] + '...' if topCategory and len(topCategory) > 15 else (topCategory or 'N/A'), colors.HexColor('#3b82f6')],  # Blue (truncated if too long)
    ]
    
    # Create 4x2 grid of compact KPI cards with equal size
    grid_rows = []
    for i in range(0, len(kpi_data), 4):
        row_data = []
        for j in range(4):
            if i + j < len(kpi_data):
                label, value, color = kpi_data[i + j]
                card_data = [
                    [Paragraph(label, ParagraphStyle('KPILabel', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#6b7280'), fontName='Helvetica-Bold'))],
                    [Paragraph(value, ParagraphStyle('KPIValue', parent=styles['Normal'], fontSize=16, textColor=color, fontName='Helvetica-Bold'))],
                ]
                card_table = Table(card_data, colWidths=[1.4 * inch])
                card_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
                ]))
                row_data.append(card_table)
            else:
                row_data.append('')
        
        grid_rows.append(row_data)
    
    grid_table = Table(grid_rows, colWidths=[1.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
    grid_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(grid_table)
    story.append(Spacer(1, 0.25 * inch))
    
    # Summary Section with bullet points
    story.append(Table([['']], colWidths=[6.5 * inch], style=TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#e5e7eb'))
    ])))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Summary", styles['SectionHeading']))
    story.append(Spacer(1, 0.1 * inch))
    
    # Build summary bullet points
    summary_points = [
        f"• Total active time : {_format_seconds(summary.focus_score.total_active_time)}",
        f"• Productive work : {productivity_percent:.0f}%",
        f"• Most used website : {topDomain or 'N/A'}",
        f"• Top category : {topCategory or 'N/A'}",
    ]
    
    for point in summary_points:
        story.append(Paragraph(point, ParagraphStyle('SummaryPoint', parent=styles['Normal'], fontSize=10, fontName='Helvetica', leftIndent=20)))
    
    story.append(Spacer(1, 0.25 * inch))
    
    # ==================== PAGE 2: VISUAL ANALYTICS (Vertical Layout) ====================
    story.append(PageBreak())
    
    # Visual Analytics Header
    story.append(Paragraph("Visual Analytics", styles['SectionHeading']))
    story.append(Spacer(1, 0.15 * inch))
    
    # 1. Productivity Distribution (Pie Chart) - Full width
    story.append(Paragraph("Productivity Distribution", styles['CustomBodyText']))
    story.append(Spacer(1, 0.1 * inch))
    
    pie_chart = _create_productivity_pie_chart(summary)
    if pie_chart:
        story.append(pie_chart)
    else:
        story.append(Paragraph("No productivity data available", styles['CustomSmallText']))
    story.append(Spacer(1, 0.35 * inch))
    
    # 2. Category Breakdown (Horizontal Bar Chart) - Full width
    story.append(Paragraph("Time Spent by Category", styles['CustomBodyText']))
    story.append(Spacer(1, 0.1 * inch))
    
    category_chart = _create_category_bar_chart(categories)
    if category_chart:
        story.append(category_chart)
    else:
        story.append(Paragraph("No category data available", styles['CustomSmallText']))
    
    # ==================== PAGE 3: USAGE ANALYTICS (Vertical Layout) ====================
    story.append(PageBreak())
    
    # Usage Analytics Header
    story.append(Paragraph("Usage Analytics", styles['SectionHeading']))
    story.append(Spacer(1, 0.15 * inch))
    
    # 3. Top Websites (Horizontal Bar Chart) - Full width
    story.append(Paragraph("Top Websites", styles['CustomBodyText']))
    story.append(Spacer(1, 0.1 * inch))
    
    domain_chart = _create_domain_bar_chart(domains)
    if domain_chart:
        story.append(domain_chart)
    else:
        story.append(Paragraph("No website data available", styles['CustomSmallText']))
    story.append(Spacer(1, 0.35 * inch))
    
    # 4. Activity Trend (Line Chart) - Full width
    story.append(Paragraph("Activity Trend", styles['CustomBodyText']))
    story.append(Spacer(1, 0.1 * inch))
    
    trend_chart = _create_trend_chart(timeline, report_type)
    if trend_chart:
        story.append(trend_chart)
    else:
        story.append(Paragraph("No trend data available", styles['CustomSmallText']))
    
    # ==================== PAGE 4: CATEGORY INSIGHTS (Donut + Key Insights) ====================
    story.append(PageBreak())
    
    # Category Insights Header
    story.append(Paragraph("Category Insights", styles['SectionHeading']))
    story.append(Spacer(1, 0.15 * inch))
    
    # 5. Category Percentage (Donut Chart) - Full width
    story.append(Paragraph("Category Percentage", styles['CustomBodyText']))
    story.append(Spacer(1, 0.1 * inch))
    
    donut_chart = _create_category_donut_chart(categories)
    if donut_chart:
        story.append(donut_chart)
    else:
        story.append(Paragraph("No category percentage data available", styles['CustomSmallText']))
    story.append(Spacer(1, 0.35 * inch))
    
    # Key Insights Section
    story.append(Table([['']], colWidths=[6.5 * inch], style=TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.HexColor('#e5e7eb'))
    ])))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Key Insights", styles['SectionHeading']))
    story.append(Spacer(1, 0.1 * inch))
    
    # Build key insights bullet points
    insights_points = [
        f"• Focus Score : {summary.focus_score.score:.1f}",
        f"• Productivity : {productivity_percent:.0f}%",
        f"• Top Category : {topCategory or 'N/A'}",
        f"• Most Used Website : {topDomain or 'N/A'}",
    ]
    
    for point in insights_points:
        story.append(Paragraph(point, ParagraphStyle('SummaryPoint', parent=styles['Normal'], fontSize=10, fontName='Helvetica', leftIndent=20)))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


def _create_productivity_pie_chart(summary) -> Optional[Drawing]:
    """Create a pie chart showing productivity distribution with legend and percentages."""
    productive = summary.metrics.productive_time
    idle = summary.metrics.idle_time
    neutral = summary.metrics.neutral_time if hasattr(summary.metrics, 'neutral_time') else 0
    
    total = productive + idle + neutral
    if total == 0:
        return None
    
    drawing = Drawing(500, 220)
    pie = Pie()
    pie.x = 100
    pie.y = 40
    pie.width = 200
    pie.height = 200
    
    # Colors matching dashboard
    colors_list = [colors.HexColor('#10b981'), colors.HexColor('#ef4444'), colors.HexColor('#f59e0b')]
    
    if neutral > 0:
        data = [productive, idle, neutral]
        labels = ['Productive', 'Idle', 'Neutral']
    else:
        data = [productive, idle]
        labels = ['Productive', 'Idle']
    
    pie.data = data
    pie.slices[0].fillColor = colors_list[0]
    pie.slices[1].fillColor = colors_list[1]
    if len(data) > 2:
        pie.slices[2].fillColor = colors_list[2]
    
    drawing.add(pie)
    
    # Add legend with percentages
    legend_x = 330
    legend_y = 110
    for i, (label, value) in enumerate(zip(labels, data)):
        percent = (value / total * 100)
        legend_text = f"{label} {percent:.0f}%"
        
        # Color box
        from reportlab.graphics.shapes import Rect
        rect = Rect(legend_x, legend_y - i * 25, 10, 10, fillColor=colors_list[i], strokeColor=None)
        drawing.add(rect)
        
        # Label text
        from reportlab.graphics.shapes import String
        label_str = String(legend_x + 15, legend_y - i * 25 + 3, legend_text, fontSize=9, fontName='Helvetica', fillColor=colors.black)
        drawing.add(label_str)
    
    return drawing


def _create_category_bar_chart(categories) -> Optional[Drawing]:
    """Create a horizontal bar chart for category breakdown with proper axis labels, rounded values, and bar value labels."""
    if not categories.categories:
        return None
    
    drawing = Drawing(500, 220)
    chart = HorizontalBarChart()
    chart.x = 100
    chart.y = 40
    chart.width = 380
    chart.height = 150
    chart.valueAxis.valueMin = 0
    
    # Convert seconds to minutes and round to whole numbers
    max_minutes = round(max([c.duration_seconds / 60 for c in categories.categories[:5]])) or 1
    chart.valueAxis.valueMax = max_minutes
    chart.valueAxis.valueStep = max(max_minutes / 5, 1)
    
    chart.categoryAxis.categoryNames = [c.category for c in categories.categories[:5]]
    chart.data = [[round(c.duration_seconds / 60) for c in categories.categories[:5]]]
    chart.bars[0].fillColor = colors.HexColor('#3b82f6')
    chart.bars.strokeWidth = 0
    
    # Add labels and axes
    chart.valueAxis.labels.fontSize = 8
    chart.valueAxis.labels.fontName = 'Helvetica'
    chart.categoryAxis.labels.fontSize = 8
    chart.categoryAxis.labels.fontName = 'Helvetica'
    chart.categoryAxis.labels.boxAnchor = 'e'
    chart.categoryAxis.labels.dx = -5
    chart.categoryAxis.labels.dy = 0
    
    drawing.add(chart)
    
    # Add value labels at the end of each bar
    from reportlab.graphics.shapes import String
    bar_height = chart.height / len(categories.categories[:5])
    for i, category in enumerate(categories.categories[:5]):
        value = round(category.duration_seconds / 60)
        # Calculate position: chart.x + chart.width + padding, chart.y + (i * bar_height) + offset
        label_x = chart.x + chart.width + 5
        label_y = chart.y + (i * bar_height) + (bar_height / 2) - 3
        value_label = String(label_x, label_y, f"{value} min", fontSize=8, fontName='Helvetica', textAnchor='start')
        drawing.add(value_label)
    
    # Add axis label (moved to prevent overlap)
    y_axis_label = String(40, 115, "Category", fontSize=8, fontName='Helvetica', textAnchor='end')
    x_axis_label = String(490, 25, "Time (Minutes)", fontSize=8, fontName='Helvetica', textAnchor='end')
    drawing.add(y_axis_label)
    drawing.add(x_axis_label)
    
    return drawing


def _create_domain_bar_chart(domains) -> Optional[Drawing]:
    """Create a horizontal bar chart for top websites with proper axis labels, rounded values, and bar value labels."""
    if not domains.domains:
        return None
    
    drawing = Drawing(500, 220)
    chart = HorizontalBarChart()
    chart.x = 100
    chart.y = 40
    chart.width = 380
    chart.height = 150
    chart.valueAxis.valueMin = 0
    
    # Convert seconds to minutes and round to whole numbers
    max_minutes = round(max([d.duration_seconds / 60 for d in domains.domains[:5]])) or 1
    chart.valueAxis.valueMax = max_minutes
    chart.valueAxis.valueStep = max(max_minutes / 5, 1)
    
    chart.categoryAxis.categoryNames = [d.domain for d in domains.domains[:5]]
    chart.data = [[round(d.duration_seconds / 60) for d in domains.domains[:5]]]
    chart.bars[0].fillColor = colors.HexColor('#8b5cf6')
    chart.bars.strokeWidth = 0
    
    # Add labels and axes
    chart.valueAxis.labels.fontSize = 8
    chart.valueAxis.labels.fontName = 'Helvetica'
    chart.categoryAxis.labels.fontSize = 8
    chart.categoryAxis.labels.fontName = 'Helvetica'
    chart.categoryAxis.labels.boxAnchor = 'e'
    chart.categoryAxis.labels.dx = -5
    chart.categoryAxis.labels.dy = 0
    
    drawing.add(chart)
    
    # Add value labels at the end of each bar
    from reportlab.graphics.shapes import String
    bar_height = chart.height / len(domains.domains[:5])
    for i, domain in enumerate(domains.domains[:5]):
        value = round(domain.duration_seconds / 60)
        # Calculate position: chart.x + chart.width + padding, chart.y + (i * bar_height) + offset
        label_x = chart.x + chart.width + 5
        label_y = chart.y + (i * bar_height) + (bar_height / 2) - 3
        value_label = String(label_x, label_y, f"{value} min", fontSize=8, fontName='Helvetica', textAnchor='start')
        drawing.add(value_label)
    
    # Add axis label (moved to prevent overlap)
    y_axis_label = String(40, 115, "Website", fontSize=8, fontName='Helvetica', textAnchor='end')
    x_axis_label = String(490, 25, "Time (Minutes)", fontSize=8, fontName='Helvetica', textAnchor='end')
    drawing.add(y_axis_label)
    drawing.add(x_axis_label)
    
    return drawing


def _create_trend_chart(timeline, report_type: str) -> Optional[Drawing]:
    """Create a line chart for activity trend with readable values (no floating points)."""
    if not timeline.items:
        return None
    
    drawing = Drawing(500, 220)
    chart = HorizontalLineChart()
    chart.x = 60
    chart.y = 40
    chart.width = 420
    chart.height = 150
    chart.valueAxis.valueMin = 0
    
    # Group data based on report type with proper aggregation
    if report_type == 'Daily':
        # Hourly trend (all hours, not just work hours)
        hourly_data = {}
        for item in timeline.items:
            if item.start_time:
                hour = item.start_time.hour
                hourly_data[hour] = hourly_data.get(hour, 0) + item.duration_seconds
        
        hours = sorted(hourly_data.keys())
        if not hours:
            return None
        
        data = [hourly_data.get(h, 0) for h in hours]
        labels = [f"{h}" for h in hours]
        x_label = "Hour"
        y_label = "Focus Minutes"
    elif report_type == 'Weekly':
        # Daily trend
        daily_data = {}
        for item in timeline.items:
            if item.start_time:
                day = item.start_time.strftime('%a')
                daily_data[day] = daily_data.get(day, 0) + item.duration_seconds
        
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        data = [daily_data.get(d, 0) for d in days]
        labels = days
        x_label = "Day"
        y_label = "Focus Minutes"
    else:
        # Weekly trend for monthly report
        weekly_data = {}
        for item in timeline.items:
            if item.start_time:
                week = item.start_time.isocalendar()[1]
                weekly_data[week] = weekly_data.get(week, 0) + item.duration_seconds
        
        weeks = sorted(weekly_data.keys())[:4]
        if not weeks:
            return None
        
        data = [weekly_data.get(w, 0) for w in weeks]
        labels = [f"W{w}" for w in weeks]
        x_label = "Week"
        y_label = "Focus Minutes"
    
    if not data or all(d == 0 for d in data):
        return None
    
    # Convert seconds to minutes and round to whole numbers
    data_minutes = [round(d / 60) for d in data]
    
    chart.valueAxis.valueMax = max(data_minutes) if max(data_minutes) > 0 else 1
    chart.valueAxis.valueStep = max(round(chart.valueAxis.valueMax / 5), 1)
    chart.categoryAxis.categoryNames = labels
    chart.data = [data_minutes]
    chart.lines[0].strokeColor = colors.HexColor('#10b981')
    chart.lines[0].strokeWidth = 2
    chart.valueAxis.labels.fontSize = 8
    chart.valueAxis.labels.fontName = 'Helvetica'
    chart.categoryAxis.labels.fontSize = 8
    chart.categoryAxis.labels.fontName = 'Helvetica'
    
    # Add axis labels (moved to prevent overlap)
    from reportlab.graphics.shapes import String
    y_axis_label = String(20, 115, y_label, fontSize=8, fontName='Helvetica', textAnchor='end')
    x_axis_label = String(480, 25, x_label, fontSize=8, fontName='Helvetica', textAnchor='end')
    drawing.add(y_axis_label)
    drawing.add(x_axis_label)
    
    drawing.add(chart)
    return drawing


def _create_category_donut_chart(categories) -> Optional[Drawing]:
    """Create a donut chart for category percentage with legend."""
    if not categories.categories:
        return None
    
    total_duration = sum(c.duration_seconds for c in categories.categories)
    if total_duration == 0:
        return None
    
    drawing = Drawing(500, 220)
    pie = Pie()
    pie.x = 100
    pie.y = 40
    pie.width = 180
    pie.height = 180
    pie.slices.strokeWidth = 1
    pie.slices.strokeColor = colors.white
    
    colors_list = [
        colors.HexColor('#3b82f6'),
        colors.HexColor('#10b981'),
        colors.HexColor('#f59e0b'),
        colors.HexColor('#ef4444'),
        colors.HexColor('#8b5cf6'),
    ]
    
    data = [c.duration_seconds for c in categories.categories[:5]]
    pie.data = data
    
    for i, cat in enumerate(categories.categories[:5]):
        pie.slices[i].fillColor = colors_list[i % len(colors_list)]
    
    drawing.add(pie)
    
    # Add legend with category names and percentages
    legend_x = 320
    legend_y = 130
    for i, cat in enumerate(categories.categories[:5]):
        percentage = (cat.duration_seconds / total_duration * 100)
        legend_text = f"{cat.category} {percentage:.0f}%"
        
        # Color box
        from reportlab.graphics.shapes import Rect
        rect = Rect(legend_x, legend_y - i * 25, 10, 10, fillColor=colors_list[i % len(colors_list)], strokeColor=None)
        drawing.add(rect)
        
        # Label text
        from reportlab.graphics.shapes import String
        label_str = String(legend_x + 15, legend_y - i * 25 + 3, legend_text, fontSize=9, fontName='Helvetica', fillColor=colors.black)
        drawing.add(label_str)
    
    return drawing


def _get_report_type(start_date: date, end_date: date) -> str:
    """Determine report type based on date range."""
    diff_days = (end_date - start_date).days + 1
    if diff_days <= 1:
        return "Daily"
    elif diff_days <= 7:
        return "Weekly"
    elif diff_days <= 30:
        return "Monthly"
    else:
        return "Custom Range"


def _format_seconds(seconds: int) -> str:
    """Format seconds into human-readable time."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m"
    else:
        return "0m"
