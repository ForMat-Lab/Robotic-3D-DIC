import json
import os
from datetime import datetime
import logging
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

logger = logging.getLogger(__name__)

def load_config(config_file="config.json"):
    """
    Load configuration settings from a JSON file with error handling for empty or invalid files.
    """
    if not os.path.exists(config_file):
        logger.error(f"Configuration file {config_file} does not exist.")
        return None

    with open(config_file, 'r') as f:
        try:
            config = json.load(f)
            if not config:
                raise ValueError("Configuration file is empty.")
        except json.JSONDecodeError as e:
            logger.error(f"Error reading the configuration file: {e}")
            return None
        except ValueError as e:
            logger.error(e)
            return None

    logger.info(f"Configuration loaded from {config_file}.")
    return config

def get_folder_size(folder_path):
    """
    Calculate the total size of the output folder.
    """
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            total_size += os.path.getsize(filepath)
    return total_size

# Needs more work
def generate_pdf_report(config, start_time, end_time, num_samples, visit_counts, output_folder):
    """
    Generate a PDF report with experiment details.
    """
    pdf_filename = os.path.join(output_folder, f'{start_time}_report.pdf')
    logger.info(f"Generating PDF report: {pdf_filename}")

    start_datetime = datetime.strptime(start_time, '%Y-%m-%d_%H-%M-%S')
    end_datetime = datetime.strptime(end_time, '%Y-%m-%d_%H-%M-%S')
    total_duration = end_datetime - start_datetime
    total_duration_str = str(total_duration)

    # Create PDF document
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
    styles = getSampleStyleSheet()
    normal_style = styles["Normal"]
    heading_style = styles["Heading1"]
    table_style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                              ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                              ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                              ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                              ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                              ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                              ('GRID', (0, 0), (-1, -1), 1, colors.black)])

    # Add content to the PDF
    content = []

    # Experiment details
    content.append(Paragraph("Experiment Details", heading_style))
    experiment_info = [
        ["Experiment Name:", config['experiment_name']],
        ["Recording Devices:", ", ".join(config['recording_devices'])],
        ["Trigger Devices:", config['trigger_devices']],
        ["Trigger Interval:", config['trigger_interval']],
        ["Start Time:", start_time],
        ["End Time:", end_time],
        ["Total Duration:", total_duration_str],
        ["Number of Samples:", str(num_samples)],
        ["Image Format:", config['image_format']],
        ["Total Filesize:", f"{get_folder_size(output_folder) / (1024 * 1024):.2f} MB"],
    ]
    experiment_table = Table(experiment_info, colWidths=[150, 350])
    experiment_table.setStyle(table_style)
    content.append(experiment_table)
    content.append(Spacer(1, 12))

    # Visit counts per sample
    content.append(Paragraph("Visit Counts per Sample", heading_style))
    visit_info = [["Sample", "Visit Count"]]
    for i, count in enumerate(visit_counts):
        visit_info.append([str(i + 1), str(count)])
    visit_table = Table(visit_info)
    visit_table.setStyle(table_style)
    content.append(visit_table)

    # Build the PDF document
    doc.build(content)
    logger.info(f"PDF report generated successfully: {pdf_filename}")