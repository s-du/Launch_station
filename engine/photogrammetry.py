import resources
import os
import subprocess
from open3d import io, visualization
import time
import math
import numpy as np
from cv2 import imread, imwrite, boundingRect, findNonZero
import Metashape

from skimage.color import rgb2gray
from skimage.transform import rotate
from skimage.transform import (hough_line, hough_line_peaks)
from skimage import io
from skimage.filters import threshold_otsu, sobel


"""
======================================================================================
General functions
======================================================================================
"""

def win_function(project_folder, function_name, fun_txt):
    batpath = os.path.join(project_folder, function_name + ".bat")
    with open(batpath, 'w') as OPATH:
        OPATH.writelines(fun_txt)
    subprocess.call([batpath])
    os.remove(batpath)


"""
======================================================================================
Reconstruction functions
======================================================================================
"""
def launch_odm_reconstruction(img_dir, results_dir):
    function_name = 'run_odm'
    print('RUNNING ODM RECONSTRUCTION')

    img_dir_win = '"' + img_dir + '"'
    # fun_txt = 'cd ' + img_dir_win + ' \n' + r'mm3d Tapioca MulScale ".*JPG" 500 2500'
    fun_txt = 'cd ' + img_dir_win + ' \n' + r'mm3d Tapas RadialStd ".*JPG" Out=Fontaine'
    win_function(img_dir, function_name, fun_txt)

def launch_micmac_reconstruction(img_dir, results_dir):
    function_name = 'run_mm'
    print('RUNNING MICMAC RECONSTRUCTION')

    img_dir_win = '"' + img_dir + '"'
    # fun_txt = 'cd ' + img_dir_win + ' \n' + r'mm3d Tapioca MulScale ".*JPG" 500 2500'
    fun_txt = 'cd ' + img_dir_win + ' \n' + r'mm3d Tapas RadialStd ".*JPG" Out=Fontaine'
    win_function(img_dir, function_name, fun_txt)

def launch_realitycapture_reconstruction(rc_path, license_path, img_dir, results_dir):
    function_name = 'run_rc'
    print('RUNNING REALITY CAPTURE RECONSTRUCTION')

    license_path_win = '"' + license_path + '"'
    img_dir_win = '"' + img_dir + '"'
    results_dir_win = '"' + results_dir + '"'

    fun_txt = 'SET MY_PATH="' + rc_path + '" \n' + '%MY_PATH% -addFolder ' + img_dir_win + ' -align '
    win_function(img_dir, function_name, fun_txt)


def launch_meshroom_reconstruction(meshroom_path, img_dir, results_dir):
    function_name = 'run_meshroom'
    print('RUNNING MESHROOM RECONSTRUCTION')

    ref_process = resources.find(r'other\ref_process_v5_tag.mg')
    img_dir_win = '"' + img_dir + '"'
    results_dir_win = '"' + results_dir + '"'

    # CloudCompare fonction
    fun_txt = 'SET MY_PATH="' + meshroom_path + '" \n' + '%MY_PATH% --input ' + img_dir_win + ' --output ' \
              + results_dir_win + ' --pipeline ' + ref_process + ' --forceCompute'
    win_function(img_dir, function_name, fun_txt)

