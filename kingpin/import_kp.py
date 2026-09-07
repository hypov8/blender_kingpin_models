"""
kingpin model import. mdx/md2
"""

# import time
import numpy as np
import struct
import os
import bpy
# from timeit import default_timer as time
from bpy.props import (
    BoolProperty,
    EnumProperty,
)
from bpy.types import Operator, PropertyGroup
from bpy_extras.io_utils import ImportHelper
# from bpy_extras.io_utils import unpack_list
from bpy_extras.image_utils import load_image
from mathutils import Vector
from . pcx_file import read_pcx_file
from . import common_kp as kpc
from . import bl_info  # version


# -|GUI|- import Properties
class KINGPIN_Import_props(PropertyGroup):
    """ _ """
    ui_opt_store_pcx = BoolProperty(
        name="Store .pcx Internaly",
        description=(
            "Store .pcx file data into the blend file, so it can be loaded later\n" +
            "Note: you will need to manualy remove data later if unused"
        ),
        default=True,
    )
    ui_opt_anim = BoolProperty(
        name="Import Animations",
        description="Import animation frame data",
        default=True,
    )

    type_list = [
        (kpc.SK_MODE_VERT , "1.Vertex Keys", #"SK_VERTEX"
            "Animate using vertex data", 1),
        (kpc.SK_MODE_ABS, "2.Shape Key (absolute)", #"SK_ABS"
            "Use action graph for animations", 2),
        (kpc.SK_MODE_REL, "3.Shape Keys (Relative)", #"SK_MULTI"
            "Add shape key\'s for every frame.\n" +
            "Import speed is faster, but mesh is harder to edit.\n" +
            "Note: this is the old plugin method", 3)
    ]
    # ("NONE", "None", "No animations", 0),  # force no animation
    # ("SK_SINGLE", "Shape Keys (Single)", "Animate using only 1 shape key", 3),
    ui_opt_anim_type = EnumProperty(
        name="Type",
        description="Import all frames",
        items=type_list,
        default=kpc.SK_MODE_VERT,
    )
    ui_opt_frame_names = BoolProperty(
        name="Import Frame Names",
        description=(
            "Import animation frame names to time line\n" +
            "WARNING: Removes all existing marker frame names"
        ),
        default=False,
    )
    ui_opt_dupe_mat = BoolProperty(
        name="Use Existing Material",
        description="If material name exists, model will use the existing material",
        default=True,
    )

    # TODO SK_ABS Interpolation
    # ui_opt_sk_types = EnumProperty(
    #     name="key type",
    #     description="Import all frames",
    #     items=(
    #         ("NONE", "None", "", 0),
    #         ("KEY_LINEAR", "Linear", "", 1),
    #         ("KEY_CARDINAL", "Cardinal", "", 2),
    #         ("KEY_CATMULL_ROM", "Catmull-Rom", "", 3),
    #         ("KEY_BSPLINE", "BSpline", "", 4),
    #     ),
    #     default="NONE",
    # )

    ui_opt_mesh_cleanup = BoolProperty(
        name="Mesh Cleanup",
        description=(
            "Use blenders internal mesh cleanup.\n"
            "Note: disable if mesh is missing faces/vertex"
        ),
        default=True,
    )
    ui_opt_weld_verts = BoolProperty(
        name="Weld Vertex",
        description=(
            "Welds vertex that share the same location.\n"
            "CAUTION: a vertex with 3+ faces, like thugs knee, will becme corrupt"
        ),
        default=False,
    )


class KINGPIN_Import_Button(Operator, kpc.KINGPIN_FileSelect_md2_Params):
    """ Import selection to Kingpin file format (md2/mdx) """
    bl_idname = "kp.import_model_button"
    bl_label = "Import md2/mdx"
    bl_options = {'REGISTER'}
    bl_description = "Import selection to Kingpin file format (md2/mdx)"
    filename_ext = {".mdx", ".md2"}  # md2 used later
    check_extension = True

    def execute(self, context):
        # kp_import_ = context.window_manager.kp_import_
        user_prefs = kpc.get_addon_preferences()
        if user_prefs:
            if user_prefs.pref_kp_import_button_use_dialog:
                self.filepath = ""
            else:
                self.filepath = ""

        execute_import(self, context)
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


