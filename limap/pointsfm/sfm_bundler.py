from _limap import _base, _pointsfm

import os
import numpy as np
import cv2
from tqdm import tqdm
import pdb

def ReadModelBundler(bundler_path, list_path, model_path, max_image_dim=None):
    ################################
    # read imname_list
    ################################
    list_path = os.path.join(bundler_path, list_path)
    print("Loading bundler list file {0}...".format(list_path))
    with open(list_path, 'r') as f:
        lines = f.readlines()
    image_names = [line.strip('\n').split(' ')[0] for line in lines]
    imname_list = [os.path.join(bundler_path, img_name) for img_name in image_names]

    ################################
    # read sfm model
    ################################
    model_path = os.path.join(bundler_path, model_path)
    print("Loading bundler model file {0}...".format(model_path))
    with open(model_path, 'r') as f:
        lines = f.readlines()
    counter = 1 # start from the second line
    line = lines[counter].strip('\n').split(' ')
    n_images, n_points = int(line[0]), int(line[1])
    counter += 1

    # construct SfmModel instance
    camviews = []
    model = _pointsfm.SfmModel()
    # read camviews
    for image_id in tqdm(range(n_images)):
        # read camera
        line = lines[counter].strip('\n').split(' ')
        f, k1, k2 = float(line[0]), float(line[1]), float(line[2])
        counter += 1
        img_hw = cv2.imread(imname_list[image_id]).shape[:2]
        K = np.zeros((3, 3))
        cx = img_hw[1] / 2.0
        cy = img_hw[0] / 2.0
        params = [f, cx, cy, k1, k2]
        camera = _base.Camera("RADIAL", params, cam_id=image_id, hw=img_hw)
        # read pose
        R = np.zeros((3, 3))
        for row_id in range(3):
            line = lines[counter].strip('\n').split(' ')
            R[row_id, 0], R[row_id, 1], R[row_id, 2] = float(line[0]), float(line[1]), float(line[2])
            counter += 1
        R[1,:] = -R[1,:] # for bundler format
        R[2,:] = -R[2,:] # for bundler format
        T = np.zeros((3))
        line = lines[counter].strip('\n').split(' ')
        T[0], T[1], T[2] = float(line[0]), float(line[1]), float(line[2])
        T[1:] = -T[1:] # for bundler format
        counter += 1
        pose = _base.CameraPose(R, T)
        camview = _base.CameraView(cam, pose)
        camviews.append(camview)
        # add image
        image = _pointsfm.SfmImage(imname_list[image_id], img_hw[1], img_hw[0], camview.K().reshape(-1).tolist(), camview.R().reshape(-1).tolist(), camview.T().tolist())
        model.addImage(image)

    # read points
    for point_id in tqdm(range(n_points)):
        line = lines[counter].strip('\n').split(' ')
        x, y, z = float(line[0]), float(line[1]), float(line[2])
        counter += 1
        counter += 1 # skip color
        line = lines[counter].strip('\n').split(' ')
        n_views = int(line[0])
        subcounter = 1
        track = []
        for view_id in range(n_views):
            track.append(int(line[subcounter]))
            subcounter += 4
        model.addPoint(x, y, z, track)
        counter += 1
    return model, imname_list, camviews