def launch_agisoft_reconstruction_with_markers(ref_path, img_dir, results_dir,opt_make_ortho = True):
    print('RUNNING AGISOFT RECONSTRUCTION')
    # file names
    model_rgb_file = os.path.join(results_dir, 'texturedMesh.obj')
    if opt_make_ortho:
        ortho_rgb_file = os.path.join(results_dir, 'ortho_rgb.tif')

    # new project
    doc = Metashape.Document()
    doc.save(path=results_dir + "/" + 'agisoft.psx')

    # creating new chunk for RGB
    chk = doc.addChunk()
    chk.label = 'RGB'

    # loading RGB images
    image_list = os.listdir(img_dir)
    photo_list = []
    for photo in image_list:
        photo_list.append("/".join([img_dir, photo]))
    chk.addPhotos(photo_list)

    # proces RGB images

    chk.matchPhotos(guided_matching=True, generic_preselection=False, reference_preselection=False)
    chk.alignCameras()
    chk.buildDepthMaps()
    chk.buildModel(source_data=Metashape.DataSource.DepthMapsData, face_count=Metashape.MediumFaceCount)
    chk.buildUV(mapping_mode=Metashape.GenericMapping)
    chk.buildTexture(texture_size=4096)  # optional argument to change texture size
    chk.detectMarkers()
    chk.importReference(path=ref_path, format=Metashape.ReferenceFormatCSV, delimiter=';', columns='nxyz')
    chk.updateTransform()
    Metashape.app.update()

    # export rgb model (mesh)
    chk.exportModel(path=model_rgb_file, save_normals=False, texture_format=Metashape.ImageFormatPNG, save_texture=True,
                    save_uv=True, save_markers=False)

    doc.save()
    # make ortho if needed
    if opt_make_ortho:
        chk.buildOrthomosaic(surface_data=Metashape.ModelData)
        chk.exportRaster(ortho_rgb_file)

def launch_agisoft_reconstruction(img_dir, results_dir, opt_make_ortho = False):
    print('RUNNING AGISOFT RECONSTRUCTION')
    # file names
    model_rgb_file = os.path.join(results_dir, 'texturedMesh.obj')
    if opt_make_ortho:
        ortho_rgb_file = os.path.join(results_dir, 'ortho_rgb.tif')

    # new project
    doc = Metashape.Document()
    doc.save(path=results_dir + "/" + 'agisoft.psx')

    # creating new chunk for RGB
    chk = doc.addChunk()
    chk.label = 'RGB'

    # loading RGB images
    image_list = os.listdir(img_dir)
    photo_list = []
    for photo in image_list:
        photo_list.append("/".join([img_dir, photo]))
    chk.addPhotos(photo_list)

    # proces RGB images
    chk.matchPhotos(guided_matching=True, generic_preselection=False, reference_preselection=False)
    chk.alignCameras()
    chk.buildDepthMaps()
    chk.buildModel(source_data=Metashape.DataSource.DepthMapsData, face_count=Metashape.MediumFaceCount)
    chk.buildUV(mapping_mode=Metashape.GenericMapping)
    chk.buildTexture(texture_size=4096)  # optional argument to change texture size
    Metashape.app.update()

    # export rgb model (mesh)
    chk.exportModel(path=model_rgb_file, save_normals=False, texture_format=Metashape.ImageFormatPNG, save_texture=True, save_uv=True, save_markers=False)

    doc.save()
    # make ortho if needed
    if opt_make_ortho:
        chk.buildOrthomosaic(surface_data=Metashape.ModelData)
        chk.exportRaster(ortho_rgb_file)

    # avoiding bad allocation error


"""
======================================================================================
Optimization functions
======================================================================================
"""

