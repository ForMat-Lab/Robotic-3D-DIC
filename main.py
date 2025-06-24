"""
Robotic-3D-DIC: Automated Image Acquisition System

Developed at ForMatLab, Penn State University (2025)

Author:      Özgüç B. Çapunaman
Maintainers: Özgüç B. Çapunaman, Alale Mohseni
GitHub:      https://github.com/ForMat-Lab/Robotic-3D-DIC
"""

import logging
from src.util import load_config, validate_config
from src.Experiment import Experiment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for the Robotic-3D-DIC experiment.
    Loads configuration, validates it, then runs the Experiment.
    """
    try:
        # Load configuration
        config = load_config()
        if not config:
            logger.error("Failed to load configuration.")
            return

        # Validate configuration
        validate_config(config)
        logger.info("Configuration validation successful.")

        # Create and run the experiment
        experiment = Experiment(config)
        experiment.run()

    except ValueError as ve:
        logger.error(f"Configuration Error: {ve}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        # Ensure cleanup in case of an exception
        if 'experiment' in locals():
            experiment.cleanup()

if __name__ == "__main__":
    main()