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

def validate_config(config):
    """
    Validates the configuration dictionary to ensure all required parameters are present
    and have the correct data types.

    Args:
        config (dict): The configuration dictionary to validate.

    Raises:
        ValueError: If any required configuration key is missing or has an incorrect type.
    """
    # Define required top-level keys and their expected types
    required_top_level_keys = {
        'camera_settings': dict,
        'arduino_settings': dict,
        'number_of_samples': int,
        'output_folder': str,
        'experiment_name': str
    }

    # Check for required top-level keys
    for key, expected_type in required_top_level_keys.items():
        if key not in config:
            raise ValueError(f"Missing required configuration key: '{key}'")
        if not isinstance(config[key], expected_type):
            raise ValueError(f"Configuration key '{key}' must be of type {expected_type.__name__}")

    # Validate 'camera_settings'
    camera_settings = config['camera_settings']
    required_camera_keys = {
        'exposure_time': (int, float),
        'width': int,
        'height': int
    }
    for key, expected_type in required_camera_keys.items():
        if key not in camera_settings:
            raise ValueError(f"Missing required camera setting: '{key}'")
        if not isinstance(camera_settings[key], expected_type):
            raise ValueError(f"Camera setting '{key}' must be of type {expected_type if isinstance(expected_type, tuple) else expected_type.__name__}")

    # Validate 'exposure_mode' if present
    exposure_mode = camera_settings.get('exposure_mode', 'Manual')
    if exposure_mode not in ['Manual', 'SetOnce', 'Continuous']:
        raise ValueError("Invalid 'exposure_mode'. Must be one of 'Manual', 'SetOnce', or 'Continuous'.")

    # If 'exposure_mode' is 'Manual', ensure 'exposure_time' is provided and valid
    if exposure_mode == 'Manual':
        if camera_settings['exposure_time'] is None:
            raise ValueError("'exposure_time' must be provided for 'Manual' exposure_mode.")

    # Validate 'arduino_settings'
    arduino_settings = config['arduino_settings']
    required_arduino_keys = {
        'input_pins': dict,
        'output_pins': dict
    }
    for key, expected_type in required_arduino_keys.items():
        if key not in arduino_settings:
            raise ValueError(f"Missing required arduino setting: '{key}'")
        if not isinstance(arduino_settings[key], expected_type):
            raise ValueError(f"Arduino setting '{key}' must be of type {expected_type.__name__}")

    # Validate Arduino input pins
    required_input_pins = ['DO_CAPTURE', 'DO_RUN_COMPLETE']
    for pin in required_input_pins:
        if pin not in arduino_settings['input_pins']:
            raise ValueError(f"Missing required Arduino input pin: '{pin}'")
        if not isinstance(arduino_settings['input_pins'][pin], int):
            raise ValueError(f"Arduino input pin '{pin}' must be of type int")

    # Validate Arduino output pins
    required_output_pins = ['DI_RUN', 'DI_CAPTURE_COMPLETE']
    for pin in required_output_pins:
        if pin not in arduino_settings['output_pins']:
            raise ValueError(f"Missing required Arduino output pin: '{pin}'")
        if not isinstance(arduino_settings['output_pins'][pin], int):
            raise ValueError(f"Arduino output pin '{pin}' must be of type int")

    # Validate optional Arduino settings
    if not isinstance(arduino_settings.get('auto_detect_port', False), bool):
        raise ValueError("'auto_detect_port' in arduino_settings must be of type bool")

    # If 'auto_detect_port' is False, ensure 'port' is provided and valid
    if not arduino_settings.get('auto_detect_port', False):
        if 'port' not in arduino_settings:
            raise ValueError("'port' must be specified in arduino_settings when 'auto_detect_port' is False")
        if not isinstance(arduino_settings['port'], str):
            raise ValueError("'port' in arduino_settings must be of type str")

    # Validate 'number_of_samples'
    if config['number_of_samples'] <= 0:
        raise ValueError("'number_of_samples' must be a positive integer")

    # Validate 'interval_minutes'
    if not isinstance(config.get('interval_minutes', 30), int) or config.get('interval_minutes', 30) <= 0:
        raise ValueError("'interval_minutes' must be a positive integer")

    # Validate 'total_runs'
    if not isinstance(config.get('total_runs', -1), int):
        raise ValueError("'total_runs' must be an integer")

    # Validate 'display_scale_factor'
    if not isinstance(config.get('display_scale_factor', 0.5), (int, float)):
        raise ValueError("'display_scale_factor' must be a float or int")

    # Validate 'display_images'
    if not isinstance(config.get('display_images', True), bool):
        raise ValueError("'display_images' must be of type bool")

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