def rotation_workflow(cc_path, obj_path):
    # Sample point cloud on mesh
    (obj_folder, obj_name) = os.path.split(obj_path)
    cc_cloud = '"' + obj_path + '"'
    function_name = 'sample'
    function = ' -NO_TIMESTAMP -C_EXPORT_FMT PLY -SAMPLE_MESH POINTS 100000'

    # Prepare CloudCompare function
    fun_txt = 'SET MY_PATH="' + cc_path + '" \n' + '%MY_PATH% -SILENT -O ' + cc_cloud + function
    win_function(obj_folder, function_name, fun_txt)

    # ransac part
    cloud_path = os.path.join(obj_folder, 'texturedMesh_SAMPLED_POINTS.ply')
    new_folder = os.path.join(obj_folder, 'ransac')
    if not os.path.exists(new_folder):
        os.mkdir(new_folder)
    new_cloud_path = os.path.join(new_folder, 'texturedMesh_SAMPLED_POINTS.ply')
    os.rename(cloud_path, new_cloud_path)

    (cloud_folder, cloud_name) = os.path.split(new_cloud_path)
    cc_cloud = '"' + new_cloud_path + '"'
    function_name = 'sample'
    function = ' -NO_TIMESTAMP -AUTO_SAVE OFF -M_EXPORT_FMT OBJ -SAVE_MESHES -RANSAC OUTPUT_INDIVIDUAL_PRIMITIVES -SAVE_MESHES '

    # Prepare CloudCompare function
    fun_txt = 'SET MY_PATH="' + cc_path + '" \n' + '%MY_PATH% -SILENT -O ' + cc_cloud + function
    win_function(obj_folder, function_name, fun_txt)

    final_plane_file = 'texturedMesh_SAMPLED_POINTS_texturedMesh_SAMPLED_POINTS - Cloud_PLANE_0001.obj'
    final_plane_path = os.path.join(new_folder, final_plane_file)

    rot_txt_path = estimate_rotation(cc_path, final_plane_path)
    rotate_from_matrix(cc_path, obj_path, rot_txt_path)


def estimate_rotation(cc_path, obj_path):
    # File names and paths
    (obj_folder, obj_name) = os.path.split(obj_path)
    cc_cloud = '"' + obj_path + '"'
    function_name = 'fitor'
    function = ' -AUTO_SAVE OFF -NO_TIMESTAMP -SAMPLE_MESH POINTS 1000 -BEST_FIT_PLANE -MAKE_HORIZ'

    # Prepare CloudCompare function
    fun_txt = 'SET MY_PATH="' + cc_path + '" \n' + '%MY_PATH% -SILENT -O ' + cc_cloud + function
    win_function(obj_folder, function_name, fun_txt)

    for file in os.listdir(obj_folder):
        print(file)
        if file.endswith('.txt'):
            txt_path = os.path.join(obj_folder, file)

    txt_path2 = os.path.join(obj_folder, 'rot_matrix.txt')

    # Read rotation
    file1 = open(txt_path, 'r')
    Lines = file1.readlines()

    Lines = Lines[-4:]

    file2 = open(txt_path2, "w")
    for line in Lines:
        file2.write(line)

    return txt_path2

def rotate_from_matrix(cc_path, obj_path, rot_txt_path):
    """
    Function to apply a rotation to a point cloud, using a rotation matrix
    @param obj_path:
    @param rot_matrix: as a numpy array (3,3)
    """
    (cloud_folder, cloud_file) = os.path.split(obj_path)
    cc_cloud = '"' + obj_path + '"'
    # create the text file including the transformation matrix

    cc_txt_path = '"' + rot_txt_path + '"'

    function_name = 'rotated'
    function = ' -APPLY_TRANS ' + str(cc_txt_path)

    # prepare CloudCompare fonction
    fun_txt = 'SET MY_PATH="' + cc_path + '" \n' + '%MY_PATH% -SILENT -NO_TIMESTAMP -M_EXPORT_FMT OBJ -O ' + cc_cloud + function
    win_function(cloud_folder, function_name, fun_txt)


"""
======================================================================================
Generate ortho
======================================================================================
"""

def rot_x_matrix(angle):
    matrix = np.asarray([[1, 0, 0, 0],
                         [0, math.cos(math.radians(angle)), -math.sin(math.radians(angle)), 0],
                         [0, math.sin(math.radians(angle)), math.cos(math.radians(angle)), 0],
                         [0, 0, 0, 1]])
    return matrix


def rot_y_matrix(angle):
    matrix = np.asarray([[math.cos(math.radians(angle)), 0, math.sin(math.radians(angle)), 0],
                         [0, 1, 0, 0],
                         [-math.sin(math.radians(angle)), 0, math.cos(math.radians(angle)), 0],
                         [0, 0, 0, 1]])
    return matrix


