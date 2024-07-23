import os
import time
import cv2
from pypylon import pylon
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

print("All libraries imported successfully.")

def set_camera_settings(cameras, exposure_time):
    for camera in cameras:
        camera.Width.SetValue(2472)
        camera.Height.SetValue(2064)
        camera.ExposureTime.SetValue(exposure_time)

def capture_images(cameras, num_samples, output_folder, experiment_name, experiment_description, interval, exposure_time):
    # Record start time
    start_time = time.strftime('%Y-%m-%d_%H-%M-%S')

    # Create folders for each sample
    sample_folders = [os.path.join(output_folder, f'Sample_{i}') for i in range(1, num_samples + 1)]
    for folder in sample_folders:
        os.makedirs(folder, exist_ok=True)

    # Set camera settings for all cameras
    set_camera_settings(cameras, exposure_time)
    # Track visit counts for each sample
    sample_index = 0
    visit_counts = [0] * num_samples  # Track visit counts for each sample
    capture_continues = True

    while capture_continues:
        start_capture_time = time.time()

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
                    timestamp = time.strftime('%Y%m%d_%H%M%S', time.localtime())
                    visit_count_str = f'{visit_counts[sample_index]:04}'
                    filename = f'sample_{sample_index + 1}_{timestamp}_{visit_count_str}_{j}.tif'
                    cv2.imwrite(os.path.join(sample_folder, filename), frame, [cv2.IMWRITE_TIFF_COMPRESSION, 1])
                    
                    # Get the current time
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

                    # Print a message indicating that images have been captured for this sample along with the current time
                    print(f"{current_time}: Images captured for Sample {sample_index + 1}. Filename: {filename}")

                    results[j].Release()

        elapsed_capture_time = time.time() - start_capture_time
        time_to_wait = max(0, interval - elapsed_capture_time)

        key = cv2.waitKey(int(time_to_wait * 1000)) & 0xFF
        if key == ord('q'):
            capture_continues = False

        # Move to the next sample after capturing images for each sample
        sample_index = (sample_index + 1) % num_samples

        # Move cameras to the next sample (pseudo-code, replace with your actual camera movement code)
        #move_cameras_to_next_sample(sample_index, num_samples)

    for camera in cameras:
        camera.StopGrabbing()
    cv2.destroyAllWindows()

    # Record end time
    end_time = time.strftime('%Y-%m-%d_%H-%M-%S')

    # Generate PDF report
    generate_pdf_report(start_time, end_time, num_samples, visit_counts, experiment_name, experiment_description, interval, exposure_time, output_folder)

def generate_pdf_report(start_time, end_time, num_samples, visit_counts, experiment_name, experiment_description, interval, exposure_time, output_folder):
    pdf_filename = os.path.join(output_folder, f'{start_time}_report.pdf')

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
        ["Start Time:", start_time],
        ["End Time:", end_time],
        ["Total Duration:", total_duration_str],
        ["Number of samples:", str(num_samples)],
        ["Interval Time (seconds):", str(interval)],
        ["Exposure Time (microseconds):", str(exposure_time)],
    ]
    experiment_table = Table(experiment_info, colWidths=[150, 350])
    experiment_table.setStyle(table_style)
    content.append(experiment_table)
    content.append(Spacer(1, 12))

    # Visit counts per sample
    content.append(Paragraph("Visit Counts per sample", heading_style))
    visit_info = [["sample", "Visit Count"]]
    for i, count in enumerate(visit_counts):
        visit_info.append([str(i + 1), str(count)])
    visit_table = Table(visit_info)
    visit_table.setStyle(table_style)
    content.append(visit_table)
    content.append(Spacer(1, 12))
    
    # Experiment description with wrapping
    content.append(Paragraph("Experiment Description:", heading_style))
    content.append(Paragraph(experiment_description, normal_style))
    content.append(Spacer(1, 250))  # Adjust the spacer height as needed for extra space

    # Build the PDF document
    doc.build(content)
    print("PDF report generated successfully:", pdf_filename)

# Function to move cameras to the next sample (pseudo-code, replace with your actual camera movement code)
# def move_cameras_to_next_sample(sample_index, num_samples):
#     next_sample = (sample_index + 1) % num_samples + 1  # Calculate the next sample index (and add 1 to start from 1 instead of 0)
#     print(f"Moving cameras to Sample {next_sample}...")
#     # Your camera movement logic goes here

if __name__ == "__main__":
    # Initialize cameras
    cameras = [pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(device)) for device in pylon.TlFactory.GetInstance().EnumerateDevices()]

    # Open cameras
    for camera in cameras:
        camera.Open()

    # Specify the experiment name
    experiment_name = input("Enter the experiment name (Calibration, Speckle, Other): ")

    # Specify experimental details
    experiment_description = input("Enter an experimental description: ")

    # Specify the number of samples
    num_samples = int(input("Enter the number of samples in a single experiment: "))

    # Specify the interval time (in seconds)
    interval = float(input("Enter the interval time of image acquisition (in seconds): "))

    # Specify the exposure time (in microseconds)
    exposure_time = int(input("Enter the exposure time (in microseconds) - check the required exposure time before with Basler Pylon Viewer: "))

    # Specify the output folder
    output_folder = os.path.join("captured_images", time.strftime('%Y-%m-%d_%H-%M-%S'))

    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Prompt to start recording
    input("Press Enter to start recording...")

   
    # Capture images from each sample and generate PDF report
    capture_images(cameras, num_samples, output_folder, experiment_name, experiment_description, interval, exposure_time)
