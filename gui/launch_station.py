""" MAIN Launch_Station APP : Defining user interaction """

# TODO: Add a batch process system

import os.path
from shutil import copyfile, copytree
from pathlib import Path

# import Pyqt packages
import PyQt5.uic
from PyQt5 import QtCore, QtGui, QtWidgets

# custom modules
from engine import photogrammetry as ph
import resources



class TestListView(QtWidgets.QListWidget):
    dropped = QtCore.pyqtSignal(list)
    def __init__(self, type, parent=None):
        super(TestListView, self).__init__(parent)
        self.setAcceptDrops(True)
        self.setIconSize(QtCore.QSize(72, 72))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
            links = []
            for url in event.mimeData().urls():
                links.append(str(url.toLocalFile()))
            #self.emit(QtCore.SIGNAL("dropped"), links)
            self.dropped.emit(links)
        else:
            event.ignore()

class LaunchStation(QtWidgets.QMainWindow):
    """
    Main Window class for the Pointify application.
    """

    def __init__(self, parent=None):
        """
        Function to initialize the class
        :param parent:
        """
        super(LaunchStation, self).__init__(parent)

        # paths and licences check
        self.licenses_checks()

        # load the ui
        basepath = os.path.dirname(__file__)
        basename = 'launch_station'
        uifile = os.path.join(basepath, 'ui/%s.ui' % basename)
        PyQt5.uic.loadUi(uifile, self)
        self.setWindowTitle('Launch 3D reconstruction')

        # initializaing variables for batch operations
        self.batch = False # no batch operations by default
        self.batch_operations = []

        # add custom listview
        self.listview = TestListView(self)
        self.listview.dropped.connect(self.pictureDropped)
        self.verticalLayout.addWidget(self.listview)

        # add photogrammetry tools in combobox
        self.tool_list = ph.TOOL_LIST
        self.comboBox_soft.addItems(self.tool_list)

        # disable options depending on the defined paths
        self.update_photog_tools()

        # add outputs options in combobox
        self.output_list = ph.OUTPUT_LIST
        self.comboBox_output.addItems(self.output_list)

        # define useful paths
        self.gui_folder = os.path.dirname(__file__)
        self.ref_path = resources.find('other/target.txt')

        # initialize status

        # create connections (signals)
        self.create_connections()

    def licenses_checks(self):
        # load setup file with the different paths to the photogrammetry applications + license files
        file1 = open('setup.txt', 'r')
        Lines = file1.readlines()

        self.paths = []
        paths_names = ['Meshroom .exe path', 'ODM folder', 'MicMac bin folder path', 'Reality Capture .exe path',
                       'Agisoft license path', 'cloudCompare .exe path']
        self.wrong_paths = [False, False, False, False, False, False]  # By default, the setup file is considered valid (all 6 paths working)
        error_text = ''
        lines_to_check = [1, 4, 7, 10, 13, 16]

        for count, l in enumerate(lines_to_check):
            self.paths.append(Lines[l].strip())
            if count == 1 or count == 2:  # for micmac and ODM, test if folder
                if not os.path.isdir(self.paths[count]):
                    self.wrong_paths[count] = True
                    error_text += paths_names[count] + ' is not set (or wrong) \n'
            else:
                if not os.path.isfile(self.paths[count]):
                    self.wrong_paths[count] = True
                    error_text += paths_names[count] + ' is not set (or wrong) \n'

        if error_text:
            msg = QtWidgets.QMessageBox()
            msg.setWindowTitle("Oops something wrong with paths")
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setText(error_text)
            msg.exec_()

        # Metashape license operations
        if not self.wrong_paths[4]:
            # print Metashape license location
            print('license location is: ', self.paths[4])
            # add license to environment variables
            os.putenv('agisoft_LICENSE', self.paths[4])

        # Micmac operations (add environment path if necessary)
        if not self.wrong_paths[1]:
            if not self.paths[1] in os.environ['PATH']:
                print('MicMac bin folder not found in environment variables...')
                os.environ['PATH'] += ';' + self.paths[1]
            else:
                print('MicMac bin folder found in environment variables!')


    def update_photog_tools(self):
        # ['Meshroom .exe path', 'ODM folder', 'MicMac bin folder path', 'Reality Capture .exe path',
        #                'Agisoft license path', 'cloudCompare .exe path']
        for i in range(len(self.wrong_paths)):
            if self.wrong_paths[i]:
                self.comboBox_soft.model().item(i).setEnabled(False)

    def pictureDropped(self, l):
        for url in l:
            if os.path.exists(url):
                print(url)
                if url.endswith('.JPG') or url.endswith('.jpg') or url.endswith('png'):
                    icon = QtGui.QIcon(url)
                    pixmap = icon.pixmap(72, 72)
                    icon = QtGui.QIcon(pixmap)
                    item = QtWidgets.QListWidgetItem(url, self.listview)
                    item.setIcon(icon)
                    item.setStatusTip(url)
                else:
                    msg = QtWidgets.QMessageBox()
                    msg.setIcon(QtWidgets.QMessageBox.Information)

                    msg.setText("Please add jpg or png pictures!")
                    returnValue = msg.exec()
                    pass


    def create_connections(self):
        # 'Simplify buttons'
        self.pushButton_load.clicked.connect(self.load_img)
        self.pushButton_go.clicked.connect(self.go)
        self.pushButton_add_batch.clicked.connect(self.add_batch)


    def load_img(self):
        folder = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))

    def go(self):
        # get user choices
        i = self.comboBox_soft.currentIndex()  # get the user choice for the software
        j = self.comboBox_output.currentIndex()  # get the user choice for the outputs
        soft_name = ph.TOOL_LIST[i]
        print(soft_name, ' will be used for the processing...')

        # get list of images to process
        img_list = [str(self.listview.item(i).text()) for i in range(self.listview.count())]
        print('... and the following images will be processed: \n', img_list)

        # get user choice for the output folder
        out_dir = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select output_folder"))
        out_subdir = os.path.join(out_dir, soft_name)
        if not os.path.exists(out_subdir):
            os.mkdir(out_subdir)

        img_dir = os.path.join(out_subdir, 'images')
        results_dir = os.path.join(out_subdir, 'outputs')

        if not os.path.exists(img_dir):
            os.mkdir(img_dir)
        if not os.path.exists(results_dir):
            os.mkdir(results_dir)

        for img in img_list:
            _, img_file = os.path.split(img)
            dest_file = os.path.join(img_dir, img_file)
            if not os.path.exists(dest_file):
                copyfile(img,dest_file)

        if not self.batch:
            # get software options
            if i == 0: # Meshroom
                options = [self.paths[0], results_dir]
            if i == 1: # ODM
                out_dir_odm = Path(out_dir)
                options = [self.paths[1], out_dir_odm]
            if i == 2: # MicMac
                pass
            if i == 3: # Agisoft
                pass
            if i == 4: # RealityCapture
                pass

            # launch reconstruction
            ph.launch_3D_reconstruction(i, j, img_dir, options) # i = software name, j = required outputs, options are software dependant
        else:
            pass

    def add_batch(self):
        i = self.comboBox_soft.currentIndex()  # get the user choice for the software
        j = self.comboBox_output.currentIndex()  # get the user choice for the outputs

        self.batch_operations.append([i,j])

        # add item to list view


        # update status of operations
        self.batch = True

