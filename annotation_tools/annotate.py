'''
INSTRUCTIONS
------------
Run this in commandline:

blender --python annotate.py -- shapenet_model_number annotate object


Need to install pandas first
----------------------------
cd /path/to/blender/python
rm -rf ./lib/python3.7/site-packages/numpy
./python -m ensurepip
./python -m pip install pandas
'''

import os
import sys
import argparse
import socket
import time
import pandas as pd
import bpy

test_items = [
    ("front_right", "Front Right Door", "", 1),
    ("front_left", "Front Left Door", "", 2),
    ("back_right", "Back Right Door", "", 3),
    ("back_left", "Back Left Door", "", 4),
    ("trunk", "Trunk", "", 5),
    ("to_delete", "Delete", "", 6),
]

def import_file(file_name, separate_objects):
    print("Running import_file(file_name={}, separate_objects={})".format(file_name, separate_objects))
    bpy.ops.import_scene.obj(filepath=file_name, use_split_groups=separate_objects, use_split_objects=separate_objects)

    # Rename to "car body" if importing as one object
    if separate_objects == False:
        names = [obj for obj in bpy.context.scene.objects]
        names[0].name = "car_body"
    for obj in bpy.context.scene.objects:
        bpy.context.scene.objects.active = obj
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')


def clear_world():
    print("Running clear_world")
    # Delete all objects and meshes
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    for mes in bpy.data.meshes:
        bpy.data.meshes.remove(mes, do_unlink=True)


def set_mode_for_selecting(object_mode):
    print("Running set_mode_for_selecting")
    for obj in bpy.context.scene.objects:
        bpy.context.scene.objects.active = obj
    if not object_mode:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')
    else:
        bpy.ops.object.select_all(action='DESELECT')


def save_selected_objects_to_csv(part_type, save_path):
    print("Running save_selected_objects_to_csv")
    vert_dicts = []
    for obj in bpy.context.selected_objects:
        vert_dicts.append({
            'part_type': part_type,
            'object_name': obj.name,
        })
    print(vert_dicts)
    df = pd.DataFrame(vert_dicts)
    if os.path.isfile(save_path):
        df = pd.concat([pd.read_csv(save_path), df])
    df = df.drop_duplicates()
    df = df.sort_values(["part_type", "object_name"])
    df.to_csv(save_path, index=False)


def remove_selected_objects_from_csv(part_type, save_path):
    print("Running remove_selected_objects_from_csv")
    df = pd.read_csv(save_path)
    df = df[~((df['part_type'] == part_type) & (df['object_name'].isin([obj.name for obj in bpy.context.selected_objects])))]
    df.to_csv(save_path, index=False)


def toggle_hide_objects_from_csv(part_type, save_path):
    print("Running toggle_hide_objects_from_csv")
    if not os.path.isfile(save_path):
        return
    df = pd.read_csv(save_path)
    object_names = list(df[df['part_type'] == part_type]['object_name'].values)
    to_hide = False
    for object_name in object_names:
        if bpy.data.objects[object_name].hide == False:
            to_hide = True
    for object_name in object_names:
        bpy.data.objects[object_name].hide = to_hide
        bpy.data.objects[object_name].select = True


def save_parts_to_obj_files(save_location, object_annotation_csv):
    print("Running save_parts_to_obj_files")
    if not os.path.isfile(object_annotation_csv):
        return
    df = pd.read_csv(object_annotation_csv)
    part_types = list(df['part_type'].unique())
    for part_type in part_types:
        bpy.ops.object.select_all(action='DESELECT')
        object_names = list(df[df['part_type'] == part_type]['object_name'].values)
        for object_name in object_names:
            bpy.data.objects[object_name].select = True
        if part_type == "to_delete":
            bpy.ops.object.delete()
            continue
        file_name = save_location.replace("part_type", part_type)
        bpy.ops.export_scene.obj(filepath=file_name, use_selection=True, check_existing=False)
        bpy.ops.object.delete()
    file_name = save_location.replace("part_type", "car_body")
    bpy.ops.export_scene.obj(filepath=file_name)


def get_selected_vertices():
    print("Running get_selected_vertices")
    current_mode = bpy.context.active_object.mode
    bpy.ops.object.mode_set(mode='OBJECT')
    selected_verts = [v for v in bpy.context.active_object.data.vertices if v.select]
    bpy.ops.object.mode_set(mode=current_mode)
    print("Found {} selected vertices on 'model_normalized'".format(len(selected_verts)))
    return selected_verts


