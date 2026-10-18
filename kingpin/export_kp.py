"""
md2/mdx exporter
"""

import bpy
import os
import struct
import numpy as np
# import traceback
from collections import deque, namedtuple
# from mathutils import Vector as Vec
from bpy.types import Operator, PropertyGroup
from bpy.props import (
    BoolProperty,
    EnumProperty,
    StringProperty,
    IntProperty
)
from bpy_extras.io_utils import ExportHelper
from . import common_kp as kpc
from . import bl_info  # version


# -|GUI|- Export Properties
class KINGPIN_Export_props(PropertyGroup):
    """ export properties """
    # skin name selector
    ui_opt_tex_name = EnumProperty(
        name="Skin",
        description="Skin naming method",
        items=(
            ("SKIN_MAT_NAME", "1.Material Name",
             "Use material name for skin.\n" +
             "Must include the file extension\n" +
             "eg.. models/props/test.tga\n" +
             "Image dimensions are sourced from nodes. 256 is use if no image exists"
             ),
            ("SKIN_TEX_NAME", "2.Image Name",
             "Use image name from Material nodes\n" +
             "Must include the file extension\n" +
             "\"material name\" will be used if no valid textures are found\n" +
             "Image dimensions are sourced from nodes. 256 is use if no image exists"
             ),
            ("SKIN_TEX_PATH", "3.Image Path",
             "Use image path name from Material nodes\n" +
             "Path must contain a folder models/ or players/ or textures/ \n" +
             "\"material name\" will be used if no valid textures are found\n" +
             "Image dimensions are sourced from nodes. 256 is use if no image exists"
             ),
        ),
        default="SKIN_MAT_NAME"
    )
    # misc options
    ui_opt_apply_modify = BoolProperty(
        name="Apply Modifiers",
        description="Apply Modifiers or use the original base mesh",
        default=True
    )
    ui_opt_is_hd = BoolProperty(
        name="HD Vertex",
        description=(
            "2-byte vertex position. Backward compatable with engine and some viewers.\n" +
            "Limit its use to large/animated models\n" +
            "Note: requires MH patch to view in kingpin. without the wobble :)"
        ),
        default=False
    )
    ui_opt_is_player = BoolProperty(
        name="Player Model", # Seam Fix (Player etc.)",
        description=(
            "Export all \'head\' \'body\' \'legs\' named objects. using a shared quantizer.\n" +
            "Usage: Show all head, body, legs objects. Click export. 3 models will be exported.\n" +
            "Note: only use on models with a shared seam, as it waste precision"
        ),
        default=False,
    )
    # animation group
    ui_opt_animated = BoolProperty(
        name="Export animation",
        description=(
            "Export all animation frames.\n" +
            "Note: Start/End frame initially comes from timeline range"
        ),
        default=False
    )
    ui_opt_fr_start = IntProperty(
        name="Start",
        description="Animated model start frame",
        min=0, max=kpc.MD2_MAX_FRAMES - 1,
        default=0
    )
    ui_opt_fr_end = IntProperty(
        name="End",
        description="Animated model end frame",
        min=0, max=kpc.MD2_MAX_FRAMES - 1,
        default=40
    )
    ui_opt_use_hitbox = BoolProperty(
        # name="Player HitBox",
        name="MDX objects/HitBox",
        description=(
            "Seperate each mesh into an mdx object(hitbox). eg hand, arm, torso.\n" +
            "Each objects can use a differnt textures, " +
            "location damage in multiplayer, and for detatchable body parts.\n" +
            "Note: disabled will create 1 large object/hitbox"
        ),
        default=False
    )
    ui_opt_exp_weps = BoolProperty(
        name="Player wep, extras, etc.",
        description=(
            "Export all additional scene objects. Using mesh names.\n" +
           " Note: names truncated to first dot(.)"),
        default=False
    )
    # gui panel extra
    ui_opt_model_ext = EnumProperty(
        name="Format",
        description="Choose which format to export",
        items=((".md2", "MD2", "Quake2 models"), (".mdx", "MDX", "Kingpin models")),
        default=".mdx"
    )
    ui_opt_export_name = StringProperty(
        name="File",
        description="File name for model",
        default="tris",
        maxlen=1024,
        subtype="FILE_NAME"  # "FILE_PATH"
    )
    ui_opt_export_path = StringProperty(
        name="Path",
        description="Folder path to MD2/X file",
        options={"HIDDEN"},
        default="",
        maxlen=1024,
        subtype="NONE"
    )
    ui_opt_export_mdx_obj = EnumProperty(
        # name="",
        name="MDX Parts",
        description=(
            "MDX hitbox/parts support.\n" +
            "Used for hitboxs, multiple skins and shootable limbs"
        ),
        items=(
            ("MDX_OBJ_NONE", "1.SINGLE PART",
             "Export 1 large mdx hitbox/parts"
            ),
            ("MDX_OBJ_OBJECTS", "2.FROM OBJECTS",
             "Use each object as a seperate hitbox/parts"
            ),
            ("MDX_OBJ_SKINS", "3.FROM OBJECTS+SKINS",
             "Create mdx hitbox/parts from each material and objects selected"
            ),
        ),
        default="MDX_OBJ_NONE"
    )
    ui_opt_export_mode = EnumProperty(
        name="Mode",
        description="Export model as a single file, player model, all visable objects etc.\nNote: file names will be trimmed at first dot (.)",
        items=(
            ("EXP_MERGED", "1.SELECTED",
             "Export all selected objects as one md2/mdx"
            ),
            ("MDX_PLAYER_ONLY", "2.PLAYER MODEL",
             "Export any visable head/body/legs. Use each object prefix to find its destination.\n" +
             "Note: export names become head/body/legs"
            ),
            ("EXP_PLAYER_WEPS", "3.PLAYER+ADDONS",
             "Export all visable model. Grouping head/body/legs and all other models(weps, addons..)"
            ),
            ("EXP_ADDON_ONLY", "4.ADDONS ONLY",
             "Export all visable models, that are not prefixed with head/body/legs"
            ),
            ("EXP_ALL_ITEMS", "5.ALL OBJECTS",
             "Export all visable models in scene"
            ),
        ),
        default="EXP_MERGED"
    )
    ui_opt_cust_vn_face = EnumProperty(
        name="Normal",
        description=(
            "Source used to get vertex normal direction"
        ),
        items=(
            ("EXP_NORM_VERT", "1.VERTEX",
             "Use vertex normals (matches viewport smooth)"
            ),
            ("EXP_NORM_EDGE", "2.EDGE NORMAL",
             "Use edge normals (for custom normals).\n" +
             "eg. Data Transfer to fix player seam's.\n" +
             "Note: normal is an average of all shared edges"
            ),
            ("EXP_NORM_FACE", "3.FACE NORMAL",
             "Use face weighted normals (use for quad mesh)"
            ),
        ),
        default="EXP_NORM_VERT"
    )


