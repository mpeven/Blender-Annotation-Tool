import os
# import pymesh
import glob
import subprocess
import numpy as np
import shutil
import json
from tqdm import tqdm

def create_ply_files():
    root_dir = './02958343'
    os.makedirs('ply_files', exist_ok=True)
    for model_dir in sorted(glob.glob(root_dir + "/*")):
        model_name = os.path.basename(model_dir)
        model_file_obj = model_dir + "/models/model_normalized.obj"
        if not os.path.isfile(model_file_obj):
            continue
        model_file_ply = 'ply_files/{}.ply'.format(model_name)
        mesh = pymesh.load_mesh(model_file_obj)
        pymesh.save_mesh(model_file_ply, mesh, use_float=True)

def is_relative(im_path):
    if "/home/mike/Projects/DIVA/car_models/02958343" in im_path:
        return False
    if "/Users/mpeven/Downloads/02958343" in im_path:
        return False
    if im_path[:2] == "./":
        return True
    return False

def correct_texture_paths(folder):
    '''
    Updates all materials and textures to have unique names
    Change the texture path in the mtl files to be relative
    Copies the texture files over to the new relative location
    '''

    # Edit the materials in the obj files
    for object_file in tqdm(glob.glob("{}/*.obj".format(folder)), ncols=100, desc="updating obj files"):
        model_name = object_file.split("/")[-1].split("_")[0]
        lines = [l for l in open(object_file, 'r')]
        for i, l in enumerate(lines):
            words = l.replace('\n','').split(' ')

            # Change the material name
            if words[0] == 'usemtl':
                if model_name not in words[1]:
                    lines[i] = l.replace(words[1], model_name + "_" + words[1])

        with open(object_file, 'w') as f:
            f.writelines(lines)

    # Create path for texture ims
    texture_dir = "{}/textures".format(folder)
    if os.path.isdir(texture_dir):
        shutil.rmtree(texture_dir)
    else:
        os.makedirs(texture_dir)

    # Edit the materials and image paths in the mtl files
    for texture_file in tqdm(glob.glob("{}/*.mtl".format(folder)), ncols=100, desc="updating mtl files"):
        model_name = texture_file.split("/")[-1].split("_")[0]
        lines = [l for l in open(texture_file, 'r')]

        # Edit path
        # Options:
        # 1 - map_Kd /full/path/to/im/file.jpg
        # 2 - map_Kd relative/path/from/mtlfile.jpg
        for i, l in enumerate(lines):
            words = l.replace('\n','').split(' ')

            # Change the material name
            if words[0] == 'newmtl':
                if model_name not in words[1]:
                    lines[i] = l.replace(words[1], model_name + "_" + words[1])

            # Change the texture image path
            if 'map_' in words[0]:
                im_path_full = words[1]
                new_im_path = "./textures/{}_{}".format(model_name, os.path.basename(im_path_full))

                # Change path to make sure it exists
                if not os.path.isfile(im_path_full):
                    im_path_guesses = [
                        "/home/mike/Projects/DIVA/car_models/02958343/{}/{}".format(model_name, im_path_full),
                        "/home/mike/Projects/DIVA/car_models/02958343/{}/{}".format(model_name, im_path_full).replace(".jpg", ".JPG"),
                        "/home/mike/Projects/DIVA/car_models/02958343/{}/{}".format(model_name, im_path_full).replace(".JPG", ".jpg")
                    ]
                    for im_path_guess in im_path_guesses:
                        if os.path.isfile(im_path_guess):
                            print("Changing {} to {}".format(im_path_full, im_path_guess))
                            im_path_full = im_path_guess
                            break
                if not os.path.isfile(im_path_full):
                    print(texture_file)
                    print("No file at {}".format(im_path_full))
                    exit()

                # Copy file over
                shutil.copyfile(im_path_full, "{}/{}_{}".format(texture_dir, model_name, os.path.basename(im_path_full)))
                lines[i] = l.replace(im_path_full, new_im_path)

        # Edit texture file
        with open(texture_file, 'w') as f:
            f.writelines(lines)