def select_vertices_from_list(list_of_verts):
    print("Running select_vertices_from_list")
    bpy.ops.object.mode_set(mode="OBJECT")
    obj = bpy.context.active_object
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_mode(type="VERT")

    # bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    for vert in list_of_verts:
        obj.data.vertices[vert].select = True
    bpy.ops.object.mode_set(mode="EDIT")


def hide_selected_vertices():
    print("Running hide_selected_vertices")
    current_mode = bpy.context.active_object.mode
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.hide(unselected=False)
    bpy.ops.object.mode_set(mode=current_mode)


def save_selected_vertices(verts, part_type, save_path):
    print("Running save_selected_vertices")
    vert_dicts = []
    for vert in verts:
        print(vert)
        vert_dicts.append({
            'part_type': part_type,
            'vert_index': vert.index,
        })
    df = pd.DataFrame(vert_dicts)
    if os.path.isfile(save_path):
        df = pd.concat([pd.read_csv(save_path), df])
    df = df.drop_duplicates()
    df = df.sort_values(["part_type", "vert_index"])
    df.to_csv(save_path, index=False)


def save_vertices_to_obj_files(save_location, vert_csv_path, coords={}):
    if not os.path.isfile(vert_csv_path):
        return
    part_types = [x[0] for x in test_items]
    # Save to vertex groups
    for part_type in part_types:
        print("Saving {} to a vertex group".format(part_type))
        # Check for coordinates (happens when objects already removed)
        if part_type in coords:
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action='SELECT')
            for vert in bpy.context.active_object.data.vertices:
                coord_tup = (
                    vert.co.x,
                    vert.co.y,
                    vert.co.z,
                    vert.normal.x,
                    vert.normal.y,
                    vert.normal.z,
                )
                if coord_tup in coords[part_type]:
                    verts.append(vert.index)
        else:
            verts = get_verts_from_csv(part_type, vert_csv_path)
            print("Found these verts in csv for {}: {}".format(part_type, verts))
        if len(verts) == 0:
            continue
        vg = bpy.context.active_object.vertex_groups.new(name=part_type)
        bpy.ops.object.mode_set(mode="OBJECT")
        vg.add(verts, 1.0, 'ADD')
        bpy.ops.object.mode_set(mode="EDIT")

    # Separate meshes
    for part_type in part_types:
        print("Saving {} as its own object".format(part_type))
        if part_type not in [v.name for v in bpy.context.object.vertex_groups]:
            continue
        bpy.ops.object.vertex_group_set_active(group=part_type)
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_select()
        names = [obj.name for obj in bpy.context.scene.objects]
        bpy.ops.mesh.separate(type='SELECTED')
        new_objs = [obj for obj in bpy.context.scene.objects if obj.name not in names]
        new_objs[0].name = part_type

    # Save meshes to obj files
    set_mode_for_selecting(False)
    for item in bpy.context.selectable_objects:
        item.select = False
    for ob in bpy.context.scene.objects:
        bpy.context.scene.objects.active = ob
        print("Saving {} as an obj file".format(ob.name))
        ob.select = True
        if ob.type != 'MESH':
            continue
        file_name = save_location.replace("part_type", ob.name)
        bpy.ops.export_scene.obj(filepath=file_name, use_selection=True, check_existing=False)
        ob.select = False
        bpy.data.objects.remove(bpy.data.objects[ob.name], True)


def remove_selected_vertices(verts, part_type, save_path):
    print("Running remove_selected_vertices")
    if not os.path.isfile(save_path):
        return
    df = pd.read_csv(save_path)
    df = df[~((df['part_type'] == part_type) & (df['vert_index'].isin([v.index for v in verts])))]
    df.to_csv(save_path, index=False)


def get_verts_from_csv(part_type, save_path):
    print("Running get_verts_from_csv")
    df = pd.read_csv(save_path)
    verts = [int(x) for x in df[df['part_type'] == part_type]['vert_index'].values]
    print("Found {} {} vertices in {}".format(len(verts), part_type, save_path))
    return verts