def rot_z_matrix(angle):
    matrix = np.asarray([[math.cos(math.radians(angle)), -math.sin(math.radians(angle)), 0, 0],
                         [math.sin(math.radians(angle)), math.cos(math.radians(angle)), 0, 0],
                         [0, 0, 1, 0],
                         [0, 0, 0, 1]])
    return matrix


def front_mat():
    matrix = rot_x_matrix(-90)
    inv_matrix = rot_x_matrix(90)
    return matrix, inv_matrix

def bottom_mat():
    matrix = rot_y_matrix(180)
    inv_matrix = rot_x_matrix(-180)
    return matrix, inv_matrix

def back_mat():
    matrix1 = rot_x_matrix(-90)
    matrix2 = rot_y_matrix(180)
    final_matrix = matrix2 @ matrix1
    inv_matrix1 = rot_y_matrix(-180)
    inv_matrix2 = rot_x_matrix(90)
    final_inv_matrix = inv_matrix2 @ inv_matrix1
    return final_matrix, final_inv_matrix


def right_mat():
    matrix1 = rot_x_matrix(-90)
    matrix2 = rot_y_matrix(-90)
    final_matrix = matrix2 @ matrix1
    inv_matrix1 = rot_y_matrix(90)
    inv_matrix2 = rot_x_matrix(90)
    final_inv_matrix = inv_matrix2 @ inv_matrix1
    return final_matrix, final_inv_matrix


def left_mat():
    matrix1 = rot_x_matrix(-90)
    matrix2 = rot_y_matrix(90)
    final_matrix = matrix2 @ matrix1
    inv_matrix1 = rot_y_matrix(-90)
    inv_matrix2 = rot_x_matrix(90)
    final_inv_matrix = inv_matrix2 @ inv_matrix1
    return final_matrix, final_inv_matrix


def iso2_mat():
    matrix1 = rot_x_matrix(60)
    matrix2 = rot_y_matrix(-20)
    matrix3 = rot_z_matrix(190)
    final_matrix1 = matrix3 @ matrix2
    final_matrix = final_matrix1 @ matrix1
    inv_matrix1 = rot_z_matrix(-190)
    inv_matrix2 = rot_y_matrix(20)
    inv_matrix3 = rot_x_matrix(-60)
    final_inv_matrix1 = inv_matrix3 @ inv_matrix2
    final_inv_matrix = final_inv_matrix1 @ inv_matrix1
    return final_matrix, final_inv_matrix


def iso1_mat():
    matrix1 = rot_x_matrix(-60)
    matrix2 = rot_y_matrix(-20)
    matrix3 = rot_z_matrix(-10)
    final_matrix1 = matrix3 @ matrix2
    final_matrix = final_matrix1 @ matrix1
    inv_matrix1 = rot_z_matrix(10)
    inv_matrix2 = rot_y_matrix(20)
    inv_matrix3 = rot_x_matrix(60)
    final_inv_matrix1 = inv_matrix3 @ inv_matrix2
    final_inv_matrix = final_inv_matrix1 @ inv_matrix1
    return final_matrix, final_inv_matrix


def name_to_matrix(orientation):

    if orientation == 'iso_front':
        trans_init, inv_trans = iso1_mat()
    elif orientation == 'bottom':
        trans_init, inv_trans = bottom_mat()
    elif orientation == 'iso_back':
        trans_init, inv_trans = iso2_mat()
    elif orientation == 'left':
        trans_init, inv_trans = left_mat()
    elif orientation == 'right':
        trans_init, inv_trans = right_mat()
    elif orientation == 'front':
        trans_init, inv_trans = front_mat()
    elif orientation == 'back':
        trans_init, inv_trans = back_mat()

    return trans_init, inv_trans

