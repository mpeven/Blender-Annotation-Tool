import os
import shutil
import glob
import subprocess
import utils

def main():
    folder = "car_models_hand_annotated"
    remove_all_files(folder)
    save_out_annotations(folder)
    utils.correct_texture_paths(folder)
    utils.add_metadata(folder)

def remove_all_files(folder):
    if os.path.isdir(folder):
        shutil.rmtree(folder)
    os.mkdir(folder)

def save_out_annotations(save_folder):
    models_annotated = set(x.split("_")[0].split(".csv")[0].replace("annotations/", "") for x in glob.glob("annotations/*.csv"))
    print(models_annotated)
    for model in models_annotated:
        cmd = 'blender --background --python annotate_with_blender.py -- -m {} -a N -o N -s {}'.format(model, save_folder)
        subprocess.call(cmd, shell=True)

if __name__ == '__main__':
    main()