def get_vertex_coordinates(vertex_csv):
    print("Running get_vertex_coordinates")
    df = pd.read_csv(vertex_csv)
    bpy.ops.object.mode_set(mode='OBJECT')
    coords = {}
    for part_type in df['part_type'].unique():
        coords[part_type] = []
        vert_indices = [int(x) for x in df[df['part_type'] == part_type]['vert_index'].values]
        for vert in bpy.context.active_object.data.vertices:
            if vert.index in vert_indices:
                coords[part_type].append((
                    vert.co.x,
                    vert.co.y,
                    vert.co.z,
                    vert.normal.x,
                    vert.normal.y,
                    vert.normal.z,
                ))
    return coords


class VertexAnnotationSaverPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "mesh_edit"
    bl_category = "Tools"
    bl_label = "Vertex Annotation Tool"

    def draw(self, context):
        TheCol = self.layout.column(align=True)
        TheCol.prop(context.scene, "part_type")
        TheCol.operator("mesh.save_verts", text="Save selected to csv")
        TheCol.operator("mesh.remove_verts", text="Remove selected from csv")
        TheCol.operator("mesh.hide_verts", text="Hide vertices")
        TheCol.operator("mesh.unhide_verts", text="Unhide all vertices")

class ObjectAnnotationSaverPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "Tools"
    bl_label = "Object Annotation Tool"

    def draw(self, context):
        TheCol = self.layout.column(align=True)
        TheCol.prop(context.scene, "part_type")
        TheCol.operator("object.save_verts", text="Save selected to csv")
        TheCol.operator("object.remove_verts", text="Remove selected from csv")
        TheCol.operator("object.toggle_hide_objects", text="Toggle hide objects from csv")

class ObjectSaveSelected(bpy.types.Operator):
    bl_idname = "object.save_verts"
    bl_label = "Save Vertices from object"
    bl_options = {"UNDO"}
    def invoke(self, context, event):
        verts = save_selected_objects_to_csv(context.scene.part_type, context.scene.annot_object_loc)
        return {"FINISHED"}

class ObjectRemoveSelected(bpy.types.Operator):
    bl_idname = "object.remove_verts"
    bl_label = "Remove Vertices from object"
    bl_options = {"UNDO"}
    def invoke(self, context, event):
        verts = remove_selected_objects_from_csv(context.scene.part_type, context.scene.annot_object_loc)
        return {"FINISHED"}

class ObjectShowObjects(bpy.types.Operator):
    bl_idname = "object.toggle_hide_objects"
    bl_label = "Show objects"
    bl_options = {"UNDO"}
    def invoke(self, context, event):
        toggle_hide_objects_from_csv(context.scene.part_type, context.scene.annot_object_loc)
        return {"FINISHED"}

class VertexSaveSelected(bpy.types.Operator):
    bl_idname = "mesh.save_verts"
    bl_label = "Save Vertices"
    bl_options = {"UNDO"}
    def invoke(self, context, event):
        verts = get_selected_vertices()
        save_selected_vertices(verts, context.scene.part_type, context.scene.annot_loc)
        return {"FINISHED"}

class RemoveSelected(bpy.types.Operator):
    bl_idname = "mesh.remove_verts"
    bl_label = "Remove Vertices"
    bl_options = {"UNDO"}
    def invoke(self, context, event):
        verts = get_selected_vertices()
        remove_selected_vertices(verts, context.scene.part_type, context.scene.annot_loc)
        set_mode_for_selecting(False)
        return {"FINISHED"}

class HideVerticesFromCSV(bpy.types.Operator):
    bl_idname = "mesh.hide_verts"
    bl_label = "Hide"
    bl_options = {"UNDO"}
    def invoke(self, context, event):
        verts = get_verts_from_csv(context.scene.part_type, context.scene.annot_loc)
        select_vertices_from_list(verts)
        hide_selected_vertices()
        return {"FINISHED"}

class UnhideAll(bpy.types.Operator):
    bl_idname = "mesh.unhide_verts"
    bl_label = "Unhide"
    bl_options = {"UNDO"}
    def invoke(self, context, event):
        bpy.ops.mesh.reveal()
        return {"FINISHED"}

