# src/util.py

import json
import os
import logging
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
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

def generate_pdf_report(
    config, start_time, end_time,
    run_count, total_samples_collected,
    visit_counts, output_folder
):
    """
    Generate a comprehensive PDF report with experiment details.
    """
    pdf_filename = os.path.join(output_folder, f'{start_time}_report.pdf')
    logger.info(f"Generating PDF report: {pdf_filename}")

    # Convert start and end times to datetime objects
    start_datetime = datetime.strptime(start_time, '%Y-%m-%d_%H-%M-%S')
    end_datetime = datetime.strptime(end_time, '%Y-%m-%d_%H-%M-%S')
    total_duration = end_datetime - start_datetime
    total_duration_str = str(total_duration)

    # Get total filesize in MB
    total_filesize_mb = get_folder_size(output_folder) / (1024 * 1024)

    # Create PDF document
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
    styles = getSampleStyleSheet()
    normal_style = styles["Normal"]
    heading_style = styles["Heading1"]
    subheading_style = styles["Heading2"]

    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f2f2f2")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ])

    # Add content to the PDF
    content = []

    # Title
    content.append(Paragraph("Experiment Report", heading_style))
    content.append(Spacer(1, 12))

    # Experiment details
    content.append(Paragraph("Experiment Details", subheading_style))
    experiment_info = [
        ["Experiment Name", config.get('experiment_name', 'N/A')],
        ["Start Time", start_time],
        ["End Time", end_time],
        ["Total Duration", total_duration_str],
        ["Total Runs Performed", str(run_count)],
        ["Interval Between Runs (minutes)", str(config.get('interval_minutes', 'N/A'))],
        ["Number of Samples", str(config.get('number_of_samples', 'N/A'))],
        ["Total Images Captured", str(total_samples_collected)],
        ["Total Filesize", f"{total_filesize_mb:.2f} MB"],
        ["Output Folder", output_folder],
    ]
    experiment_table = Table(experiment_info, colWidths=[200, 350])
    experiment_table.setStyle(table_style)
    content.append(experiment_table)
    content.append(Spacer(1, 12))

    # Camera settings
    content.append(Paragraph("Camera Settings", subheading_style))
    camera_settings = config.get('camera_settings', {})
    camera_info = [
        ["Width", str(camera_settings.get('width', 'N/A'))],
        ["Height", str(camera_settings.get('height', 'N/A'))],
        ["Exposure Time (µs)", str(camera_settings.get('exposure_time', 'N/A'))],
        ["Auto Exposure", str(camera_settings.get('auto_exposure', 'N/A'))],
        ["Scale Factor", str(camera_settings.get('scale_factor', 'N/A'))],
    ]
    camera_table = Table(camera_info, colWidths=[200, 350])
    camera_table.setStyle(table_style)
    content.append(camera_table)
    content.append(Spacer(1, 12))

    # Arduino settings
    content.append(Paragraph("Arduino Settings", subheading_style))
    arduino_settings = config.get('arduino_settings', {})
    input_pins = arduino_settings.get('input_pins', {})
    output_pins = arduino_settings.get('output_pins', {})
    arduino_info = [
        ["Auto Detect Port", str(arduino_settings.get('auto_detect_port', 'N/A'))],
        ["Port", arduino_settings.get('port', 'N/A')],
        ["Input Pins", ", ".join([f"{k}: {v}" for k, v in input_pins.items()])],
        ["Output Pins", ", ".join([f"{k}: {v}" for k, v in output_pins.items()])],
    ]
    arduino_table = Table(arduino_info, colWidths=[200, 350])
    arduino_table.setStyle(table_style)
    content.append(arduino_table)
    content.append(Spacer(1, 12))

    # Visit counts per sample
    content.append(Paragraph("Visit Counts per Sample", subheading_style))
    visit_info = [["Sample Index", "Visit Count"]]
    for i, count in enumerate(visit_counts):
        visit_info.append([str(i), str(count)])
    visit_table = Table(visit_info, colWidths=[200, 350])
    visit_table.setStyle(table_style)
    content.append(visit_table)
    content.append(Spacer(1, 12))

    # Build the PDF document
    try:
        doc.build(content)
        logger.info(f"PDF report generated successfully: {pdf_filename}")
    except Exception as e:
        logger.error(f"Failed to generate PDF report: {e}")