def draw_import(self, context):
    """ draw input gui """
    ui_import_ = context.window_manager.kp_import_

    layout = self.layout

    # general options
    box1 = layout.box()
    row = box1.column_flow(columns=1, align=True)
    row.prop(ui_import_, "ui_opt_dupe_mat")
    row.prop(ui_import_, "ui_opt_store_pcx")
    row.prop(ui_import_, "ui_opt_mesh_cleanup")
    row.prop(ui_import_, "ui_opt_weld_verts")

    # animation options
    box2 = layout.box()
    row1 = box2.column_flow(columns=1, align=True)
    row1.prop(ui_import_, "ui_opt_anim")
    row2 = box2.column_flow(columns=1, align=True)
    row2.enabled = ui_import_.ui_opt_anim
    row2.prop(ui_import_, "ui_opt_anim_type")
    # sub.prop(ui_import_, "ui_opt_sk_types")
    # show "frame name" option when importing animation
    row2.prop(ui_import_, "ui_opt_frame_names")
    if ui_import_.ui_opt_frame_names:
        row2.label(text="WARNING: Removes existing names")


# TODO file picker...

def execute_import(self, context):
    """ _ """
    ver = bl_info["version"]
    print("===============================================\n" +
          "Kingpin Model Importer v%i.%i.%i" % (ver[0], ver[1], ver[2]))

    if context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")  # , toggle=False)
    # deselect any objects
    for ob in bpy.data.objects:
        kpc.set_select_state(ob, False)

    # multiple "selected" file loader
    valid = True
    folder = os.path.dirname(os.path.abspath(self.filepath))
    for f in self.files:
        fPath = os.path.join(folder, f.name)
        print("===============================================")
        ret = load_kp_model(context, fPath)

        if ret == 2:
            valid = False  # stop print
        if not ret:
            print("Error: in %s" % fPath)
            return {"FINISHED"}

    kpc.get_layers(context).update()
    if valid:
        self.report({"INFO"}, "File \'%s\' imported" % self.filepath)
    else:
        self.report({"WARNING"}, "Warning: see console")


