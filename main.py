""" Main entry point to the Launch_station application. """

# define authorship information
__authors__ = ['Samuel Dubois']
__author__ = ','.join(__authors__)
__credits__ = []
__copyright__ = 'Copyright (c) CSTC/WTCB/BBRI 2021'
__license__ = ''

from PyQt5 import QtWidgets
#from qt_material import apply_stylesheet

import os


def main(argv=None):
    """
    Creates the main window for the application and begins the \
    QApplication if necessary.

    :param      argv | [, ..] || None

    :return      error code
    """

    # Define installation path
    install_folder = os.path.dirname(__file__)

    app = None

    # create the application if necessary
    if (not QtWidgets.QApplication.instance()):
        app = QtWidgets.QApplication(argv)
        # apply_stylesheet(app, theme = 'light_blue.xml')

    # create the main window
    from gui.launch_station import LaunchStation
    window = LaunchStation()
    window.show()

    # run the application if necessary
    if (app):
        return app.exec_()

    # no errors since we're not running our own event loop
    return 0


if __name__ == '__main__':
    import sys

    sys.exit(main(sys.argv))