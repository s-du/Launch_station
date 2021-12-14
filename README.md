![Image](https://i.ibb.co/jVMcH0q/astronaut.jpg)
# Launch_station
>... *A gateway to various photogrammetry tools* ...

## What is the goal here?
This small tools is dedicated to photogrammetry 3D reconstructions. It acts as a central call point for various existing reconstruction tools.

### Which tools?
The tool uses Python to call various CLI for the main photogrammetry tools. It includes now:
* Meshroom (see [Link](https://alicevision.org/#meshroom))
* MicMac (see [Link](https://micmac.ensg.eu/index.php/Accueil))
* Agisoft Metashape
* Reality Capture

The CLI transcription system can be found in the /engine folder. A reconstruction method is typically defined as follow:
```
# code block
def launch_odm_reconstruction(img_dir, results_dir, outputs):
  actions
```

### GUI
A simple GUI is being developed (PyQT5). 


## Installation
(TBC)


## Use
The app is made to propose a simplified experience. First the user drops some photos in the dedicated zone (or choose an image folder). Then he defines the output of the 3D reconstruction (point cloud, mesh, etc.). 

### Batch system
By proposing a batch system, the user can launch several reconstructions in a row. 