class KINGPIN_Export_Button(Operator, kpc.KINGPIN_FileSelect_md2_Params):
    """
    Export selection to Kingpin file format (md2/mdx)
    note: GUI button on tool-panel
    """

    bl_idname = "kp.export_button_model"
    bl_label = "Export model"
    bl_options = {'REGISTER'}
    bl_description = "Export selection to Kingpin file format (md2/mdx)"
    filename_ext = {".mdx", ".md2"}  # md2 used later
    check_extension = True  # 2.8 allow typing md2/mdx

    def execute(self, context):
        kp_export_ = context.window_manager.kp_export_

        if kp_export_.ui_opt_export_path == '':
            self.report({'ERROR'}, "No \'path\' name set")
        elif kp_export_.ui_opt_export_name == '':
            self.report({'ERROR'}, "No \'file\' name set")
        else:
            merg_path = os.path.join(
                kp_export_.ui_opt_export_path,
                kp_export_.ui_opt_export_name)

            self.filepath = bpy.path.abspath(
                bpy.path.ensure_ext(
                    merg_path,
                    kp_export_.ui_opt_model_ext))
            execute_export(self, context)
        return {"FINISHED"}


class KINGPIN_Export_Button_File(Operator):
    """ Copy object @name to @file input box
        export tool panel
    """
    bl_idname = "kp.export_button_file"
    bl_label = ""
    # bl_options = {'REGISTER'}
    bl_description = "Copy selected objects @name to @file input box"
    check_extension = True  # 2.8 allow typing md2/mdx

    def execute(self, context):
        kp_export_ = context.window_manager.kp_export_

        act_obj = kpc.get_objects_active(bpy.context)

        if act_obj:
            kp_export_.ui_opt_export_name = os.path.splitext(act_obj.name)[0]
        else:
            sel_obj = kpc.get_objects_selected(context)[:]
            if len(sel_obj) > 0:
                kp_export_.ui_opt_export_name = os.path.splitext(sel_obj[0].name)[0]
        return {"FINISHED"}


class KINGPIN_Export_Button_Folder(Operator, kpc.KINGPIN_FileSelect_folder_Params):
    """ export folder selector
        export tool panel
    """
    bl_idname = "kp.export_button_folder"
    bl_label = "Select Folder"  # icon
    # bl_options = {'REGISTER'}
    bl_description = "Brows for a folder to export models to"
    check_extension = True

    def execute(self, context):
        ui_export_ = context.window_manager.kp_export_
        ui_export_.ui_opt_export_path = self.directory
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


def draw_export(self, context, is_tool_panel):
    ui_export_ = context.window_manager.kp_export_
    layout = self.layout

    # skin chooser box
    col = layout.column_flow(columns=2, align=True)
    col.label(text="Skin Name")
    col.label(text="Export Modes")
    col.label(text="Vertex Normal")
    col.label(text="MDX Hitbox")
    col.prop(ui_export_, "ui_opt_tex_name", text="")
    col.prop(ui_export_, "ui_opt_export_mode", text="")
    col.prop(ui_export_, "ui_opt_cust_vn_face", text="")
    col.prop(ui_export_, "ui_opt_export_mdx_obj", text="")

    # animation box
    box = layout.box()
    col = box.column_flow(columns=1, align=True)
    col.prop(ui_export_, "ui_opt_animated")  # export animation
    sub = col.row(align=True)
    sub.enabled = ui_export_.ui_opt_animated
    sub.prop(ui_export_, "ui_opt_fr_start")      # frame start number
    sub.prop(ui_export_, "ui_opt_fr_end")        # frame end number

    # advanced opt
    split= box.split()
    split.label(text="")
    split.prop(ui_export_, "ui_opt_is_hd") #, icon="MOD_DECIM")


def execute_export(self, context):
    """ export selected models """
    # print headder
    ver = bl_info["version"]
    print("\n=======================\n" +
          "Kingpin Model Exporter.\n" +
          "Version: (%i.%i.%i)\n" % (ver[0], ver[1], ver[2]) +
          "=======================")

    # store current frame
    cur_frame = bpy.context.scene.frame_current

    # store selected objects
    cur_mode, act_obj, sel_objs = kpc.set_mode_get_obj(context)
    objects_sel = kpc.get_mesh_objects(sel_objs)
    # store all scene objects (bbox size)
    objects_vis = kpc.get_mesh_objects(context.visible_objects)
    # specific player mesh
    objects_player = [o for o in objects_vis if o.name[:4].lower() in ["head", "body", "legs"]]

    # deselect any objects
    for obj in sel_objs:
        kpc.set_select_state(obj, False)
    if act_obj:
        kpc.set_select_state(act_obj, False)

    # set output type
    fpath_, fname_ = os.path.split(self.filepath)
    fname_, fext_ = os.path.splitext(fname_)

    if fext_ == ".mdx":
        isMdx = True
    elif fext_ == ".md2":
        isMdx = False
    else:
        user_prefs = kpc.get_addon_preferences()
        if user_prefs.pref_kp_file_ext:
            fext_ = ".mdx"
            isMdx = True
        else:
            fext_ = ".md2"
            isMdx = False

    ret = Export_MD2_fn(self,
        objects_sel ,objects_vis, objects_player,
        fpath_, fname_, fext_, isMdx)
    # #### export done #####

    bpy.context.scene.frame_set(cur_frame)  # set current frame
    for obj in sel_objs:  # select inital objects
        kpc.set_select_state(obj, True)
    if act_obj:  # return to edit mode
        kpc.set_objects_active(bpy.context, act_obj)
        bpy.ops.object.mode_set(mode=cur_mode)

    if ret:
        self.report({"WARNING"}, "Error: see console")
    else:
        self.report({"INFO"}, "Export Model: Done")
    print("=======================")


