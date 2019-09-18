import os
import glob
import socket
import bpy
import shutil
# import pymesh
import numpy as np
import pickle
import importlib.util
spec = importlib.util.spec_from_file_location("cluster_main", "/home/mike/Projects/DIVA/car_models/cluster_main.py")
cluster_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cluster_main)
spec = importlib.util.spec_from_file_location("utils", "/home/mike/Projects/DIVA/car_models/utils.py")
utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utils)

def get_paths(model):
    host = socket.gethostname()
    if host == 'Michaels-MacBook-Pro.local':
        model_file = '/Users/mpeven/Downloads/02958343/{}/models/model_normalized.obj'.format(model)
        clusters_file = '/Users/mpeven/Projects/DIVA/car_models/clusters.pkl'
    elif host == 'titan':
        model_file = '/home/mike/Projects/DIVA/car_models/02958343/{}/models/model_normalized.obj'.format(model)
        clusters_file = '/home/mike/Projects/DIVA/car_models/clusters.pkl'
    else:
        raise ValueError("Unrecognized host: {}".format(host))
    return model_file, clusters_file

def get_vertices(model_file):
    # If pymesh -- pymesh.meshio.load_mesh(model_file).vertices
    vertices = []
    with open(model_file, "r") as f:
        for line in f.readlines():
            if line[:2] == "v ":
                vertices.append(np.array([float(x) for x in line.replace("v ", "").replace("\n", "").split(" ")]))
    return vertices

def import_file(file_name):
    bpy.ops.import_scene.obj(filepath=file_name, use_split_groups=False, use_split_objects=False)
    names = [obj for obj in bpy.context.scene.objects]
    names[0].name = "car_body"
    for obj in bpy.context.scene.objects:
        bpy.context.scene.objects.active = obj
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

def clear_world():
    # Delete all objects and meshes
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    for mes in bpy.data.meshes:
        bpy.data.meshes.remove(mes, do_unlink=True)

def save_out_parts(file, cluter_center_part_vertices, save_path):
    clear_world()
    import_file(file)
    # Save to vertex groups
    for part_type, bbox_dict in cluter_center_part_vertices.items():
        print("Saving {} to a vertex group".format(part_type))
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action='SELECT')
        bbox_max = bbox_dict['bbox_max']
        bbox_min = bbox_dict['bbox_min']
        if "right" in part_type:
            bbox_max[0] += 1
            bbox_max[1] += .02
            bbox_max[2] += .01
            bbox_min[0] -= .02
            bbox_min[1] -= .02
            bbox_min[2] -= .01
        if "left" in part_type:
            bbox_max[0] += .02
            bbox_max[1] += .02
            bbox_max[2] += .01
            bbox_min[0] -= 1
            bbox_min[1] -= .02
            bbox_min[2] -= .01
        if "trunk" in part_type:
            bbox_max[2] += 1
            bbox_max[1] += 1
            bbox_min[2] -= .02
            bbox_min[1] -= .02
        vertices = []
        vert_indices = []
        for vert in bpy.context.active_object.data.vertices:
            vertices.append(np.array([vert.co.x, vert.co.y, vert.co.z]))
            vert_indices.append(vert.index)
        vertices = np.stack(vertices)
        in_bounds = (vertices <= bbox_max) & (vertices >= bbox_min)
        in_bounds_vertex_indices = in_bounds.all(axis=1).nonzero()[0]
        if len(in_bounds_vertex_indices) == 0:
            continue
        vg = bpy.context.active_object.vertex_groups.new(name=part_type)
        vg.add([vert_indices[int(x)] for x in in_bounds_vertex_indices], 1.0, 'ADD')


    # Separate meshes
    bpy.ops.object.mode_set(mode="EDIT")
    for part_type in cluter_center_part_vertices.keys():
        print("Saving {} as its own object".format(part_type))
        if part_type not in [v.name for v in bpy.context.object.vertex_groups]:
            continue
        bpy.ops.object.vertex_group_set_active(group=part_type)
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_select()
        names = [obj.name for obj in bpy.context.scene.objects]
        try:
            bpy.ops.mesh.separate(type='SELECTED')
        except Exception:
            continue
        new_objs = [obj for obj in bpy.context.scene.objects if obj.name not in names]
        new_objs[0].name = part_type

    # Save meshes to obj files
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.select_all(action='DESELECT')
    for item in bpy.context.selectable_objects:
        item.select = False
    for ob in bpy.context.scene.objects:
        bpy.context.scene.objects.active = ob
        print("Saving {} as an obj file".format(ob.name))
        ob.select = True
        if ob.type != 'MESH':
            continue
        file_name = save_path + "_{}.obj".format(ob.name)
        bpy.ops.export_scene.obj(filepath=file_name, use_selection=True, check_existing=False)
        ob.select = False
        bpy.data.objects.remove(bpy.data.objects[ob.name], True)

def main():
    if os.path.isdir("./car_models_auto_annotated"):
        shutil.rmtree("./car_models_auto_annotated")
    os.mkdir("car_models_auto_annotated")
    parts = ["front_right", "front_left", "back_right", "back_left", "trunk"]

    # Annotate
    to_annotate = cluster_main.get_models_to_annotate()
    i = 0
    total_models = sum([len(x) for x in to_annotate.values()])
    for cluster_center, cluster_models in to_annotate.items():
        print("Using annotations from model {}".format(cluster_center))

        # Unannotated model loop
        for model in cluster_models:
            print("\n\nAnnotating {}/{}.".format(i, total_models))
            unannotated_mesh_file = get_paths(model)[0]
            part_boxes = {}
            for part in parts:
                mesh_file = "car_models_hand_annotated/{}_{}.obj".format(cluster_center, part)
                if not os.path.isfile(mesh_file):
                    continue
                cluster_center_vertices = get_vertices(mesh_file)
                bbox_max = np.amax(cluster_center_vertices, 0)
                bbox_min = np.amin(cluster_center_vertices, 0)
                part_boxes[part] = {'bbox_max': bbox_max, 'bbox_min': bbox_min}
            save_path = "car_models_auto_annotated/{}".format(model)
            save_out_parts(unannotated_mesh_file, part_boxes, save_path)
            i += 1
    utils.correct_texture_paths("car_models_auto_annotated")
    utils.add_metadata("car_models_auto_annotated")
    utils.remove_faceless_models("car_models_auto_annotated")



if __name__ == '__main__':
    main()