class KINGPIN_Import_Dialog(Operator, ImportHelper, kpc.KINGPIN_FileSelect_md2_Params):
    """ Import Kingpin format file (md2/mdx) """
    bl_idname = "kp.import_model_dialog"
    bl_label = "Import md2/mdx"
    bl_options = {'REGISTER'}
    bl_description = "Import Kingpin format file (md2/mdx)"
    filename_ext = {".mdx", ".md2"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        execute_import(self, context)
        return {"FINISHED"}

    def draw(self, context):
        draw_import(self, context)


class Kingpin_Model_Reader:
    """ Kingpin Model Reader """

    def __init__(
            self,
            file_path,
            ext,
            ui_opt_anim,
            ui_opt_anim_type,
            ui_opt_frame_names,
            ui_opt_dupe_mat,
            ui_opt_mesh_cleanup,
            ui_opt_weld_verts,
            ui_opt_store_pcx):
        """ init """
        # md2.ui_opt_sk_types = ui_import_.ui_opt_sk_types

        self.object = None
        # self.self = bl_self #not used? import dialog
        self.ui_opt_anim = ui_opt_anim
        self.ui_opt_anim_type = ui_opt_anim_type
        self.ui_opt_frame_names = ui_opt_frame_names
        self.ui_opt_dupe_mat = ui_opt_dupe_mat
        self.ui_opt_mesh_cleanup = ui_opt_mesh_cleanup
        self.ui_opt_weld_verts = ui_opt_weld_verts
        # self.ui_opt_sk_types = ui_opt_sk_types
        self.ui_opt_store_pcx = ui_opt_store_pcx

        self.start_time = 0
        self.isHDmodel = False
        self.isMdx = True if ext == ".mdx" else False
        self.ident = 0
        self.version = 0
        self.valid = 1  # disable "done"

        self.filePath = file_path
        self.name = os.path.splitext(os.path.basename(file_path))[0]
        self.ext = os.path.splitext(os.path.basename(file_path))[1]
        self.skins = []
        self.tri_idc_vt = []  # store triangle vertex index (idx1, idx2, idx3)
        self.tri_idc_uv = []  # store triangles UV index (idx1, idx2, idx3)
        self.tri_mdx_id = []  # mdx object id. for spliting mesh into groups
        self.uv_cords = []  # UV float cordanates (X,Y)
        # frames data
        self.fr_v_pos = []  # vertex position (X,Y,Z)
        self.fr_v_nrm = []  # vertex normal
        self.fr_names = []  # frame names
        # data stored in object
        self.store_fr_scale = []  # stored custom data
        self.store_fr_v_pos = []  # stored custom data
        self.hdr = None

    def makeObject(self, _): #dlog_context
        """ _ """

        def weldVertex(self):
            """ _ """
            prefix = "Welding Vertex"
            temp_time = kpc.printStart_fn()  # reset timmer
            kpc.printProgress_fn(0, 100, prefix)

            fr0_v_pos_byte = self.store_fr_v_pos[0]
            if kpc.check_version(2, 80, 0) < 0:
                unique_pos = []
                uidx = []
                seen = {}
                # seen = set()

                for i, pos in enumerate(fr0_v_pos_byte):
                    t = tuple(pos)                     # must be hashable
                    if t not in seen:
                        # seen.add(t)
                        seen[t] = len(unique_pos)
                        unique_pos.append(pos)
                        uidx.append(i)

                # Build old -> new mapping
                # old_to_new = {old_i: new_i for new_i, old_i in enumerate(uidx)}
                old_to_new = {i: seen[tuple(fr0_v_pos_byte[i])] for i in range(len(fr0_v_pos_byte))}

                # Remap triangle indices
                self.tri_idc_vt = [
                    (old_to_new[a], old_to_new[b], old_to_new[c])
                    for a, b, c in self.tri_idc_vt
                ]

                # Filter per-frame positions (keep order of first appearance)
                for fr in range(self.hdr.numFrames):
                    self.fr_v_pos[fr] = np.array([self.fr_v_pos[fr][i] for i in uidx])
            else:
                # Build once from first frame
                _, uidx, inverse_idx = np.unique(
                    fr0_v_pos_byte, axis=0, return_index=True, return_inverse=True
                )

                # Remap indices
                self.tri_idc_vt = inverse_idx[np.array(self.tri_idc_vt)].tolist()

                # Keep original per-frame data, just remove duplicates
                for fr in range(self.hdr.numFrames):
                    self.fr_v_pos[fr] = np.array(self.fr_v_pos[fr])[uidx] #.tolist()

            # update vertex count
            self.hdr.numVerts = len(self.fr_v_pos[0])

            kpc.printDone_fn(temp_time, prefix)
        # end weldVertex
        # ##############

        # start make object
        bpy_context = bpy.context
        current_scene = bpy_context.scene
        int_frame = current_scene.frame_current
        current_scene.frame_set(0)

        # weld vertex
        if self.ui_opt_weld_verts:
            weldVertex(self)

        self.start_time = kpc.printStart_fn()  # reset timmer
        prefix_mesh = "Generating Mesh"
        kpc.printProgress_fn(0, self.hdr.numFrames, prefix_mesh)  # print progress

        # ###################
        # 2.8 Create the mesh
        md2_mesh = bpy.data.meshes.new(self.name)
        # new 2.8 method.
        md2_mesh.from_pydata(self.fr_v_pos[0].tolist(), [], self.tri_idc_vt)
        kpc.printDone_fn(self.start_time, prefix_mesh)  # Finish mesh data
        # md2_mesh.shade_smooth()
        print_stat = "Poly:  %i\nVerts: %i" % (
            len(md2_mesh.polygons), len(md2_mesh.vertices))

        # ##########
        # skins data
        image_array = []
        print_skin = "Skins: 0\n========\n"
        if self.hdr.numSkins > 0:
            self.start_time = kpc.printStart_fn()  # reset timmer
            prefix_skin = ""
            # print("========")
            #      "Generate Materials:")
            # print("skins: %i" % len(self.skins))  # print count
            print_skin = "Skins: %i\n========\n" % len(self.skins)

            for skin in self.skins:
                # print("skin_%i: %s" % (idx + 1, skin), end="")  # print name
                prefix_skin = str("%s%s" % (prefix_skin, skin))

                if self.ui_opt_dupe_mat:  # use old material if it exists
                    foundMat = False
                    for mat in bpy.data.materials:
                        if mat.name == skin:
                            md2_mesh.materials.append(mat)
                            foundMat = True
                            break
                    if foundMat:
                        prefix_skin = str(
                            "%s  Existing material\n" % prefix_skin)
                        continue

                mat_id = bpy.data.materials.new(skin)  # new material
                md2_mesh.materials.append(mat_id)  # asign materal to mesh

                # get materal node/links
                mat_id.use_nodes = True
                mat_nodes = mat_id.node_tree.nodes
                mat_links = mat_id.node_tree.links
                # delete existing node
                while mat_nodes:
                    mat_nodes.remove(mat_nodes[0])

                # create diffuse/texture/output nodes
                node_tex = mat_nodes.new("ShaderNodeTexImage")  # image texture
                node_diff = mat_nodes.new(
                    type="ShaderNodeBsdfDiffuse")  # simple shader
                node_out_mat = mat_nodes.new(
                    type="ShaderNodeOutputMaterial")  # output Cycles
                # move nodes
                node_tex.location = Vector((-350, -80))
                node_out_mat.location = Vector((250, 0))  # output Cycles
                # create links
                mat_links.new(
                    node_diff.outputs["BSDF"], node_out_mat.inputs["Surface"])
                mat_links.new(
                    node_tex.outputs["Color"], node_diff.inputs["Color"])

                if kpc.check_version(2, 80, 0) < 0:  # output blender render v2.79
                    node_output = mat_nodes.new(type="ShaderNodeOutput")
                    mat_links.new(
                        node_tex.outputs["Color"], node_output.inputs["Color"])
                    node_output.location = Vector((250, -120))
                    node_tex.color_space = "NONE"  # set node/3d view to non sRGB

                # try to load tga/pcx image
                skinImg = load_kingpin_image(mdxPath=skin,
                                             filePath=self.filePath,
                                             check_dupe=self.ui_opt_dupe_mat,
                                             store_image=self.ui_opt_store_pcx)  # KP_Util_Import
                if skinImg is None:
                    skinImg = bpy.data.images.new(
                        skin, self.hdr.skinWidth, self.hdr.skinHeight)
                    prefix_skin = str("%s  Missing\n" %
                                      prefix_skin)  # print(" Missing")
                else:
                    prefix_skin = str("%s  OK\n" % prefix_skin)  # print(" OK")
                # skinImg. mapping = "UV" #2.7
                skinImg.name = skin
                # set non sRGB (makes image brighter)
                skinImg.colorspace_settings.name = "Non-Color"  # "Linear"
                image_array.append(skinImg)

                # link image to texture node
                node_tex.image = skinImg

            # Materials Done
            print_skin += prefix_skin  # + "========"
            kpc.printDone_fn(self.start_time, "Generating Materials")

        # #######
        # uv data
        self.start_time = kpc.printStart_fn()  # reset timmer
        prefix = "Generating UV"
        kpc.printProgress_fn(0, self.hdr.numFrames, prefix)  # print progress

        uv_type, uv_layer = kpc.get_uv_data_new(
            md2_mesh, uv_name="UVMap_0")  # v1.2.2
        image = None  # asign first image. TODO: cleanup
        for im in image_array:
            if im is not None:
                image = im
                break
        if uv_type == 1:  # B2.79 v1.2.2
            blen_uvs = md2_mesh.uv_layers[0]
            for i, poly in enumerate(md2_mesh.polygons):
                uv_face = self.tri_idc_uv[i]
                v1, v2, v3 = uv_face
                blen_uvs.data[poly.loop_start + 0].uv = self.uv_cords[v1]
                blen_uvs.data[poly.loop_start + 1].uv = self.uv_cords[v2]
                blen_uvs.data[poly.loop_start + 2].uv = self.uv_cords[v3]
                poly.use_smooth = True  # smooth all faces
                # set face texture
                md2_mesh.uv_textures[0].data[i].image = image
        elif uv_type == 2:  # B2.8 v1.2.2
            for i, poly in enumerate(md2_mesh.polygons):
                poly.use_smooth = True
                if i != poly.index:
                    print("--== i:%i f:%i ==--" % (i, poly.index))
                uv_x = self.tri_idc_uv[i]
                for uvid, loop_idx in enumerate(poly.loop_indices):
                    uv_layer.data[loop_idx].uv = self.uv_cords[uv_x[uvid]][:]

        kpc.printDone_fn(self.start_time, prefix)
        # Finish uv data
        # ##############

        # #####################
        # validate/update model
        if self.ui_opt_mesh_cleanup:
            if md2_mesh.validate(verbose=True, clean_customdata=False):  # print errors
                print("--------\n" +
                      "WARNING: Found invalid mesh data.\n"
                      "  Disable \"Mesh Cleanup\" if required\n" +
                      "--------\n")
                self.valid = 2

        kpc.set_auto_smooth(md2_mesh, 180)
        md2_mesh.update()

        # create new object from mesh
        self.start_time = kpc.printStart_fn()  # reset timmer
        prefix = "Generating Object"
        kpc.printProgress_fn(0, self.hdr.numFrames, prefix)  # print progress

        obj = bpy.data.objects.new(md2_mesh.name, md2_mesh)
        kpc.set_object_link(bpy_context, obj)  # v1.2.2
        # select object
        kpc.set_select_state(obj, True)  # 1.2.2
        # Print Done.
        kpc.printDone_fn(self.start_time, prefix)

        # ############
        # Animate mesh
        sk_type = 0
        if self.hdr.numFrames > 1 and self.ui_opt_anim:
            self.start_time = kpc.printStart_fn()  # reset timmer
            prefix = "Generating Frames"

            # setup shape keys
            obj_dat = obj.data
            sk_type = self.ui_opt_anim_type

            #
            # create key frames for vertex
            if sk_type == kpc.SK_MODE_VERT:  # "SK_VERTEX"
                obj_dat.animation_data_create()
                new_action = bpy.data.actions.new("KP_Anim")
                #obj_dat.animation_data.action = new_action
                kpc.assign_action_with_slot(  # b44+
                    obj_dat, new_action, slot_id_type='MESH')

                obj_act = obj_dat.animation_data.action

                # num_verts = len(obj_dat.vertices)
                num_frames = self.hdr.numFrames
                # frames = self.fr_v_pos
                # frames = np.array(self.fr_v_pos)
                fpath = "vertices[%d].co" # kpc.get_anim_fdata_vert()
                frames_np = np.stack(self.fr_v_pos)   # shape: (num_frames, num_verts, 3)
                frame_nums = np.arange(num_frames, dtype=np.float32)
                for v in obj_dat.vertices:  # num_verts):
                    vert_idx = v.index
                    fcurves = [kpc.fcurves_new( # b44+
                        obj_act,
                        fpath % (vert_idx),
                        index=i,
                        group_name="Vertex %d" % vert_idx,
                        slot_id_type='MESH') for i in range(3)]

                    for i in range(3):
                        fcurves[i].keyframe_points.add(num_frames)

                    for coord, fc in enumerate([fcurves[0], fcurves[1], fcurves[2]]):
                        values = frames_np[:, vert_idx, coord]
                        co_flat = np.column_stack((frame_nums, values)).ravel().tolist()
                        fc.keyframe_points.foreach_set("co", co_flat)
                        # for kp in fc.keyframe_points: #slow... minimal benifit..
                        #     kp.interpolation = 'LINEAR'

                    for i in range(3):
                        fcurves[i].update()

                    kpc.printProgress_fn(
                        vert_idx, self.hdr.numVerts, prefix)  # print progress
            #
            # animate multiple shape keys
            elif sk_type == kpc.SK_MODE_REL: # SK_MULTI (Relative)
                _ = obj.shape_key_add(name="Basis", from_mix=False)
                sk_name = kpc.get_shapekey_name_str() # generate names
                sk_names = [sk_name % i for i in range(self.hdr.numFrames)]
                sk_blocks = [obj.shape_key_add(name=name, from_mix=False) for name in sk_names]

                for i, sk in enumerate(sk_blocks):
                    # Set vertex data in shape
                    flat_co = self.fr_v_pos[i].ravel()
                    sk.data.foreach_set("co", flat_co)
                    # set keyframe to use shapeky
                    sk.value = 1.0  # main key
                    sk.keyframe_insert("value", frame=i)
                    sk.value = 0.0  # neighbouring frames
                    sk.keyframe_insert("value", frame=i - 1)
                    sk.keyframe_insert("value", frame=i + 1)

                #  set keys linear
                anim = kpc.get_shapekey_anim_data(obj_dat, True) #obj_dat.animation_data
                if anim is not None and anim.action is not None:
                    anim_fcurves = kpc.fcurves_get(anim.action)  #b44+
                    for fcu in anim_fcurves: # anim.action.fcurves:
                        for kf in fcu.keyframe_points:
                            kf.interpolation = "LINEAR"
                            # kf.easing = "AUTO"
                        fcu.update()

                obj.use_shape_key_edit_mode = False
                # kpc.sync_shapekey_to_frame(obj, obj_dat.shape_keys)
            #
            # absolute shape keys
            elif sk_type == kpc.SK_MODE_ABS:  # "SK_ABS", "2.Shape Key (absolute)",
                sk_offs = 20 if kpc.check_version(2, 80, 0) < 0 else 10 # bugfix index0 = 10.0 :-/
                _ = obj.shape_key_add(name="Basis", from_mix=False)
                sk_name = kpc.get_shapekey_name_str() # generate names
                sk_names = [sk_name % i for i in range(self.hdr.numFrames)]
                sk_blocks = [obj.shape_key_add(name=name, from_mix=False) for name in sk_names]
                for i, sk in enumerate(sk_blocks):
                    # Set vertex data in shape
                    flat_co = self.fr_v_pos[i].ravel()
                    sk.data.foreach_set("co", flat_co)
                    sk.interpolation = "KEY_LINEAR" # KEY_CARDINAL #2.79

                sk_data = obj_dat.shape_keys
                sk_data.use_relative = False

                for i in range(self.hdr.numFrames):
                    sk_data.eval_time = (i * 10) + sk_offs
                    sk_data.keyframe_insert(data_path="eval_time", frame=i)

                anim = kpc.get_shapekey_anim_data(obj_dat, False)
                if anim is not None and anim.action is not None:
                    anim_fcurves = kpc.fcurves_get(anim.action)  #b44+
                    for fcu in anim_fcurves: # anim.action.fcurves:
                        for kf in fcu.keyframe_points:
                            kf.interpolation = "LINEAR"
                            # kf.easing = "AUTO"
                        fcu.update()

                obj.use_shape_key_edit_mode = False
                # kpc.sync_shapekey_to_frame(obj, sk_data)
                # obj.active_shape_key_index = 1  # updates display

            ####################
            # import frame names
            if self.ui_opt_frame_names:  # reset frame names
                lastFName = ""
                mark = current_scene.timeline_markers
                mark.clear()
                fNames = self.fr_names
                for i in range(self.hdr.numFrames):
                    tmp_str = fNames[i].rstrip("0123456789")  # remove numbers
                    if not lastFName == tmp_str:
                        # mark.new(tmp_str.decode("utf-8"), frame=i)
                        mark.new(tmp_str, frame=i)
                        lastFName = tmp_str

            # set sceen timeline to match imported model
            current_scene.frame_start = 0
            current_scene.frame_end = self.hdr.numFrames - 1
            obj_dat.update()
            # Frames Done
            kpc.printDone_fn(self.start_time, prefix)

        # set frame back to old position
        current_scene.frame_set(int_frame)

        # add custom data
        obj.data[kpc.DATA_V_BYTE] = np.concatenate(self.store_fr_v_pos).ravel().tolist()
        obj.data[kpc.DATA_F_SCALE] = self.store_fr_scale
        obj.data[kpc.DATA_F_COUNT] = self.hdr.numFrames
        obj.data[kpc.DATA_V_COUNT] = self.hdr.numVerts

        kpc.set_objects_active(bpy_context, obj)
        kpc.set_layer_update(bpy_context)  # v1.2.2

        # bug in 2.79. retime sets base to 10.00
        if sk_type == kpc.SK_MODE_ABS and kpc.check_version(2, 80, 0) < 0:
            bpy.ops.object.shape_key_retime()

        if sk_type in (kpc.SK_MODE_REL, kpc.SK_MODE_ABS):
            kpc.sync_shapekey_to_frame(obj, obj.data.shape_keys)

        print(print_stat)
        print(print_skin)
        print("Model imported.\n" +
              "===============================================")
    # end makeObject
    # ##############

    def read_file(self, filePath: str):  # Kingpin_Model_Reader
        """ open .md2 file and read contents """
        print("Reading %s" % filePath, end="\n")
        start_read_time = kpc.printStart_fn()  # reset timmer

        def _read_header(self, inFile):
            if self.isMdx:
                self.hdr = kpc.mdx_hdr(inFile)
            else:
                self.hdr = kpc.md2_hdr(inFile)

            if self.ui_opt_anim is False:
                self.hdr.numFrames = 1
            if self.hdr.framesize == (self.hdr.numVerts * 7 + 40):  # +3 bytes/vert
                self.isHDmodel = True

        def _read_skins(self, inFile):
            # Skins
            if self.hdr.numSkins > 0:
                inFile.seek(self.hdr.ofsSkins, 0)
                chunk = kpc.readChunkToList(
                    inFile, "<64s", self.hdr.numSkins)  # .split(b"\x00")
                self.skins = [
                    (asciiz(skin[0].decode("utf-8", errors="replace"))) for skin in chunk]

        def _read_uv(self, inFile):
            # UV (software 1byte texture cords)
            if not self.isMdx and self.hdr.numGLCmds <= 1:
                #
                start_tex_time = kpc.printStart_fn()  # reset timmer
                prefix = "Reading Software UV"
                kpc.printProgress_fn(
                    0, self.hdr.numFrames, prefix)  # print progress

                inFile.seek(self.hdr.ofsUV, 0)
                chunk = kpc.readChunkToList(inFile, "<2h", self.hdr.numUV)
                for i in range(self.hdr.numUV):
                    self.uv_cords.insert(
                        i,
                        (chunk[i][0] / self.hdr.skinWidth, 1 - (chunk[i][1] / self.hdr.skinHeight)))

                # Tris (non GLCommand)
                inFile.seek(self.hdr.ofsTris, 0)
                chunk = kpc.readChunkToList(inFile, "<6H", self.hdr.numTris)
                for i in range(self.hdr.numTris):
                    self.tri_idc_vt.append(
                        (chunk[i][0], chunk[i][2], chunk[i][1]))  # vert indices
                    self.tri_idc_uv.append(
                        (chunk[i][3], chunk[i][5], chunk[i][4]))  # uv indices
                # Done
                # Reading SW Texture cords
                kpc.printDone_fn(start_tex_time, prefix)

            else:
                start_gl_time = kpc.printStart_fn()  # reset timmer
                prefix = "Reading GLCommands"
                kpc.printProgress_fn(
                    0, self.hdr.numFrames, prefix)  # print progress

                # ====================================================================
                # UV GLCommands (float texture cords)
                inFile.seek(self.hdr.ofsGLCmds, 0)
                uv_idx, c_idx = 0, 0

                def readGLVertex(chunk, c_idx):
                    data, c_idx = kpc.getChunk(chunk, "<2f1l", c_idx)
                    s = data[0]
                    t = 1.0 - data[1]  # flip Y
                    li_idx = data[2]
                    return (s, t, li_idx), c_idx

                chunk = kpc.readChunk(
                    inFile, "f", self.hdr.ofsGLCmds_end - self.hdr.ofsGLCmds)
                mdx_id = 1
                while 1:
                    if self.isMdx:
                        data, c_idx = kpc.getChunk(chunk, "<2l", c_idx)
                        mdx_id = data[1]
                    else:  # md2
                        data, c_idx = kpc.getChunk(chunk, "<l", c_idx)
                    # read gl_strip
                    if data[0] >= 1:
                        num_verts = data[0]
                        v2, c_idx = readGLVertex(chunk, c_idx)
                        v3, c_idx = readGLVertex(chunk, c_idx)
                        self.uv_cords.append((v2[0], v2[1]))
                        self.uv_cords.append((v3[0], v3[1]))
                        uv_idx += 2
                        for i in range(1, (num_verts - 1), 1):
                            # create indices for each triangle
                            v1, v2 = v2[:], v3[:]  # new ref
                            v3, c_idx = readGLVertex(chunk, c_idx)
                            self.uv_cords.append((v3[0], v3[1]))
                            uv_idx += 1
                            if (i % 2) == 0:  # reverse order?
                                self.tri_idc_vt.append( # vert indices
                                    (v1[2], v2[2], v3[2]))
                                self.tri_idc_uv.append( # uv indices
                                    (uv_idx - 3, uv_idx - 2, uv_idx - 1))
                            else:
                                self.tri_idc_vt.append( # vert indices
                                    (v3[2], v2[2], v1[2]))
                                self.tri_idc_uv.append( # uv indices
                                    (uv_idx - 1, uv_idx - 2, uv_idx - 3))
                            self.tri_mdx_id.append(mdx_id) #mdx
                    # read gl_fan
                    elif data[0] <= -1:
                        num_verts = -data[0]
                        v1, c_idx = readGLVertex(chunk, c_idx)
                        v3, c_idx = readGLVertex(chunk, c_idx)
                        piv_vert = uv_idx
                        self.uv_cords.append((v1[0], v1[1]))
                        self.uv_cords.append((v3[0], v3[1]))
                        uv_idx += 2
                        for i in range(1, (num_verts - 1), 1):
                            # create indices for each triangle
                            v2 = v3[:]  # new ref
                            v3, c_idx = readGLVertex(chunk, c_idx)
                            uv_idx += 1
                            self.uv_cords.append((v3[0], v3[1]))
                            self.tri_idc_vt.append( # vert indices
                                (v3[2], v2[2], v1[2]))
                            self.tri_idc_uv.append( # uv indices
                                (uv_idx - 1, uv_idx - 2, piv_vert))
                            self.tri_mdx_id.append(mdx_id) # mdx
                    else:
                        break
                # Done
                kpc.printDone_fn(start_gl_time, prefix)  # Reading GLCommands
                # ====================================================================

        def _read_frames(self, inFile):
            prefix = "Reading Frames"
            start_frme_time = kpc.printStart_fn()  # reset timmer
            kpc.printProgress_fn(0, self.hdr.numFrames, prefix)  # print progress

            # inFile.seek(self.hdr.ofsFrames, 0)
            for fr in range(self.hdr.numFrames):
                inFile.seek(self.hdr.ofsFrames + self.hdr.framesize * fr, 0)
                # read frame headder
                buff = inFile.read(struct.calcsize("<6f16s"))
                data = struct.unpack("<6f16s", buff)
                scale = (data[0], data[1], data[2])  # scale
                minXYZ = (data[3], data[4], data[5])  # model XYZ location
                self.store_fr_scale += [data[0], data[1], data[2]]
                # vert pos
                chunk_sd = kpc.readChunkToList(inFile, "4B", self.hdr.numVerts)
                np_sd = np.array(chunk_sd)
                # verts_sd = np.delete(np_sd, 3, axis=1)
                verts_sd = np_sd[:, :-1] #b2.79 (np v1.10.1)
                norms = [[kpc.MD2_VN[v[3]][:]] for v in chunk_sd]
                if self.isHDmodel:
                    # custom data. add 2nd byte precision in mdx/md2 (signed char. subdevision)
                    chunk_hd = kpc.readChunkToList(inFile, "3b", self.hdr.numVerts)
                    sd = (verts_sd) << 8
                    hd = np.array(chunk_hd)
                    verts = (sd + hd) / 256.0 * scale + minXYZ
                else:
                    verts = (verts_sd) * scale + minXYZ
                    # TODO add smooth pos
                    # if smooth:
                    # fast_threshold_bilateral() #smooth

                self.fr_v_pos.append(verts)  # append all vertex pos for frame
                self.fr_v_nrm.append(norms)  # vertexnormal index
                self.store_fr_v_pos.append(verts_sd) #+= [v[j] for v in chunk_sd for j in range(3)] #rev order...
                self.fr_names.append(asciiz(  # .split(b"\x00")
                    data[6].decode("utf-8", errors="replace")))  # frame names

            kpc.printDone_fn(start_frme_time, prefix)  # Reading Frames Done
            # end frame loop

        with open(file=self.filePath, mode="rb") as inFile:
            print(".", end="")  # Done. #1
            try:
                _read_header(self, inFile)
                print(".", end="")  # Done. #2

                _read_skins(self, inFile)
                print(".", end="")  # Done. #3

                _read_uv(self, inFile) #GLCommands...

                _read_frames(self, inFile)
            except AssertionError as error:
                print(error)

        # print total time
        kpc.printDone_fn(start_read_time, "Reading File Total")


def load_kingpin_image(mdxPath, filePath, check_dupe, store_image):
    """ load image file
        pcx loader added to view textures in 2.8+
    """

    def load_image_types(imgType, fileName, dir_name):
        """ load pcx or other"""
        if imgType == ".pcx":  # 2.8?
            return read_pcx_file(
                fileName, dirname=dir_name,
                check_existing=check_dupe,
                md2_name=mdxPath,
                store_image=store_image)
        # known image type
        return load_image(
            fileName, dirname=dir_name, recursive=False,
            check_existing=check_dupe, force_reload=True)

    fileName = os.path.basename(mdxPath)
    f_ext = os.path.splitext(fileName)[1]

    # try internal mdx path first
    dir_name = os.path.dirname(mdxPath)
    image = load_image_types(f_ext, fileName, dir_name)
    if image is not None:
        return image

    # try .mdx file path
    dir_name = os.path.dirname(filePath)
    image = load_image_types(f_ext, fileName, dir_name)
    if image is not None:
        return image

    strFolder = ["models", "players", "textures"]  # TODO main/baseq2?
    for d in strFolder:
        idxPath = filePath.find(d + os.sep)
        if idxPath >= 1:
            filePath = filePath[0:idxPath]
            break

    fullpath = bpy.path.native_pathsep(filePath + mdxPath)
    dir_name = os.path.dirname(fullpath)
    image = load_image_types(f_ext, fileName, dir_name)

    return image


def asciiz(s):
    """search hex null"""
    for i, c in enumerate(s):
        if ord(c) == 0:
            return s[:i]
    return s


# def Import_MD2_fn(self, filename):
def load_kp_model(context, filepath):
    """ _ """
    # bpy_context = bpy.context #
    ui_import_ = context.window_manager.kp_import_
    ext = os.path.splitext(os.path.basename(filepath))[1].lower()
    if ext not in (".md2", ".mdx"):
        print("\nERROR: Incorrect file extension. Only md2 or mdx\n")
        return 2  # error

    md2 = Kingpin_Model_Reader(
        filepath, ext,
        ui_import_.ui_opt_anim,
        ui_import_.ui_opt_anim_type,
        ui_import_.ui_opt_frame_names,
        ui_import_.ui_opt_dupe_mat,
        ui_import_.ui_opt_mesh_cleanup,
        ui_import_.ui_opt_weld_verts,
        ui_import_.ui_opt_store_pcx
    )

    md2.read_file(filepath)
    md2.makeObject(context)

    return md2.valid
