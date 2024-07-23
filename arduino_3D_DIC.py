import os
import cv2
from pypylon import pylon
from datetime import datetime
import serial
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.info("All libraries imported successfully.")

def set_camera_settings(cameras, exposure_time):
    for camera in cameras:
        camera.Width.SetValue(2472)
        camera.Height.SetValue(2064)
        camera.ExposureTime.SetValue(exposure_time)

def get_folder_size(folder_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            total_size += os.path.getsize(filepath)
    return total_size

def capture_images(cameras, num_samples, output_folder, experiment_name, experiment_description, exposure_time):
    # Record start time
    start_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    logger.info(f"Experiment started at {start_time}")

    # Create folders for each sample
    sample_folders = [os.path.join(output_folder, f'Sample_{i}') for i in range(1, num_samples + 1)]
    for folder in sample_folders:
        os.makedirs(folder, exist_ok=True)

    # Set camera settings for all cameras
    set_camera_settings(cameras, exposure_time)
    logger.info("Camera settings configured.")

    # Flush the serial input buffer to discard any buffered signals
    ser.flushInput()

    sample_index = 0
    visit_counts = [0] * num_samples  # Track visit counts for each sample
    capture_continues = True

    while capture_continues:
        # Wait for the capture signal from Arduino
        line = ser.readline().decode('utf-8').strip()
        if line == "CAPTURE":
            logger.info(f"Capture signal received for Sample {sample_index + 1}")

            # Start grabbing for all cameras (if not already started)
            for camera in cameras:
                if not camera.IsGrabbing():
                    camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

            # Continue only if all cameras are grabbing
            if all(camera.IsGrabbing() for camera in cameras):
                results = [camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException) for camera in cameras]

                if all(result.GrabSucceeded() for result in results):
                    frames = [result.Array for result in results]

                    # Increment the visit count for the current sample
                    visit_counts[sample_index] += 1

                    for j, frame in enumerate(frames):
                        # Resize frame only for display
                        display_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)  # Adjust the scale as needed

                        cv2.imshow(f'Camera {j + 1}', display_frame)

                        # Save images to the respective sample folder
                        sample_folder = sample_folders[sample_index]
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        visit_count_str = f'{visit_counts[sample_index]:04}'
                        filename = f'sample_{sample_index + 1}_{timestamp}_{visit_count_str}_{j}.tif'
                        cv2.imwrite(os.path.join(sample_folder, filename), frame, [cv2.IMWRITE_TIFF_COMPRESSION, 1])

                        # Log image capture event
                        logger.info(f"Image captured for Sample {sample_index + 1}. Filename: {filename}")

                        results[j].Release()

            # Move to the next sample after capturing images for each sample
            sample_index = (sample_index + 1) % num_samples

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            capture_continues = False

    for camera in cameras:
        camera.StopGrabbing()
    cv2.destroyAllWindows()

    # Record end time
    end_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    logger.info(f"Experiment ended at {end_time}")

    # Calculate the total size of the output folder
    total_filesize = get_folder_size(output_folder)
    total_filesize_str = f"{total_filesize / (1024 * 1024):.2f} MB"

    # Generate PDF report
    recording_devices = ", ".join([camera.GetDeviceInfo().GetModelName() for camera in cameras])
    trigger_devices = "Arduino"  # Assuming the trigger is from Arduino
    trigger_interval = "3 seconds"  # Assuming the trigger interval is fixed
    image_folder_filepath = output_folder
    image_format = "TIFF"
    file_compression = "None"
    delay_to_trigger = "3 seconds"  # Assuming delay to trigger is 3 seconds

    generate_pdf_report(start_time, end_time, num_samples, visit_counts, experiment_name, experiment_description, output_folder, 
                        recording_devices, trigger_devices, trigger_interval, image_folder_filepath, image_format, total_filesize_str, file_compression, delay_to_trigger)