def check_texture_paths(folder):
    for texture_file in glob.glob("{}/*.mtl".format(folder)):
        lines = [l for l in open(texture_file, 'r')]
        for i, l in enumerate(lines):
            words = l.replace('\n','').split(' ')
            if not (words[0] == 'map_Kd' or words[0] == 'map_d'):
                continue
            if not os.path.isfile(words[1]):
                print("No file at {}".format(words[1]))
            if "DIVA" in words[1]:
                print("Not relative at {}".format(words[1]))

def add_metadata(folder):
    import cluster_on_text
    for c in cluster_on_text.cluster():
        if 'pickup' in c['name']:
            pickup_models = c['models']
    pickup_models.append('12f2905dc029f59a2479fbc7da5ed22b')

    models_annotated = set(x.split("/")[-1].split("_")[0] for x in glob.glob(folder + "/*") if os.path.isfile(x))
    for model_name in tqdm(models_annotated, desc="Adding metadata", ncols=100):
        json_dict = {}
        for part_file in glob.glob("{}/{}*.obj".format(folder, model_name)):
            # print(part_file)
            part = os.path.basename(part_file).replace(".obj", "").replace(model_name + "_", "")
            vertices = []
            with open(part_file, "r") as f:
                for line in f.readlines():
                    if line[:2] == "v ":
                        vertices.append(np.array([float(x) for x in line.replace("v ", "").replace("\n", "").split(" ")]))
            if len(vertices) == 0:
                continue
            vertices = np.stack(vertices)
            # print("min z (front of car): ", vertices[np.argmin(vertices[:,2])])
            # print("median y (up and down): ", np.median(vertices[:,1]))
            max_z = np.max(vertices[:,2])
            min_z = np.min(vertices[:,2])
            max_y = np.max(vertices[:,1])
            min_y = np.min(vertices[:,1])
            median_y = np.median(vertices[:,1])
            median_x = np.median(vertices[:,0])
            if part == "trunk" and model_name not in pickup_models:
                best_point = np.argmin(np.sum(np.abs(vertices[:,:] - np.array([median_x, max_y, min_z])), 1))
                rotation = [1, 0, 0]
            elif part == "trunk" and model_name in pickup_models:
                best_point = np.argmin(np.sum(np.abs(vertices[:,:] - np.array([median_x, min_y, min_z])), 1))
                rotation = [-1, 0, 0]
            elif part == "car_body":
                continue
            else:
                best_point = np.argmin(np.sum(np.abs(vertices[:,:] - np.array([median_x, median_y, min_z])), 1))
                if 'right' in part:
                    rotation = [0, 0, -1]
                elif 'left' in part:
                    rotation = [0, 0, 1]
                else:
                    raise ValueError("Don't know part {}".format(part))
            json_dict[part] = {
                'hinge_x': vertices[best_point][0],
                'hinge_y': -vertices[best_point][2],
                'hinge_z': vertices[best_point][1],
                'rotation': rotation,
            }
        with open("{}/{}_metadata.json".format(folder, model_name), 'w') as fp:
            json.dump(json_dict, fp)

def remove_faceless_models(folder):
    for obj_file in glob.glob("{}/*.obj".format(folder)):
        has_face = False
        lines = [l for l in open(obj_file, 'r')]
        for i, l in enumerate(lines):
            words = l.replace('\n','').split(' ')
            if words[0] == 'f':
                has_face = True
                break
        if not has_face:
            print("Removing {}".format(obj_file))
            os.remove(obj_file)
            os.remove(obj_file.replace(".obj", ".mtl"))


if __name__ == '__main__':
    # correct_texture_paths("car_models_hand_annotated")
    remove_faceless_models("car_models_auto_annotated")