def basic_vis_creation(obj_load, orientation, p_size=1, back_color=[1, 1, 1]):
    """A function that creates the basic environment for creating things with open3D
            @ parameters :
                pcd_load -- a point cloud loaded into open3D
                orientation -- orientation of the camera; can be 'top', ...
                p_size -- size of points
                back_color -- background color
    """
    if orientation != 'top':
        trans_init, inv_trans = name_to_matrix(orientation)
        obj_load.transform(trans_init)

    vis = visualization.Visualizer()
    vis.create_window(visible=False)
    vis.add_geometry(obj_load)
    opt = vis.get_render_option()
    opt.point_size = p_size
    opt.background_color = np.asarray(back_color)
    ctr = vis.get_view_control()

    return vis, opt, ctr

def rgb2gray(img_rgb):
    return np.dot(img_rgb[..., :3], [0.2989, 0.5870, 0.1140])

def crop_empty_areas(img_path):
    img = imread(img_path)
    gray = rgb2gray(img)
    gray = 255 * (gray < 128).astype(np.uint8)  # To invert the text to white
    coords = findNonZero(gray)  # Find all non-zero points (text)
    x, y, w, h = boundingRect(coords)  # Find minimum spanning bounding box

    crop_img = img[y:y + h, x:x + w]

    imwrite(img_path, crop_img)

def render_ortho_HD(obj_path, output_path, orientation, style='orthogonal', zoom=2):
    """A function to render a point cloud with Open3D engine
        @ parameters :
            pcd_load -- output of the loaf_cloud function
            orientation -- the point of view, choose between iso_front / iso_back / left / right / front / back (str)
            style -- choose between orthogonal or perspective (str)"""

    obj_load = io.read_triangle_mesh(obj_path)
    vis, opt, ctr = basic_vis_creation(obj_load, orientation)

    param = vis.get_view_control().convert_to_pinhole_camera_parameters()
    new_param = param
    ex = new_param.extrinsic.copy()
    ex[2, 3] = ex[2, 3] - zoom

    new_param.extrinsic = ex
    ctr.convert_from_pinhole_camera_parameters(new_param)
    if style == 'orthogonal':
        ctr.change_field_of_view(step=-90)

    vis.poll_events()
    vis.update_renderer()
    time.sleep(1)
    vis.capture_screen_image(output_path, do_render=True)

    # remove white parts

def render_cloud_rgb_ortho_zoom(obj_path, output_path, orientation, zoom, pix_x=1920, pix_y=1055):
    def h_fov(pix_x, pix_y):
        d = pix_y / 2 / math.tan(30 * math.pi / 180)
        x = math.atan(pix_x / 2 / d)
        return x

    def inter(d, fov):
        inter = 2 * d * math.tan(fov) - 2 * center[2] * math.tan(fov)
        return inter

    """def zoom_factor(required_d, inter):
        zoom_factor = inter / (required_d * 2 * math.tan(fov) - 2 * center[2] * math.tan(fov))
        return zoom_factor"""

    def d_at_zoom(fov, inter, zoom):
        d = (inter / zoom + 2 * center[2] * math.tan(fov)) / (2 * math.tan(fov))
        return d

    # basic environment
    obj_load = io.read_triangle_mesh(obj_path, True)

    vis, opt, ctr = basic_vis_creation(obj_load, orientation)

    # Get extrinsic camera parameters
    param = vis.get_view_control().convert_to_pinhole_camera_parameters()
    new_param = param
    ex = new_param.extrinsic.copy()

    bound = obj_load.get_axis_aligned_bounding_box()
    center = bound.get_center()

    fov = h_fov(pix_x, pix_y)
    inter_init = inter(ex[2, 3], fov)
    inter_zoom = inter_init/zoom
    struc = [zoom+1, zoom+1]
    d_zoom = d_at_zoom(fov, inter_zoom, zoom)

    step_h = inter(d_zoom, fov)
    step_v = step_h * pix_y / pix_x
    range_h = step_h * struc[1]
    range_v = step_v * struc[0]

    width = struc[1] * pix_x
    height = struc[0] * pix_y

    #create matrix of the final recomposed image
    final_img = np.zeros((height, width, 3), np.uint8)
    print(final_img.shape)

    for j in range(1, struc[0] + 1):
        for i in range(1, struc[1] + 1):
            if i == 1 and j == 1:
                param = vis.get_view_control().convert_to_pinhole_camera_parameters()
                a = range_h / 2 - step_h / 2
                b = range_v / 2 - step_v / 2
                c = -(ex[2, 3] - d_zoom)
            elif i == 1:
                ctr.convert_from_pinhole_camera_parameters(param)
                a = (struc[1] - 1) * step_h
                b = - step_v
                c = 0
            else:
                ctr.convert_from_pinhole_camera_parameters(param)
                a = - step_h
                b = 0
                c = 0
            new_param = param
            ex = new_param.extrinsic.copy()

            ex[0, 3] += a
            ex[1, 3] += b
            ex[2, 3] += c

            new_param.extrinsic = ex
            ctr.convert_from_pinhole_camera_parameters(new_param)
            ctr.change_field_of_view(step=-90)
            vis.poll_events()
            vis.update_renderer()

            img_name = output_path[:-4] + str(j) + str(i) + '.png'
            vis.capture_screen_image(img_name, True)
            im = imread(img_name)

            start_pixel_h = (i - 1) * pix_x
            stop_pixel_h = start_pixel_h + pix_x
            start_pixel_v = (j - 1) * pix_y
            stop_pixel_v = start_pixel_v + pix_y

            final_img[start_pixel_v:stop_pixel_v, start_pixel_h:stop_pixel_h, :] = im

            # remove_temp_img
            os.remove(img_name)
            imwrite(output_path, final_img)

    # Eliminate white areas