class KINGPIN_Export_Dialog(Operator, ExportHelper, kpc.KINGPIN_FileSelect_md2_Params):
    """ Export selection to Kingpin file format (md2/mdx)
        note: popup export window
    """
    bl_idname = "kp.export_model_dialog"
    bl_label = "Export md2/mdx"
    # bl_options = {'REGISTER'}
    bl_description = "Export selection to Kingpin file format (md2/mdx)"
    filename_ext = {".mdx", ".md2"}  # md2 used later
    check_extension = False  # 2.8 allow typing md2/mdx

    def execute(self, context):
        execute_export(self, context)
        return {"FINISHED"}

    def draw(self, context):
        draw_export(self, context, False)

    def invoke(self, context, event):
        """ check selected objets.
            get scene start/end from timeline
        """
        ui_export_ = context.window_manager.kp_export_
        ui_export_.ui_opt_fr_start = context.scene.frame_start
        ui_export_.ui_opt_fr_end = context.scene.frame_end

        obj_sel = kpc.get_objects_selected(context)
        if len(obj_sel) == 0:
            self.report({"ERROR"}, "Please, select an object to export!")
            return {"CANCELLED"}

        user_prefs = kpc.get_addon_preferences()
        if user_prefs and user_prefs.pref_kp_meshname:
            fname = os.path.splitext(obj_sel[0].name)
            if fname[1] == ".mdx":
                self.filepath = obj_sel[0].name
            elif fname[1] == ".md2":
                self.filepath = obj_sel[0].name
            else:
                # no extension found in mesh name. append prefered ext
                if user_prefs.pref_kp_file_ext:
                    self.filepath = bpy.path.ensure_ext(obj_sel[0].name, ".mdx")
                else:
                    self.filepath = bpy.path.ensure_ext(obj_sel[0].name, ".md2")
            # filePath = bpy.path.ensure_ext(filepath, self.filename_ext[0])

        context.window_manager.fileselect_add(self)

        return {"RUNNING_MODAL"}


def setupInternalArrays_fn(export_mdls, cfg: kpc.export_cfg, numFrames):
    """get selected mesh data and store
       also store all viewable mesh for player models
    """
    start_time = kpc.printStart_fn()  # reset timmer
    prefix = "Getting mesh/anim data"
    scene = bpy.context.scene
    start_frame = cfg.ui_opt_fr_start
    cust_vn = cfg.ui_opt_cust_vn
    apply_modifyer = cfg.ui_opt_apply_modify

    for frame in range(numFrames):
        if numFrames < 50 or (frame % 20) == 0:
            kpc.printProgress_fn(frame, numFrames, prefix)  # print progress

        # --------------------------------------------
        # TODO find why this is taking lots of time...
        # 5 seconds with no items to seek 700 frames
        if cfg.ui_opt_animated:  # dont move frame unless animated
            frame_idx = start_frame + frame
            scene.frame_set(frame_idx)
        # --------------------------------------------

        # get bounds for head+body+legs
        if cfg.ui_opt_is_player:  # isPlayer
            mesh_data = None # shared bbox
            for mdl in export_mdls:
                if len(mdl.mdl_objs_player) == 0:
                    continue
                if mesh_data is None:
                    mesh_data = kpc.getMeshArrays_fn(mdl.mdl_objs_player)
                mdl.frMeData_BBox.append(mesh_data)

        for mdl in export_mdls:
            if not mdl.valid:
                continue
            if len(mdl.mdl_objs) == 0:
                mdl.valid = False
                continue

            mesh_data = kpc.getMeshArrays_fn(
                mdl.mdl_objs, #obj_sel,
                getUV=bool(frame == 0),  # ignore uv for animated frames
                apply_modifyer=apply_modifyer,
                custom_vn=cust_vn)
            mdl.frMeData.append(mesh_data)

    kpc.printDone_fn(start_time, prefix)  # Done.
    print("===============")
# end setupInternalArrays_fn


def write_frame_fn(mdl, cfg, file, frame, frameName="frame"):
    """ build frame data """
    bbox_min = mdl.bbox_min[frame][0:3]
    bbox_max = mdl.bbox_max[frame][0:3]

    # BL: some caching to speed it up:
    # -> sd_ gets the vertices between [0 and 255]
    #    which is our important quantization.
    maxXYZ = [(a-b) for a, b in zip(bbox_max, bbox_min)]  # bbox size
    scaleXYZ = [a / 255.0 for a in maxXYZ]
    isdXYZ = [float(65280.0 / a) if a != 0.0 else 0.0 for a in maxXYZ]

    # note about the scale: self.object.scale is already applied via matrix_world
    data = struct.pack(
        "<6f16s",
        *scaleXYZ[0:3],  # write scale of the model
        *bbox_min[0:3],  # write offset (min bounding box)
        kpc.string_to_bytes(frameName, 16))  # write frame name.
    file.write(data)  # frame header

    ###########################
    # write vertex X,Y,Z,lightNormalID
    # ofsetVertID = 0  # multi object
    # frames
    v8 = [0, 0, 0]
    v16 = [0, 0, 0]
    meData = []
    VecHD = namedtuple("VecHD", "x2 y2 z2 x1 y1 z1") #2byte, 1byte
    for mIdx, tmp_mesh in enumerate(mdl.frMeData[frame]):  # object/s
        # vertex data
        vData = []
        for vIdx, vert in enumerate(tmp_mesh.md_xyz_vert):
            # find the closest normal for every vertex
            bestNormalIndex = mdl.vNormData[frame][mIdx][vIdx]
            # write vertex pos and normal. (compressed position. 256 units)
            v16[0:3] = [int((a - b) * c + 0.5) for a, b, c in zip(vert, bbox_min, isdXYZ)]
            v8[0:3] = [(x + 128) >> 8 for x in v16[0:3]] # MH: compresion
            data = struct.pack("<4B", *v8, bestNormalIndex)
            file.write(data)  # write vertex and normal
            vData.append(VecHD(*v16, *v8))
        meData.append(vData)

    if cfg.ui_opt_is_hd is True:  # save an extra byte (HD)
        for ob_verts in meData:
            for vHD in ob_verts:
                data = struct.pack(  # HD vertex. 256 subdivision
                    "<3b",
                    vHD.x2 - (vHD.x1 << 8),  # MH: compresion
                    vHD.y2 - (vHD.y1 << 8),  # MH: compresion
                    vHD.z2 - (vHD.z1 << 8))  # MH: compresion
                file.write(data)
