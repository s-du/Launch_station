""" MAIN Launch_Station APP : Defining user interaction """

# TODO: Add a batch process system

import os.path
from shutil import copyfile, copytree
from pathlib import Path
import sys
import subprocess
import pkg_resources

# import Pyqt packages
import PyQt5.uic
from PyQt5 import QtCore, QtGui, QtWidgets

# custom modules
from engine import photogrammetry as ph
import resources as res


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


class dialog_agisoft(QtWidgets.QDialog):
    """
    Dialog that opens finding specific walls
    """

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self)
        basepath = os.path.dirname(__file__)
        basename = 'dialog_agisoft'
        uifile = os.path.join(basepath, 'ui/%s.ui' % basename)
        PyQt5.uic.loadUi(uifile, self)

        self.pushButton_browse.clicked.connect(self.get_gcp)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def fill_combos(self, qual_list, text_list):
        self.qual_list = qual_list
        self.text_list = text_list
        self.comboBox_qual.addItems(self.qual_list)
        self.comboBox_res.addItems(self.res_list)


    def get_gcp(self):
        pass




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

        # add icon
        astro = res.find('imgs/astronaut_small_tr.png')
        self.pushButton_go.setIcon(QtGui.QIcon(astro))
        self.pushButton_go.setStyleSheet("background-color: #B9B9B9")

        # add custom list view
        self.listview = TestListView(self)
        self.listview.dropped.connect(self.picture_dropped)
        self.verticalLayout.addWidget(self.listview)

        # prepare tree view
        # create model (for the tree structure)
        self.model = QtGui.QStandardItemModel()
        self.treeView_batch.setModel(self.model)
        # add right click contextual menu on the tree view
        self.treeView_batch.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeView_batch.customContextMenuRequested.connect(self.openMenu)

        self.selmod = self.treeView_batch.selectionModel()

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
        self.ref_path = res.find('other/target.txt')

        # create connections (signals)
        self.create_connections()

    def openMenu(self):
        pass

    def add_item_in_tree(self, parent, line):
        item = QtGui.QStandardItem(line)
        parent.appendRow(item)

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
            os.environ['agisoft_LICENSE'] = str(Path(self.paths[4]))
            print('Here it is!!', os.environ['agisoft_LICENSE'])

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

    def picture_dropped(self, l):

        for url in l:
            if os.path.exists(url):
                print(url)
                if url.endswith('.JPG') or url.endswith('.jpg') or url.endswith('png'):
                    self.img_list = [str(self.listview.item(i).text()) for i in range(self.listview.count())]
                    if url not in self.img_list:
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


        if len(self.img_list) > 3:
            print('... the following images will be processed: \n', self.img_list)
            # enable some widgets
            self.pushButton_go.setEnabled(True)
            self.pushButton_add_batch.setEnabled(True)
            self.comboBox_output.setEnabled(True)
            self.comboBox_soft.setEnabled(True)
            self.pushButton_go.setStyleSheet("background-color: #02DAFF")

    def create_connections(self):
        # 'Simplify buttons'
        self.pushButton_load.clicked.connect(self.load_img)
        self.pushButton_go.clicked.connect(self.go)
        self.pushButton_add_batch.clicked.connect(self.add_batch)

    def load_img(self):
        folder = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        imported_list = []
        for path in os.listdir(folder):
            full_path = folder + '/' + path # TODO make that more clean
            imported_list.append(full_path)
        print(imported_list)
        self.picture_dropped(imported_list)

    def go(self):
        # get user choices
        i = self.comboBox_soft.currentIndex()  # get the user choice for the software
        j = self.comboBox_output.currentIndex()  # get the user choice for the outputs

        # get user choice for the output folder
        self.out_dir = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select output_folder"))

        if os.path.isdir(self.out_dir): # nothing happens if the user do not choose a folder
            if not self.batch:
                self.launch_op(i,j)
            else:
                for i,op in enumerate(self.batch_operations):
                    i = op[0]
                    j = op[1]
                    self.lauch_op(i, j, batch=i+1)

    def launch_op(self, soft, outputs, batch=0):
        soft_name = ph.TOOL_LIST[soft]
        if batch !=0:
            soft_name = 'OP' + str(batch) + '_' + 'soft_name'
        print(soft_name, ' will be used for this processing...')

        # create subfolders to store results
        out_subdir = os.path.join(self.out_dir, soft_name)
        if not os.path.exists(out_subdir):
            os.mkdir(out_subdir)

        img_dir = os.path.join(out_subdir, 'images')
        results_dir = os.path.join(out_subdir, 'outputs')

        if not os.path.exists(img_dir):
            os.mkdir(img_dir)
        if not os.path.exists(results_dir):
            os.mkdir(results_dir)

        for img in self.img_list:
            _, img_file = os.path.split(img)
            dest_file = os.path.join(img_dir, img_file)
            if not os.path.exists(dest_file):
                copyfile(img, dest_file)

        # convert path to windows format
        # TODO: avoid mixing os.path and pathlib methods
        out_dir_windows = Path(self.out_dir)
        img_dir_windows = Path(img_dir)
        results_dir_windows = Path(results_dir)

        # get software options
        if soft == 0:  # Meshroom
            options = [self.paths[0], results_dir_windows, ''] # the '' should be replaced with markers txt file path
            ph.launch_meshroom_reconstruction(outputs, img_dir_windows, options)
        # ______________________________________________

        if soft == 1:  # ODM
            options = [self.paths[1], out_dir_windows]
            ph.launch_odm_reconstruction(outputs, img_dir_windows, options)
        # ______________________________________________

        if soft == 2:  # MicMac
            pass
        # ______________________________________________

        if soft == 3:  # RealityCapture
            options = [self.paths[3], results_dir_windows]
            ph.launch_realitycapture_reconstruction(outputs, img_dir_windows, options)
        # ______________________________________________

        if soft == 4:  # Agisoft
            # check if module is installed
            required = {'metashape'}
            installed = {pkg.key for pkg in pkg_resources.working_set}
            print(installed)
            missing = required - installed
            if missing:
                print(r"Ok let's intall Agisoft!")
                self.install_agisoft_module()

            # launch dialog for user options
            dialog = dialog_agisoft()
            dialog.setWindowTitle("Choose parameters for Agisoft reconstruction")

            if dialog.exec_():
                try:
                    do_precleaning = True
                    qual_list = ['Medium', 'High']
                    text_list = ['2048', '4096', '8192']
                    dialog.fill_combos(qual_list, text_list)
                    nb_text = int(dialog.lineEdit_nb_text.text())
                    qual_idx = dialog.comboBox_qual.currentIndex()
                    qual = qual_list[qual_idx]

                    text_size_idx = dialog.comboBox_res.currentIndex()
                    text_size = text_list[text_size_idx]

                    if not dialog.checkBox_clean.isChecked():
                        do_precleaning = False

                except ValueError:
                    QtWidgets.QMessageBox.warning(self, "Warning",
                                                  "Oops! The number of texture is not valid.  Try again...")
                    self.dialog_agisoft()

            options = [results_dir_windows, '', do_precleaning, qual, nb_text, text_size]
            ph.launch_agisoft_reconstruction(outputs, img_dir_windows, options)
        # ______________________________________________


        # launch reconstruction
        ph.launch_3D_reconstruction(soft, outputs, img_dir_windows, options)

    def install_agisoft_module(self):
        # install Metashape module if necessary
        def install(package):
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

        metashape_module = res.find('other/Metashape-1.7.3-cp35.cp36.cp37.cp38-none-win_amd64.whl')
        install(metashape_module)

    def add_batch(self):
        i = self.comboBox_soft.currentIndex()  # get the user choice for the software
        j = self.comboBox_output.currentIndex()  # get the user choice for the outputs

        for op in self.batch_operations:
            if not op == [i,j]:
                self.batch_operations.append([i,j])
            else:
                msg = QtWidgets.QMessageBox()
                msg.setWindowTitle("Oops")
                msg.setIcon(QtWidgets.QMessageBox.Warning)
                msg.setText('Operation already foreseen!')

        # add item to tree view
        batch_op_soft = self.tool_list[i]
        batch_op_out = self.output_list[j]
        batch_op = batch_op_soft + ', ' + batch_op_out
        self.add_item_in_tree(self.model, batch_op)
        self.model.setHeaderData(0, QtCore.Qt.Horizontal, 'Batch operations')

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