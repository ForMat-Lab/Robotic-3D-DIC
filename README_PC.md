+ Install Pylon [https://www2.baslerweb.com/en/downloads/software-downloads/#type=pylonsoftware;language=all;version=all;os=all]
	- Profiles: Developer
	- Interfaces: USB

+ Install Anaconda [https://docs.anaconda.com/anaconda/install/windows/]

+ Create Anaconda Environment + Install Libraries
- Open Anaconda Prompt. Following are command lines to be executed, which are denoted by the dollar ($) sign. Do not type in the dollar ($) sign.
	$ conda create --name limc2
	$ conda activate limc2
	$ pip install pypylon opencv-python pyfirmata reportlab

+ Install Arduino IDE [https://www.arduino.cc/en/software]
	- Tools>Manage Libraries>Search&Install:Firmata
	- File>Examples>Firmata>StandardFirmata
	- Flash Arduino with the StandardFirmata Code