def register(annot_file, annot_object_file):
    # Vertex annotater
    bpy.utils.register_class(VertexAnnotationSaverPanel)
    bpy.utils.register_class(VertexSaveSelected)
    bpy.utils.register_class(RemoveSelected)
    bpy.utils.register_class(HideVerticesFromCSV)
    bpy.utils.register_class(UnhideAll)
    # Object annotater
    bpy.utils.register_class(ObjectAnnotationSaverPanel)
    bpy.utils.register_class(ObjectSaveSelected)
    bpy.utils.register_class(ObjectRemoveSelected)
    bpy.utils.register_class(ObjectShowObjects)
    # Keymapping
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')
    kmi = km.keymap_items.new(ObjectSaveSelected.bl_idname, 'S', 'PRESS', ctrl=False, shift=False)
    km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')
    kmi = km.keymap_items.new(ObjectRemoveSelected.bl_idname, 'R', 'PRESS', ctrl=False, shift=False)
    km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')
    kmi = km.keymap_items.new(ObjectShowObjects.bl_idname, 'H', 'PRESS', ctrl=False, shift=False)

    bpy.types.Scene.part_type = bpy.props.EnumProperty(name="Part Type", items=test_items)
    bpy.types.Scene.annot_loc = bpy.props.StringProperty(name="Annot loc", default=annot_file)
    bpy.types.Scene.annot_object_loc = bpy.props.StringProperty(name="Annot object loc", default=annot_object_file)

def get_file_locations(model):
    host = socket.gethostname()
    if host == 'Michaels-MacBook-Pro.local':
        model_file = '/Users/mpeven/Downloads/02958343/{}/models/model_normalized.obj'.format(model)
        vert_annot_file = '/Users/mpeven/Projects/DIVA/car_models/annotations/{}.csv'.format(model)
        object_annot_file = vert_annot_file.replace('.csv', '_objects.csv')
    elif host == 'titan':
        model_file = '/home/mike/Projects/DIVA/car_models/02958343/{}/models/model_normalized.obj'.format(model)
        vert_annot_file = '/home/mike/Projects/DIVA/car_models/annotations/{}.csv'.format(model)
        object_annot_file = vert_annot_file.replace('.csv', '_objects.csv')
    else:
        raise ValueError("Unrecognized host: {}".format(host))

    return model_file, vert_annot_file, object_annot_file

def main(model_name, annotate_mode, object_mode, save_folder):
    model_file, vert_annot_file, object_annot_file = get_file_locations(model_name)

    clear_world()

    # Either prepare for annotations or save out file
    if annotate_mode:
        import_file(model_file, separate_objects=object_mode)
        set_mode_for_selecting(object_mode)
        register(vert_annot_file, object_annot_file)
    else:
        save_location = "{}/{}_part_type.obj".format(save_folder, model_name)
        if os.path.isfile(object_annot_file) and not os.path.isfile(vert_annot_file):
            import_file(model_file, separate_objects=True)
            save_parts_to_obj_files(save_location, object_annot_file)
        elif os.path.isfile(vert_annot_file) and not os.path.isfile(object_annot_file):
            import_file(model_file, separate_objects=False)
            save_vertices_to_obj_files(save_location, vert_annot_file)
        elif os.path.isfile(object_annot_file) and os.path.isfile(vert_annot_file):
            # If both:
            # 1 - Get locations of vertices from vert_annot_file.
            # 2 - Remove parts to own obj files from object_annot_file.
            # 3 - Load up the rest of the model without objects.
            # 4 - Select the verteces based on location.
            # 5 - Remove to their own file.
            import_file(model_file, separate_objects=False)
            coords = get_vertex_coordinates(vert_annot_file)
            clear_world()
            import_file(model_file, separate_objects=True)
            save_parts_to_obj_files(save_location, object_annot_file)
            car_body_file = vert_annot_file.replace(".csv", "/car_body.obj")
            clear_world()
            import_file(car_body_file, separate_objects=False)
            save_vertices_to_obj_files(save_location, vert_annot_file, coords)
        else:
            print("No annotations for {}, can't do anything".format(model_name))

def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

if __name__ == '__main__':
    argv = sys.argv[sys.argv.index("--") + 1:]
    parser = argparse.ArgumentParser(description='Annotate ShapeNet models with Blender.')
    parser.add_argument('-m', '--shapenet_model_id', type=str, help='Name of the shapenet model')
    parser.add_argument('-o', '--object_mode', type=str2bool, nargs='?', const=True, default=True,
        help='Whether to load obj file with objects intact (alternative is model of only vertices)')
    parser.add_argument('-a', '--annotate_mode', type=str2bool, nargs='?', const=True, default=True,
        help='Loads up blender ready for annotations, rather than just saving out objs from annotations')
    parser.add_argument('-s', '--save_folder', type=str, help='Name of the folder to save the objs', default="car_models_hand_annotated")
    args = parser.parse_args(argv)
    main(args.shapenet_model_id, args.annotate_mode, args.object_mode, args.save_folder)