def render_cloud_rgb_simple(obj_path, output_path, orientation):
    """A function to render a point cloud with Open3D engine
        @ parameters :
            pcd_load -- output of the loaf_cloud function
            orientation -- the point of view, choose between iso_front / iso_back / left / right / front / back (str)
            style -- choose between orthogonal or perspective (str)"""
    obj_load = io.read_triangle_mesh(obj_path)
    vis, opt, ctr = basic_vis_creation(obj_load, orientation)

    vis.poll_events()
    vis.update_renderer()
    time.sleep(1)
    vis.capture_screen_image(output_path, do_render=True)

    # remove white parts
    crop_empty_areas(output_path)


"""
======================================================================================
Automatic rotation of image
======================================================================================
"""


def binarizeImage(RGB_image):
    image = rgb2gray(RGB_image)
    threshold = threshold_otsu(image)
    bina_image = image < threshold

    return bina_image


def findEdges(bina_image):
    image_edges = sobel(bina_image)
    return image_edges


def findTiltAngle(image_edges):
    theta_value = np.linspace(-np.pi/2, np.pi/2, num=720)
    h, theta, d = hough_line(image_edges, theta = theta_value)

    accum, angles, dists = hough_line_peaks(h, theta, d)

    angle = np.rad2deg(float(angles[0]))

    if (angle < 0):
        angle = angle + 90
    else:
        angle = angle - 90

    return angle


def rotateImage(RGB_image, angle):
    return rotate(RGB_image, angle)

def image_rotation_workflow(image_path, output_path):
    img_folder, _ = os.path.split(image_path)
    image = io.imread(image_path)
    pixel_x = image.shape[1]
    pixel_y = image.shape[0]

    center_x = int(pixel_x /2)
    center_y = int(pixel_y /2)

    image_crop = image[center_x-650:center_x+650, center_y-650: center_y+650]
    bina_image = binarizeImage(image_crop)

    edge_path = os.path.join(img_folder, 'edges.png')
    image_edges = findEdges(bina_image)
    io.imsave(edge_path, image_edges)
    try:
        angle = findTiltAngle(image_edges)
        print(angle)
        final_img = rotateImage(image, angle)

    except (RuntimeError, TypeError, NameError):
        final_img = image
    final_img = rotateImage(final_img,180)
    io.imsave(output_path, final_img)