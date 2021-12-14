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
The CLI transcription system can be found in the /engine folder.

### Batch system
By proposing a batch system, the user can launch several reconstructions in a row. The output of the 3D reconstruction can also be defined (point cloud, mesh, etc.)