def generate_pdf_report(start_time, end_time, num_samples, visit_counts, experiment_name, experiment_description, output_folder, 
                        recording_devices, trigger_devices, trigger_interval, image_folder_filepath, image_format, total_filesize, file_compression, delay_to_trigger):
    pdf_filename = os.path.join(output_folder, f'{start_time}_report.pdf')
    logger.info(f"Generating PDF report: {pdf_filename}")

    # Calculate total duration
    start_datetime = datetime.strptime(start_time, '%Y-%m-%d_%H-%M-%S')
    end_datetime = datetime.strptime(end_time, '%Y-%m-%d_%H-%M-%S')
    total_duration = end_datetime - start_datetime
    total_duration_str = str(total_duration)

    # Create a PDF document
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

    # Content for the PDF
    content = []

    # Experiment details
    content.append(Paragraph("Experiment Details", heading_style))
    experiment_info = [
        ["Experiment Name:", experiment_name],
        ["Recording Devices:", recording_devices],
        ["Trigger Devices:", trigger_devices],
        ["Trigger Interval:", trigger_interval],
        ["Start Time:", start_time],
        ["End Time:", end_time],
        ["Total Duration:", total_duration_str],
        ["Number of Samples:", str(num_samples)],
        ["Image Folder:", image_folder_filepath],
        ["Image Format:", image_format],
        ["Total Filesize:", total_filesize],
        ["File Compression (set manually):", file_compression],
        ["Delay to Trigger (set manually in Arduino):", delay_to_trigger],
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
    content.append(Spacer(1, 12))
    
    # Image folder filepath
    content.append(Paragraph("Image Folder", heading_style))
    content.append(Paragraph(f"Folder Path: {image_folder_filepath}", normal_style))
    content.append(Spacer(1, 12))

    # Experiment description with wrapping
    content.append(Paragraph("Experiment Description:", heading_style))
    content.append(Paragraph(experiment_description, normal_style))
    content.append(Spacer(1, 250))  # Adjust the spacer height as needed for extra space

    # Build the PDF document
    doc.build(content)
    logger.info(f"PDF report generated successfully: {pdf_filename}")

# Initialize serial communication with Arduino
try:
    ser = serial.Serial('COM3', 9600)  # Replace 'COM3' with the appropriate port and baud rate
except serial.SerialException as e:
    logger.error(f"Failed to connect to Arduino: {e}. Try restarting the kernel.")
    ser = None 

# Initialize cameras
cameras = []
try:
    cameras = [pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(device)) for device in pylon.TlFactory.GetInstance().EnumerateDevices()]
    for camera in cameras:
        camera.Open()
except Exception as e:
    logger.error(f"Failed to initialize cameras: {e}. Try restarting the kernel.")

# Only proceed if serial and cameras are initialized
if ser and cameras:
    # Specify the experiment name
    experiment_name = input("Enter the experiment name (Calibration, Speckle, Other): ")
    logger.info(f"Experiment name set: {experiment_name}")

    # Specify experimental details
    experiment_description = input("Enter an experimental description: ")
    logger.info(f"Experiment description set: {experiment_description}")

    # Specify the number of samples
    num_samples = int(input("Enter the number of samples in a single experiment: "))
    logger.info(f"Number of samples set: {num_samples}")

    # Specify the exposure time (in microseconds)
    exposure_time = int(input("Enter the exposure time (in microseconds) - check the required exposure time before with Basler Pylon Viewer: "))
    logger.info(f"Exposure time set: {exposure_time} microseconds")

    # Wait for user to press Enter to start the experiment
    input("Press Enter to start the experiment...")

    # Specify the output folder
    output_folder = os.path.join("captured_images", datetime.now().strftime('%Y-%m-%d_%H-%M-%S'), experiment_name)

    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Capture images from each sample and generate PDF report
    capture_images(cameras, num_samples, output_folder, experiment_name, experiment_description, exposure_time)
else:
    logger.error("Could not start the experiment due to initialization errors.")