# end write_frame_fn


def setup_data_fn(cfg: kpc.export_cfg, export_mdls: kpc.mdl_export=None):  # context):
    """ build a valid model and export """

    def buildGLcommands_fn(mdl, cfg):
        """ build gl commands """
        start_time = kpc.printStart_fn()  # reset timmer
        prefix = "Calculate GLCommands"
        kpc.printProgress_fn(0, 1, prefix)  # print progress

        def find_uv_islands(face_data, uv_data, num_faces, face_mats):
            """
            Groups all triangles into isolated UV islands.
            """
            # 1. Map every unique (Vertex, UV) pair to the triangles that share it
            vert_to_tris = {}
            for tri_idx in range(num_faces):
                tbase = tri_idx * 3
                m = face_mats[tri_idx]
                for k in range(3):
                    v = face_data[tbase + k]
                    u = uv_data[tbase + k]
                    key = (v, u, m)
                    if key not in vert_to_tris:
                        vert_to_tris[key] = []
                    vert_to_tris[key].append(tri_idx)

            # 2. Flood fill to group connected triangles together
            unvisited = set(range(num_faces))
            uv_islands = []

            while unvisited:
                start_tri = unvisited.pop()
                current_island = [start_tri]

                queue = deque([start_tri])

                while queue:
                    curr_tri = queue.popleft()
                    tbase = curr_tri * 3

                    # Check all 3 corner points of the current triangle
                    for k in range(3):
                        v = face_data[tbase + k]
                        u = uv_data[tbase + k]
                        m = face_mats[curr_tri]

                        # Grab all other triangles that share this exact corner point
                        shared_tris = vert_to_tris.get((v, u, m), [])

                        for neighbor in shared_tris:
                            if neighbor in unvisited:
                                unvisited.remove(neighbor)
                                current_island.append(neighbor)
                                queue.append(neighbor)  # Flood outward through this neighbor

                uv_islands.append(current_island)

            return uv_islands
        # end find_uv_islands

        def findStripLength_fn(tri_neighbour, face_data, uv_data, usedFace, startTri, startVert):
            """ Build the longest possible triangle strip starting from one edge,
            extending both forward AND backward. """

            # Pick the starting edge (in correct winding order for strip)
            vIdx = startTri * 3
            verts = face_data[vIdx : vIdx + 3]
            uvs   = uv_data[vIdx : vIdx + 3]
            v0, v1, v2 = verts[startVert:] + verts[:startVert] # mod
            u0, u1, u2 = uvs[startVert:]   + uvs[:startVert] # mod

            # Reversed initial order to match engine winding
            cmdVerts = [v0, v2, v1]
            cmdUV = [u0, u2, u1]
            cmdTris = [startTri]

            length = 1  # number of triangles so far
            usedFace[startTri] = 2

            # === FORWARD extension ===
            v_m1, v_m2 = v1, v2
            u_m1, u_m2 = u1, u2
            while True:
                # Look up the edge directly. No loops!
                match = tri_neighbour.get((v_m2, u_m2, v_m1, u_m1))

                if match:
                    triIdx, next_v, next_u = match
                    if usedFace[triIdx] == 0:
                        cmdVerts.append(next_v)
                        cmdUV.append(next_u)
                        cmdTris.append(triIdx)
                        usedFace[triIdx] = 2

                        if length & 1:  # Flip
                            v_m2, u_m2 = cmdVerts[-1], cmdUV[-1]
                        else:
                            v_m1, u_m1 = cmdVerts[-1], cmdUV[-1]
                        length += 1
                        continue  # Edge matched and processed, keep stripping forward

                break  # No match or triangle already used, exit loop safely

            # === BACKWARD extension ===
            v_m1, v_m2 = v0, v2
            u_m1, u_m2 = u0, u2
            count_back = 0
            found_edge = length > 1  # skip if none forward
            while found_edge:
                found_edge = False
                # Match back edge (reverse windings logic)
                match = tri_neighbour.get((v_m1, u_m1, v_m2, u_m2))

                if match:
                    triIdx, next_v, next_u = match
                    if usedFace[triIdx] == 0:
                        # Insert directly at the front of the list
                        cmdVerts.insert(0, next_v)
                        cmdUV.insert(0, next_u)
                        cmdTris.insert(0, triIdx)
                        usedFace[triIdx] = 2
                        count_back += 1

                        # Alternating winding flip for backward insertion
                        if count_back & 1:
                            v_m2, u_m2 = cmdVerts[0], cmdUV[0]
                        else:
                            v_m1, u_m1 = cmdVerts[0], cmdUV[0]
                        length += 1
                        found_edge = True
                        continue  # Match found, loop again
                # break  # No match or triangle already used, exit loop safely

            # remove if odd num triangles added
            if count_back and (count_back & 1) == 1:
                usedFace[cmdTris[0]] = 0
                cmdVerts.pop(0)
                cmdUV.pop(0)
                cmdTris.pop(0)
                length -= 1

            # Clean up temp marks
            for tri in cmdTris:
                usedFace[tri] = 0

            return length, cmdTris, cmdVerts, cmdUV, 0 #cmdType
        # end findStripLength_fn

        def findFanLength_fn(tri_neighbour, face_data, uv_data, usedFace, startTri, startVert):
            """ triangle fan """
            usedFace[startTri] = 2 # mark temp use

            # copy edge
            vIdx = startTri * 3
            verts = face_data[vIdx : vIdx + 3]
            uvs   = uv_data[vIdx : vIdx + 3]
            v0, v1, v2 = verts[startVert:] + verts[:startVert] # mod
            u0, u1, u2 = uvs[startVert:]   + uvs[:startVert] # mod

            # store first tri
            cmdVerts = [v0, v2, v1]
            cmdUV = [u0, u2, u1]
            cmdTris = [startTri]

            cmdLength = 1

            pivot_v, pivot_u = v0, u0
            last_v, last_u = v1, u1

            while True:
                # Look up the edge radiating from the pivot
                match = tri_neighbour.get((last_v, last_u, pivot_v, pivot_u))
                if match:
                    triIdx, next_v, next_u = match
                    if usedFace[triIdx] == 0: # unused
                        cmdVerts.append(next_v)
                        cmdUV.append(next_u)
                        cmdTris.append(triIdx)
                        usedFace[triIdx] = 2
                        cmdLength += 1
                        last_v, last_u = next_v, next_u
                        continue
                break # No match or triangle already used, exit loop safely

            # Clean up temporary marks
            for tri in cmdTris:
                usedFace[tri] = 0

            return cmdLength, cmdTris, cmdVerts, cmdUV, 1 #cmdType fan
        # end findFanLength_fn

        def build_neighbour(island_data, face_data, uv_data):
            """
            Scans the island geometry once and returns a fast hash map
            for directed edge lookups.
            """
            edge_to_tri = {}
            for triIdx in island_data:
                tbase = triIdx * 3

                # Get all three vertices & UV positions for this triangle
                v0, u0 = face_data[tbase],     uv_data[tbase]
                v1, u1 = face_data[tbase + 1], uv_data[tbase + 1]
                v2, u2 = face_data[tbase + 2], uv_data[tbase + 2]

                # Map each directed edge to its triangle ID and the REMAINING opposite vertex.
                # This allows us to instantly grab the third vertex when an edge matches.
                edge_to_tri[(v0, u0, v1, u1)] = (triIdx, v2, u2)
                edge_to_tri[(v1, u1, v2, u2)] = (triIdx, v0, u0)
                edge_to_tri[(v2, u2, v0, u0)] = (triIdx, v1, u1)

            return edge_to_tri
        #end build_neighbour

        # mdx hitbox index number. adds material ID
        mdxID = 0  # TODO should this be bit index?

        ofsetVertID = 0   # multi object offset
        numCommands = 1  # add 1 for final NULL at end
        # loop through selected mesh/s
        for tmp_mesh in mdl.frMeData[0]:
            numFaces = tmp_mesh.md_face_count
            face_data = tmp_mesh.md_idc_vert
            uv_data = tmp_mesh.md_idc_uv
            face_mats = tmp_mesh.md_face_mat

            # pre-sort uv into groups
            uv_islands = find_uv_islands(face_data, uv_data, numFaces, face_mats)

            usedFace = [0] * numFaces  # has face been used. array
            # break up mesh for quicker processing.
            for island_data in uv_islands:
                if len(island_data) == 0:
                    continue
                tri_neighbour = build_neighbour(island_data, face_data, uv_data)

                # loop through face in uv group
                unvisited = set(island_data)
                while unvisited:
                    # Grab a starting seed triangle
                    startTri = next(iter(unvisited))

                    test_results = [
                        findStripLength_fn(tri_neighbour, face_data, uv_data, usedFace, startTri, sv)
                            for sv in range(3)]
                    test_results.extend([
                        findFanLength_fn(tri_neighbour, face_data, uv_data, usedFace, startTri, sv)
                            for sv in range(3)])
                    bestLength, bestTris, bestVerts, bestUV, bestType = max(test_results, key=lambda x: x[0])

                    unvisited.difference_update(bestTris)

                    # mark tringle as used
                    for tri in bestTris:
                        usedFace[tri] = 1

                    numType = (bestLength + 2) if bestType == 0 else -(bestLength + 2)
                    numCommands += 1  # tri type/count

                    if cfg.isMdx:  # mdx
                        numCommands += 1  # sub-object number

                    cmd = []
                    uv_layer = tmp_mesh.md_xy_uv  # uv_cords
                    for i in range(bestLength + 2):
                        cmd.append((
                            0.0 + uv_layer[bestUV[i]][0],  # X uv cords
                            1.0 - uv_layer[bestUV[i]][1],  # Y uv cords
                            bestVerts[i] + ofsetVertID))   # vertex number
                        numCommands += 3
                    o_id = mdxID + face_mats[bestTris[0]] # material id
                    mdl.glCmdList.append((
                        numType,  # type/count (neg=fan pos=strip)
                        o_id,    # object number
                        cmd))     # S, T, vIdx...

            #  multi part object offset
            # ofsetVertID += len(tmp_mesh.md_xyz_vert)
            ofsetVertID += tmp_mesh.md_vert_count
            # if cfg.ui_opt_use_hitbox:
            mdxID += tmp_mesh.md_mat_count

        kpc.printDone_fn(start_time, prefix)  # Done.
        mdl.numGLCmds = numCommands
    # end buildGLcommands_fn

    # TODO
    def getSkins_fn(mdl: kpc.mdl_export, cfg: kpc.export_cfg):
        """ _ """
        def stripLeadingPath(path):
            tmpPath = bpy.path.abspath(path)  # , library=n.image.library)
            tmpPath = os.path.normpath(tmpPath)
            tmpPath = tmpPath.replace("\\", "/")
            texname = ""
            modelIdx = tmpPath.find("models" + os.sep)
            plyerIdx = tmpPath.find("players" + os.sep)
            textrIdx = tmpPath.find("textures" + os.sep)
            if modelIdx >= 0:
                texname = tmpPath[modelIdx:]
            elif plyerIdx >= 0:
                texname = tmpPath[plyerIdx:]
            elif textrIdx >= 0:
                texname = tmpPath[textrIdx:]
            else:
                texname = tmpPath
            return texname

        def appendSkins(skins, texname):
            if texname and len(texname) > 0:
                if texname not in skins and len(skins) <= kpc.MD2_MAX_SKINS:
                    skins.append(texname)

        def appendValidMaterial(skins, image):
            # set skin
            if method == "SKIN_MAT_NAME":
                appendSkins(skins, image)


        def appendValidSkins(skins, image):
            # set skin
            if method == "SKIN_TEX_NAME":
                appendSkins(skins, image.name)
            elif method == "SKIN_TEX_PATH":
                appendSkins(skins, stripLeadingPath(image.filepath))

        def updateWH(size, W, H):
            width = max(size[0], W)
            height = max(size[1], H)
            return width, height

        start_time = kpc.printStart_fn()  # reset timmer
        prefix = "Calculate Skins"
        kpc.printProgress_fn(0, 1, prefix)  # print progress
        skins = []
        width, height = 0, 0
        obj_sel = mdl.mdl_objs
        method = cfg.ui_opt_tex_name

        materials = [mat for obj in obj_sel for mat in obj.data.materials if mat]
        for mat in materials:
            appendValidMaterial(skins, mat.name) # material name

            # use nodes to get skin size/name.
            if mat.use_nodes:
                # search node images for dimensions/name
                for n in mat.node_tree.nodes:
                    if n and n.type == "TEX_IMAGE" and n.image:
                        image = n.image
                        width, height = updateWH(image.size, width, height)  # set image size
                        appendValidSkins(skins, image) # image
            # B2.7 use "texture"
            elif hasattr(mat, "texture_slots"):
                # search texture slots for dimensions/name
                for mtex in mat.texture_slots:
                    if (mtex and mtex.texture and mtex.use_map_color_diffuse
                        and mtex.texture.image and mtex.texture.type == "IMAGE"
                    ):
                        image = mtex.texture.image
                        width, height = updateWH(image.size, width, height)  # set image size
                        appendValidSkins(skins, image) # image

        kpc.printDone_fn(start_time, prefix)  # Done.

        mdl.skin_print = "  Skin  W: {}  H: {}  Count: {}\n".format(width, height, len(skins))
        for idx, skin in enumerate(skins):
            mdl.skin_print += "  Skin{}:  \'{}\' \n".format(idx + 1, skin[0:kpc.MD2_MAX_SKINNAME - 1])
        if height > 480 or width > 480:
            print("NOTE: found texture larger than kingpin max 480px")

        # set min/max (kp crashes with more then 480, but is not use by opengl render)
        width = kpc.forceMinMaxRange(width, 16, 2048)
        height = kpc.forceMinMaxRange(height, 16, 480) # kingpin checks heigt

        mdl.skinWidth, mdl.skinHeight = width, height
        mdl.skins = skins
        mdl.numSkins = len(skins)
    # end getSkins_fn

    def buildFrameNames_fn(cfg: kpc.export_cfg, numFrames):
        """
        sort the markers. The marker with the frame number closest to 0 will be the first marker in the list.
        The marker with the biggest frame number will be the last marker in the list
        """
        names = []
        timeLineMarkers = []
        scene = bpy.context.scene
        start_fr = cfg.ui_opt_fr_start

        if scene.timeline_markers:
            for marker in scene.timeline_markers:
                timeLineMarkers.append(marker)

        timeLineMarkers.sort(key=lambda marker: marker.frame)
        # delete markers at same frame positions
        if len(timeLineMarkers) > 1:
            markerFrame = timeLineMarkers[len(timeLineMarkers) - 1].frame
            for i in range(len(timeLineMarkers) - 2, -1, -1):
                if timeLineMarkers[i].frame == markerFrame:
                    del timeLineMarkers[i]
                else:
                    markerFrame = timeLineMarkers[i].frame

        mark_count = len(timeLineMarkers)
        # empty list, just add numbers
        if mark_count == 0:
            return ["frame_%02d" % (fr) for fr in range(numFrames)]

        names = []
        fNameIdx = 0
        markerIdx = 0
        #find start frame
        for i, mk in enumerate(timeLineMarkers):
            if mk.frame == start_fr:
                markerIdx = i
                break

        for frame in range(numFrames):
            cur_fr = start_fr + frame
            fNameIdx += 1
            # build frame names
            if markerIdx + 1 < mark_count:
                next_fr = timeLineMarkers[markerIdx + 1].frame
                if cur_fr >= next_fr:
                    markerIdx += 1
                    fNameIdx = 1
            names.append(timeLineMarkers[markerIdx].name + ("%02d" % fNameIdx))
        return names
    # end buildFrameNames_fn

    def calcSharedBBox_fn(mdl, numFrames):
        """ option to make bbox size across all frames the same
            this fixes vertex wobble in parts of mesh that dont move
        """
        # mdl.bbox_min = []
        # self.bbox_max = []  # clear bbox
        start_time = kpc.printStart_fn()  # reset timmer
        # print("=====")
        prefix = "Calculate bounds"

        for frame in range(numFrames):
            bbox_min = [9999.0, 9999.0, 9999.0]
            bbox_max = [-9999.0, -9999.0, -9999.0]
            tmp_bounds = []
            # calculate quantizer, from head+body+legs
            if mdl.isPlayer:
                meshes = mdl.frMeData_BBox[frame]
            else:
                meshes = mdl.frMeData[frame]
            for tmp_mesh in meshes:
                tmp_bounds.extend(tmp_mesh.md_xyz_vert)
            # numpy
            verts = np.array(tmp_bounds)
            bbox_min = np.min(verts, axis=0)
            bbox_max = np.max(verts, axis=0)

            # add new bbox for each frame
            mdl.bbox_min.append(bbox_min)
            mdl.bbox_max.append(bbox_max)
        kpc.printDone_fn(start_time, prefix)  # Done.
    # end calcSharedBBox_fn

    def calculateHitBox_fn(mdl, cfg: kpc.export_cfg, numFrames):
        """
        mdx hitbox.
        saved order.
        ob1[all frames], ob2[all frames]
        ob1.mat1[all frames], ob1.mat2[all frames], ob2.mat1[all frames],
        """
        start_time = kpc.printStart_fn()  # reset timmer
        prefix = "Calculate mdx hitbox"

        if cfg.ui_opt_mat_hitbox:  # skin+object based hitbox
            # Pre-compute per-object, per-material vertex index arrays (once)
            mat_vert_idx = []
            for tmp_mesh in mdl.frMeData[0]:
                groups = [[] for _ in range(tmp_mesh.md_mat_count)]
                for tri_i, mat in enumerate(tmp_mesh.md_face_mat):
                    base = tri_i * 3
                    groups[mat].extend(tmp_mesh.md_idc_vert[base:base+3])
                mat_vert_idx.append([
                    np.array(sorted(set(g))) if g else np.array([], dtype=int)
                    for g in groups
                ])

            mdl.numSubObjects = sum(tmp.md_mat_count for tmp in mdl.frMeData[0])

            for frame in range(numFrames):
                hitboxTmp = []
                for obj_i, tmp_mesh in enumerate(mdl.frMeData[frame]):
                    verts_all = np.array(tmp_mesh.md_xyz_vert)
                    for mat_i in range(tmp_mesh.md_mat_count):
                        v_idx = mat_vert_idx[obj_i][mat_i]
                        if len(v_idx) == 0:
                            # No faces for this material — skip or use full obj
                            hitboxTmp.append([0, 0, 0, 0, 0, 0])
                            continue
                        verts = verts_all[v_idx]
                        hitboxTmp.append([
                            *np.min(verts, axis=0),
                            *np.max(verts, axis=0),
                        ])
                mdl.hitbox.append(hitboxTmp)
        elif cfg.ui_opt_use_hitbox: # object based hitbox
            mdl.numSubObjects = len(mdl.frMeData[0])
            # each object has seperate hitbox
            for frame in range(numFrames):
                hitboxTmp = []
                for tmp_mesh in mdl.frMeData[frame]:
                    verts = np.array(tmp_mesh.md_xyz_vert)
                    # add each object
                    hitboxTmp.append([
                        *np.min(verts, axis=0),
                        *np.max(verts, axis=0)
                    ])
                # add to frame
                mdl.hitbox.append(hitboxTmp)
        else: #if not mdl.isPlayer:
            for frame in range(numFrames):
                hitboxMin = mdl.bbox_min[frame]
                hitboxMax = mdl.bbox_max[frame]
                mdl.hitbox.append([[*hitboxMin[0:3], *hitboxMax[0:3]]]) # 1 object

            mdl.numSubObjects = 1
        # else: #TODO reuse shared bbox across frames
        #     # merge into 1 hit box
        #     for frame in range(numFrames):
        #         all_verts = []
        #         for tmp_mesh in mdl.frMeData[frame]:
        #             all_verts.extend(tmp_mesh.md_xyz_vert)
        #         verts = np.array(all_verts)
        #         hitboxMin = np.min(verts, axis=0)
        #         hitboxMax = np.max(verts, axis=0)
        #         # add to frame
        #         mdl.hitbox.append([*hitboxMin[0:3], *hitboxMax[0:3]])

        kpc.printDone_fn(start_time, prefix)  # Done.
    # end calculateHitBox_fn

    def calculateVNornIndex_fn(mdl, numFrames, MD2_VN):
        """ find the closest normal for every vertex on all frames """
        start_time = kpc.printStart_fn()  # reset timmer
        prefix = "Calculate vertex normals"
        for frame in range(numFrames):
            if numFrames < 50 or (frame % 20) == 0:
                kpc.printProgress_fn(frame, numFrames, prefix)  # print progress
            m_tmp = []
            for tmp_mesh in mdl.frMeData[frame]:
                _vn_ = np.array(tmp_mesh.md_xyz_norm)
                # Calculate dot products for all vn vectors against MD2_VN
                dot_products = np.dot(_vn_, MD2_VN.T)  # Shape: (number of vns, 162)

                # Find the best index for each normal vector
                best_indices = np.argmax(dot_products, axis=1).tolist()

                m_tmp.append(best_indices)
            mdl.vNormData.append(m_tmp)  # frame
            del m_tmp
        kpc.printDone_fn(start_time, prefix)  # Done.
    # end calculateVNornIndex_fn

    def get_numTris(mdl, cfg):
        triCount = 0  # self.numTris
        for tmp_mesh in mdl.frMeData[0]:
            triCount += tmp_mesh.md_face_count

        if cfg.ui_opt_is_hd is True:
            if triCount > kpc.MDX5_MAX_TRIANGLES:
                raise RuntimeError(
                    "Object has too many (triangulated) faces (%i), at most %i are supported in mdx HD"
                    % (triCount, kpc.MDX5_MAX_TRIANGLES))
        else:
            if triCount > kpc.MD2_MAX_TRIANGLES:
                raise RuntimeError(
                    "Object has too many (triangulated) faces (%i), at most %i are supported in md2"
                    % (triCount, kpc.MD2_MAX_TRIANGLES))
        mdl.numTris = triCount
    # end get_numTris

    def get_numVerts(mdl, cfg):
        vertCount = 0  # self.numVerts
        for tmp_mesh in mdl.frMeData[0]:
            vertCount += tmp_mesh.md_vert_count

        if cfg.ui_opt_is_hd is True:
            if vertCount > kpc.MDX5_MAX_VERTS:
                raise RuntimeError(
                    "Object has too many (triangulated) faces (%i), at most %i are supported in mdx HD"
                    % (vertCount, kpc.MDX5_MAX_VERTS))
        else:
            if vertCount > kpc.MD2_MAX_VERTS:
                raise RuntimeError(
                    "Object has too many (triangulated) faces (%i), at most %i are supported in md2"
                    % (vertCount, kpc.MD2_MAX_VERTS))
        mdl.numVerts = vertCount
    # end get_numVerts

    def get_numUV(mdl):
        uvCount = 0
        for tmp_mesh in mdl.frMeData[0]:
            uvCount += tmp_mesh.md_uv_count
        return uvCount
    # end get_numUV

    def get_framesize(mdl, cfg):
        if cfg.ui_opt_is_hd:
            mdl.frameSize = struct.calcsize("<6f16s") + (struct.calcsize("<7B") * mdl.numVerts)
        else:
            mdl.frameSize = struct.calcsize("<6f16s") + (struct.calcsize("<4B") * mdl.numVerts)
    # end get_framesize

    # ##### #
    # start #
    # ##### #
    if export_mdls is None or len(export_mdls) == 0:
        raise ValueError("No models to export.")
    if not cfg.ui_opt_is_player and not export_mdls[0].valid: # must be atleast 1
        raise ValueError("No model to export.")

    if not cfg.ui_opt_animated:
        numFrames = 1
    else:
        numFrames = min(1 + cfg.ui_opt_fr_end - cfg.ui_opt_fr_start, kpc.MD2_MAX_FRAMES)

    # animated, get all objects frame state at once
    setupInternalArrays_fn(export_mdls, cfg, numFrames)  # generate mesh/objects

    #build frames names from timeline
    frameNames = buildFrameNames_fn(cfg, numFrames)  # setup frame names

    # speedup vertex normal index searching
    MD2_VN = np.array(kpc.MD2_VN) #md2 vertex index

    # combine models
    for mdl in export_mdls:
        if not mdl.valid:
            continue
        print("Calculating... %s%s" % (mdl.save_name, cfg.f_ext))

        mdl.numFrames = numFrames
        mdl.frameNames = frameNames
        getSkins_fn(mdl, cfg)  # get texture names
        calcSharedBBox_fn(mdl, numFrames)  # get min/max dimensions
        calculateVNornIndex_fn(mdl, numFrames, MD2_VN)
        get_numVerts(mdl, cfg)
        get_numTris(mdl, cfg)
        buildGLcommands_fn(mdl, cfg)
        get_framesize(mdl, cfg)

        # setup md2/mdx header
        if cfg.isMdx:
            calculateHitBox_fn(mdl, cfg, numFrames)  # mdx
            mdl.hdr = kpc.mdx_hdr_export(mdl, cfg)
        else:
            numUV = get_numUV(mdl)
            mdl.hdr = kpc.md2_hdr_export(mdl, numUV)

        print(mdl.skin_print, end="") # add to end
        print("---------------")
    # Done..
    # print("===============")