"""
OLD STUFF

        i = self.comboBox_soft.currentIndex()
        if i == 0:
            ph.launch_meshroom_reconstruction(meshroom_path, img_dir, out_dir)
        elif i == 1:
            ph.launch_agisoft_reconstruction(img_dir, out_dir)
        else:
            ph.launch_agisoft_reconstruction_with_markers(self.ref_path, img_dir, out_dir)

        if i !=2:
            # launch ortho rectification
            obj_path = os.path.join(out_dir, 'texturedMesh.obj')
            ph.rotation_workflow(cc_path, obj_path)

            # launch ortho creation
            rotated_obj_path = os.path.join(out_dir, 'texturedMesh_TRANSFORMED.obj')
            output_ortho_path = os.path.join(out_dir, 'ortho.png')
            final_ortho_path = os.path.join(out_dir, 'ortho_final.png')
            # render ortho
            # ph.render_cloud_rgb_simple(rotated_obj_path, output_ortho_path, 'bottom')
            # or HD ortho
            rotate_view = False
            if i==0:
                ph.render_cloud_rgb_ortho_zoom(rotated_obj_path, output_ortho_path, 'bottom', 2)
                rotate_view = True
                trans_init, inv_trans = ph.bottom_mat()
            else:
                ph.render_cloud_rgb_ortho_zoom(rotated_obj_path, output_ortho_path, 'top', 2)

            # rotate image
            ph.image_rotation_workflow(output_ortho_path, final_ortho_path)

            # use open3D
            textured_mesh = o3d.io.read_triangle_mesh(rotated_obj_path,True)
            if rotate_view:
                textured_mesh.transform(trans_init)
            o3d.visualization.draw_geometries_with_editing([textured_mesh])"""