def write_fn(filePath, mdl, cfg):
    """ write file """

    start_time = kpc.printStart_fn()  # reset timmer
    prefix = "  %s%s" % (mdl.save_name, cfg.f_ext)
    #
    with open(filePath, "wb") as file:
        # ####################
        # ### write header ###
        data = mdl.hdr.pack_header() #mdx/2_hdr_export
        file.write(data)

        # #############################
        # ### write skin file names ###
        for skinName in mdl.skins:  # enumerate(# TODO file path?
            data = struct.pack("<64s", kpc.string_to_bytes(skinName, 64))
            file.write(data)  # skin name

        # ###############################
        # ### write software uv byte ###
        if not cfg.isMdx:  # MD2
            def clamp16(v):
                return max(-32768, min(32767, v))

            for tmp_mesh in mdl.frMeData[0]:
                for uv in tmp_mesh.md_xy_uv:
                    data = struct.pack(
                        "<2h",
                        int(uv[0] * mdl.skinWidth),
                        int(1-uv[1] * mdl.skinHeight))
                    file.write(data)  # uv

        # #################################
        # ### write triangle index data ###
        ofset_face = 0
        ofset_uv = 0
        for mesh in mdl.frMeData[0]:
            face = mesh.md_idc_vert
            uv = mesh.md_idc_uv
            count_uv = mesh.md_uv_count
            count_vert = mesh.md_vert_count
            count_face = mesh.md_face_count
            for idx in range(count_face):
                # 0,2,1 for good cw/ccw
                f_idx = idx * 3
                data = struct.pack( # signed short
                    "<3h",  # ### write vert indices ###
                    face[f_idx + 0] + ofset_face,
                    face[f_idx + 2] + ofset_face,
                    face[f_idx + 1] + ofset_face)
                file.write(data)  # vert uv index data

                data = struct.pack( # signed short
                    "<3h",  # ### write tex cord indices ###
                    uv[f_idx + 0] + ofset_uv,  # (uv idc)
                    uv[f_idx + 2] + ofset_uv,  # (uv idc)
                    uv[f_idx + 1] + ofset_uv)  # (uv idc)
                file.write(data)  # uv index

            ofset_face += count_vert
            ofset_uv += count_uv

        # ####################
        # ### write frame/s ###
        for frame in range(mdl.numFrames):
            if mdl.numFrames < 50 or (frame % 20) == 0:
                kpc.printProgress_fn(frame, mdl.numFrames, prefix)  # print progress

            # output frames to file
            write_frame_fn(mdl, cfg, file, frame, mdl.frameNames[frame])
        ###########################
        # ### write GL Commands ###
        for glCmd in mdl.glCmdList:
            if cfg.isMdx:
                # TrisTypeNum, SubObjectID
                data = struct.pack("<iL", *glCmd[:2])
            else:
                 # TrisTypeNum
                data = struct.pack("<i", *glCmd[:1])
            file.write(data)

            for cmd in glCmd[2]:
                #U, V, v-index
                data = struct.pack("<ffI", *cmd[:3])
                file.write(data)
        # NULL GLCommand
        data = struct.pack("<I", 0)
        file.write(data)

        ###################
        # ### mdx stuff ###
        if cfg.isMdx:
            # ofsVertexInfo #mdx
            for mdxObj, tmp_mesh in enumerate(mdl.frMeData[0]):
                for _ in range(tmp_mesh.md_vert_count):
                    bits = 1 << mdxObj if cfg.ui_opt_use_hitbox else 1
                    data = struct.pack("<i", bits)  # fill as object #1 TODO
                    file.write(data)  # vert index

            # ofsSfxDefines #mdx
            # ofsSfxEntries #mdx
            # ofsBBoxFrames #mdx
            for mdxObj in range(mdl.hdr.numSubObjects):
                for fr in range(mdl.hdr.numFrames):
                    data = struct.pack("<6f", *mdl.hitbox[fr][mdxObj][:6])
                    file.write(data)
    #finish open with

    kpc.printDone_fn(start_time, prefix)  # Done.
    # print("Model exported.")
    # TODO cleanup arrays
    del mdl.frameNames, mdl.frMeData, mdl.frMeData_BBox, mdl.vNormData


def Export_MD2_fn(self,
        obj_sel ,obj_vis, obj_player,
        fpath_, fname_, fext_, f_ismdx):
    """    Export model    """
    startTime = kpc.printStart_fn()  # total time
    self.start_time = startTime #TODO rename

    cfg = kpc.export_cfg(fpath_, fname_, fext_, f_ismdx)

    # gather all needed objects. make unique models for multi export
    export_mdls = []
    if cfg.ui_opt_exp_selected:
        # combine selected
        mdl = kpc.mdl_export(obj_sel, False, cfg.f_name.split('.')[0])
        export_mdls.append(mdl)
    else:
        # export multiple files. TODO: file->export is a bit confusing here.
        if cfg.ui_opt_is_player:
            export_mdls.append(kpc.mdl_export(obj_player, True, "head"))
            export_mdls.append(kpc.mdl_export(obj_player, True, "body"))
            export_mdls.append(kpc.mdl_export(obj_player, True, "legs"))
        if cfg.ui_opt_exp_weps or cfg.ui_opt_exp_all:
            for o in obj_vis:
                if o in obj_player: # get weapons etc..
                    continue
                mdl = kpc.mdl_export([o], False, o.name.split('.')[0])
                export_mdls.append(mdl)

    try:
        # build export data
        setup_data_fn(cfg, export_mdls)
        print("Writing...")

        for mdl in export_mdls:
            if mdl.valid:
                name = "%s/%s%s" % (cfg.f_path, mdl.save_name, cfg.f_ext) # filepath
                write_fn(name, mdl, cfg) # todo fix export names

        # total time
        kpc.printDone_fn(startTime, "Total time")  # Done.

    except IOError:
        print("IO Error")
        return True
    except Exception as e:
        print("Caught error exporting model")
        print(e)
        # traceback.print_exc()
        # raise RuntimeError("Only mesh objects can be exported")
        return True

    return False
