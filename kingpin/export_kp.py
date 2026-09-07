"""
md2/mdx exporter
"""

import bpy
import os
import struct
import numpy as np
# import traceback
from collections import defaultdict, deque
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
        name="HD Version",
        description=(
            "Export HD version. 2byte vertex pos. Backward compatable with engine and some viewers.\n" +
            "Note: requires MH patch to view in kingpin. without the wobble :)"
        ),
        default=True
    )
    ui_opt_cust_vn = BoolProperty(
        name="Custom Vertex Normals",
        description=(
            "Use custom vertex normals instead of average normal.\n" +
            "Note: Vertex are not split on hard edges"
        ),
        default=False
    )
    ui_opt_is_player = BoolProperty(
        name="Player Model", # Seam Fix (Player etc.)",
        description=(
            "Export all \'head\' \'body\' \'legs\' named objects. using a shared quantizer.\n" +
            "Usage: Show all head, body, legs objects. Click export. 3 models will be exported.\n" +
            "Note: only use on medels with a shared seam, as it waste precision"
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
        name="Start Frame",
        description="Animated model start frame",
        min=0, max=kpc.MD2_MAX_FRAMES - 1,
        default=0
    )
    ui_opt_fr_end = IntProperty(
        name="End Frame",
        description="Animated model end frame",
        min=0, max=kpc.MD2_MAX_FRAMES - 1,
        default=40
    )
    ui_opt_use_hitbox = BoolProperty(
        name="Player HitBox",
        description=(
            "Export a seperate mdx hitbox for each object. eg hand, arm, torso.\n" +
            "HitBox are used in multiplayer when \"dm_locational_damage 1\" is set on the server\n" +
            "Note: disabled will create 1 large hitbox"
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
        items=((".md2", "MD2", ""), (".mdx", "MDX", "")),
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


def draw_export(self, context):
    ui_export_ = context.window_manager.kp_export_
    layout = self.layout

    # skin chooser box
    layout.prop(ui_export_, "ui_opt_tex_name")  # testure source (dropdown)

    # misc options box
    box = layout.box()
    miscBox = box.column_flow(columns=1, align=True)
    # miscBox.prop(ui_export_, "ui_opt_apply_modify")  # apply modifiers
    # if ui_export_.ui_opt_apply_modify:
    miscBox.prop(ui_export_, "ui_opt_cust_vn")  # custom vertex normals
    miscBox.prop(ui_export_, "ui_opt_is_hd")    # HD version

    # animation box
    box = layout.box()
    animBox = box.column_flow(columns=1, align=True)
    animBox.prop(ui_export_, "ui_opt_animated")  # export animation
    sub = animBox.column_flow(columns=1, align=True)
    sub.enabled = ui_export_.ui_opt_animated
    sub.prop(ui_export_, "ui_opt_fr_start")      # frame start number
    sub.prop(ui_export_, "ui_opt_fr_end")        # frame end number
    # player
    sub.prop(ui_export_, "ui_opt_is_player")     # playermodel
    # weapon
    wep = sub.row()
    wep.prop(ui_export_, "ui_opt_exp_weps")
    # player hitbox
    hitbox = sub.row()
    hitbox.prop(ui_export_, "ui_opt_use_hitbox")  # merge hitbox
    # disable. if not player
    if not ui_export_.ui_opt_is_player: # or not ui_export_.ui_opt_animated:
        wep.enabled = False
        hitbox.enabled = False



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

    # valid mesh?
    ######### disabled...
    # if not kpc.is_selected_mesh(self, self.objects_sel):
    #     return {"FINISHED"}

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

        # self.report({"WARNING"}, "Incorrect file extension. Not md2 or mdx")
        # return {"FINISHED"}

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
        draw_export(self, context)

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

            # TODO this will be run multiple times, check inuse...
            # if mdl.mdl_objs in mdl.mdl_objs_player
            if mdl.isPlayer:
                # get all plyer objects. used for 'bbox'
                mdl.frMeData_BBox.append(kpc.getMeshArrays_fn(mdl.mdl_objs_player))

    kpc.printDone_fn(start_time, prefix)  # Done.
    print("===============")
# end setupInternalArrays_fn


def write_frame_fn(mdl, cfg, file, frame, frameName="frame"):
    """ build frame data """
    bbox_min = mdl.bbox_min[frame]
    bbox_max = mdl.bbox_max[frame]

    # BL: some caching to speed it up:
    # -> sd_ gets the vertices between [0 and 255]
    #    which is our important quantization.
    xMax = bbox_max[0] - bbox_min[0]  # bbox size
    yMax = bbox_max[1] - bbox_min[1]  # bbox size
    zMax = bbox_max[2] - bbox_min[2]  # bbox size
    sdx = xMax / 255.0  # write default scale to file
    sdy = yMax / 255.0  # write default scale to file
    sdz = zMax / 255.0  # write default scale to file

    isdx = float(65280.0 / xMax) if xMax != 0.0 else 0.0
    isdy = float(65280.0 / yMax) if yMax != 0.0 else 0.0
    isdz = float(65280.0 / zMax) if zMax != 0.0 else 0.0

    # note about the scale: self.object.scale is already applied via matrix_world
    data = struct.pack(
        "<6f16s",
        sdx, sdy, sdz,                          # write scale of the model
        bbox_min[0], bbox_min[1], bbox_min[2],  # write offset (min bounding box)
        kpc.string_to_bytes(frameName, 16))     # write frame name.
    file.write(data)  # frame header

    ###########################
    # write vertex X,Y,Z,lightNormalID
    ofsetVertID = 0  # multi object
    # frames
    v8 = [0] * 3
    v16 = [0] * 3
    for mIdx, tmp_mesh in enumerate(mdl.frMeData[frame]):  # object/s
        # vertex data
        for vIdx, vert in enumerate(tmp_mesh[kpc.IDX_XYZ_V]):
            # find the closest normal for every vertex
            bestNormalIndex = mdl.vNormData[frame][mIdx][vIdx]
            # write vertex pos and normal. (compressed position. 256 units)
            v16[0] = int((vert[0] - bbox_min[0]) * isdx + 0.5)  # MH: compresion
            v16[1] = int((vert[1] - bbox_min[1]) * isdy + 0.5)  # MH: compresion
            v16[2] = int((vert[2] - bbox_min[2]) * isdz + 0.5)  # MH: compresion
            v8[0] = (v16[0] + 128) >> 8  # MH: compresion
            v8[1] = (v16[1] + 128) >> 8  # MH: compresion
            v8[2] = (v16[2] + 128) >> 8  # MH: compresion
            data = struct.pack("<4B", v8[0], v8[1], v8[2], bestNormalIndex)
            file.write(data)  # write vertex and normal
        ofsetVertID += len(tmp_mesh[kpc.IDX_XYZ_V])  # TODO

    # HD model. TODO: store above instead of doing it twice
    if cfg.ui_opt_is_hd is True:  # "VERSION5":
        for mIdx, tmp_mesh in enumerate(mdl.frMeData[frame]):
            for vert in tmp_mesh[kpc.IDX_XYZ_V]:
                v16[0] = int((vert[0] - bbox_min[0]) * isdx + 0.5)  # MH: compresion
                v16[1] = int((vert[1] - bbox_min[1]) * isdy + 0.5)  # MH: compresion
                v16[2] = int((vert[2] - bbox_min[2]) * isdz + 0.5)  # MH: compresion
                v8[0] = (v16[0] + 128) >> 8  # MH: compresion
                v8[1] = (v16[1] + 128) >> 8  # MH: compresion
                v8[2] = (v16[2] + 128) >> 8  # MH: compresion
                data = struct.pack(  # HD vertex. 256 subdivision
                    "<3b",
                    v16[0] - (v8[0] << 8),  # MH: compresion
                    v16[1] - (v8[1] << 8),  # MH: compresion
                    v16[2] - (v8[2] << 8))  # MH: compresion
                file.write(data)
            ofsetVertID += len(tmp_mesh[kpc.IDX_XYZ_V])  # TODO not used
# end write_frame_fn


def setup_data_fn(cfg: kpc.export_cfg, export_mdls: kpc.mdl_export=None):  # context):
    """ build a valid model and export """

    def buildGLcommands_fn(mdl, cfg):
        """ build gl commands """
        start_time = kpc.printStart_fn()  # reset timmer
        prefix = "Calculate GLCommands"
        kpc.printProgress_fn(0, 1, prefix)  # print progress

        def find_uv_islands(face_data, uv_data, num_faces):
            """
            Groups all triangles into isolated UV islands.
            """
            # 1. Map every unique (Vertex, UV) pair to the triangles that share it
            vert_to_tris = {}
            for tri_idx in range(num_faces):
                tbase = tri_idx * 3
                for k in range(3):
                    v = face_data[tbase + k]
                    u = uv_data[tbase + k]

                    key = (v, u)
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

                        # Grab all other triangles that share this exact corner point
                        shared_tris = vert_to_tris.get((v, u), [])

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

        mdxID = 0  # mdx hitbox index number
        ofsetVertID = 0   # multi object offset
        numCommands = 1  # add 1 for final NULL at end
        # loop through selected mesh/s
        for tmp_mesh in mdl.frMeData[0]:
            numFaces = tmp_mesh[kpc.IDX_I_FACE]
            face_data = tmp_mesh[kpc.IDX_IDC_V]
            uv_data = tmp_mesh[kpc.IDX_IDC_UV]

            # pre-sort uv into groups
            uv_islands = find_uv_islands(face_data, uv_data, numFaces)

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
                    uv_layer = tmp_mesh[kpc.IDX_XY_UV]  # uv_cords
                    for i in range(bestLength + 2):
                        cmd.append((
                            0.0 + uv_layer[bestUV[i]][0],  # X uv cords
                            1.0 - uv_layer[bestUV[i]][1],  # Y uv cords
                            bestVerts[i] + ofsetVertID))   # vertex number
                        numCommands += 3

                    mdl.glCmdList.append((
                        numType,  # type/count (neg=fan pos=strip)
                        mdxID,    # object number
                        cmd))     # S, T, vIdx...

            #  multi part object offset
            ofsetVertID += len(tmp_mesh[kpc.IDX_XYZ_V])
            if cfg.ui_opt_use_hitbox:
                mdxID += 1

        kpc.printDone_fn(start_time, prefix)  # Done.
        mdl.numGLCmds = numCommands
    # end buildGLcommands_fn

    # TODO
    def getSkins_fn(mdl: kpc.mdl_export, cfg: kpc.export_cfg):
        """TODO change this
        SKIN_MAT_NAME = get materal names, then check for valid images for size
        SKIN_TEX_NAME = get texture names, then check for valid image for size
        SKIN_TEX_PATH = use texture image path and size.
        TODO: UV image?
        """
        # def check_skip_material(mat):
        #     """Simple helper to check whether we actually support exporting that material or not"""
        #     return mat.type not in {"SURFACE"} or mat.use_nodes

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

        for obj in obj_sel:
            materials = obj.data.materials[:]
            # material_names = [m.name if m else None for m in materials]
            for mat in materials:
                if not mat:
                    continue
                texname = mat.name
                if method == "SKIN_MAT_NAME":
                    appendSkins(skins, texname)
                    #get skin size below...

                # use nodes.
                if mat.use_nodes:
                    # search node images for dimensions/name
                    for n in mat.node_tree.nodes:
                        if n and n.type == "TEX_IMAGE" and n.image:
                            image = n.image
                            width, height = updateWH(image.size, width, height)  # set image size
                            # set skin
                            if method == "SKIN_TEX_NAME":
                                appendSkins(skins, image.name)
                            elif method == "SKIN_TEX_PATH":
                                appendSkins(skins, stripLeadingPath(image.filepath))
                            # elif method == "SKIN_MAT_NAME":
                # B2.7 use "texture"
                elif hasattr(mat, "texture_slots"):
                    # search texture slots for dimensions/name
                    for mtex in mat.texture_slots:
                        if mtex and mtex.texture.type == "IMAGE" and mtex.texture.image:
                            image = mtex.texture.image
                            if mtex.use_map_color_diffuse:
                                width, height = updateWH(image.size, width, height)  # set image size
                                # set skin
                                if method == "SKIN_TEX_NAME":
                                    appendSkins(skins, image.name)
                                elif method == "SKIN_TEX_PATH":
                                    appendSkins(skins, stripLeadingPath(image.filepath))
                                # elif method == "SKIN_MAT_NAME":
                # TODO no nodes? use uv name?
                # use uv name/texture?

        kpc.printDone_fn(start_time, prefix)  # Done.

        mdl.skin_print = "  Skin  W: {}  H: {}  Count: {}\n".format(width, height, len(skins))
        for idx, skin in enumerate(skins):
            mdl.skin_print += "  Skin{}:  \'{}\' \n".format(idx + 1, skin[0:kpc.MD2_MAX_SKINNAME - 1])
        if height > 480 or width > 480:
            print("WARNING: found texture larger than kingpin max 480px")

        # set min/max (kp crashes with more then 480, but is not use by opengl render)
        width = kpc.forceMinMaxRange(width, 16, 480)
        height = kpc.forceMinMaxRange(height, 16, 480)

        mdl.skinWidth = width
        mdl.skinHeight = height
        mdl.skins = skins
        mdl.numSkins = len(skins)
    # end getSkins_fn

    def buildFrameNames_fn(cfg: kpc.export_cfg, numFrames):
        """
        sort the markers. The marker with the frame number closest to 0 will be the first marker in the list.
        The marker with the biggest frame number will be the last marker in the list"""
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
            if mdl.isPlayer:
                meshes = mdl.frMeData_BBox[frame]
            else:
                meshes = mdl.frMeData[frame]
            for tmp_mesh in meshes:
                for vert in tmp_mesh[kpc.IDX_XYZ_V]:
                    for i in range(3):
                        if vert[i] < bbox_min[i]:
                            bbox_min[i] = vert[i]
                        if vert[i] > bbox_max[i]:
                            bbox_max[i] = vert[i]

            # add new bbox for each frame
            mdl.bbox_min.append(bbox_min)
            mdl.bbox_max.append(bbox_max)
        kpc.printDone_fn(start_time, prefix)  # Done.
    # end calcSharedBBox_fn

    def calculateHitBox_fn(mdl, cfg: kpc.export_cfg, numFrames):
        """ mdx hitbox """
        start_time = kpc.printStart_fn()  # reset timmer
        prefix = "Calculate mdx hitbox"

        # duplicate scale
        if not mdl.isPlayer:
            for frame in range(numFrames):
                hitboxTmp = []
                hitboxMin = mdl.bbox_min[frame]
                hitboxMax = mdl.bbox_max[frame]
                hitboxTmp.append([hitboxMin[0], hitboxMin[1], hitboxMin[2],
                                    hitboxMax[0], hitboxMax[1], hitboxMax[2]])
                mdl.hitbox.append(hitboxTmp)
        elif cfg.ui_opt_use_hitbox:
            # each object has seperate hitbox
            for frame in range(numFrames):
                hitboxTmp = []
                for tmp_mesh in mdl.frMeData[frame]:
                    verts = np.array(tmp_mesh[kpc.IDX_XYZ_V])
                    hitboxMin =np.min(verts, axis=0)
                    hitboxMax = np.max(verts, axis=0)
                    # add each object
                    hitboxTmp.append([hitboxMin[0], hitboxMin[1], hitboxMin[2],
                                      hitboxMax[0], hitboxMax[1], hitboxMax[2]])
                # add to frame
                mdl.hitbox.append(hitboxTmp)
        else:
            # merge into 1 hit box
            for frame in range(numFrames):
                all_verts = []
                hitboxTmp = []
                for tmp_mesh in mdl.frMeData[frame]:
                    all_verts = all_verts + tmp_mesh[kpc.IDX_XYZ_V]
                verts = np.array(all_verts)
                hitboxMin = np.min(verts, axis=0)
                hitboxMax = np.max(verts, axis=0)
                #add combined
                hitboxTmp.append([hitboxMin[0], hitboxMin[1], hitboxMin[2],
                                  hitboxMax[0], hitboxMax[1], hitboxMax[2]])
                # add to frame
                mdl.hitbox.append(hitboxTmp)

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
                _vn_ = np.array(tmp_mesh[kpc.IDX_XYZ_VN])
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
            triCount += tmp_mesh[kpc.IDX_I_FACE]

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
            vertCount += tmp_mesh[kpc.IDX_I_VERT]

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
            uvCount += tmp_mesh[kpc.IDX_I_UV]
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
        numFrames =  1 + cfg.ui_opt_fr_end - cfg.ui_opt_fr_start

    setupInternalArrays_fn(export_mdls, cfg, numFrames)  # generate mesh/objects
    frameNames = buildFrameNames_fn(cfg, numFrames)  # setup frame names

    # 1 if not self.ui_opt_animated else (1 + self.ui_opt_fr_end - self.ui_opt_fr_start)
    if numFrames > kpc.MD2_MAX_FRAMES:
        numFrames = kpc.MD2_MAX_FRAMES
        # raise RuntimeError( # TODO dont error
        #     "There are too many frames (%i), at most %i are supported in md2/mdx"
        #     % (numFrames, kpc.MD2_MAX_FRAMES))

    MD2_VN = np.array(kpc.MD2_VN)

    for mdl in export_mdls:
        if not mdl.valid:
            continue

        print("Calculating... %s%s" % (mdl.save_name, cfg.f_ext))

        mdl.numFrames = numFrames
        mdl.frameNames = frameNames
        getSkins_fn(mdl, cfg)  # get texture names
        calcSharedBBox_fn(mdl, numFrames)       # get min/max dimensions
        calculateVNornIndex_fn(mdl, numFrames, MD2_VN)  # TODO speed boost
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
            for tmp_mesh in mdl.frMeData[0]:
                # tmp_mesh[kpc.IDX_I_UV]
                for uv in tmp_mesh[kpc.IDX_XY_UV]:
                    data = struct.pack(
                        "<2h",
                        int(uv[0] * mdl.skinWidth),
                        int((1 - uv[1]) * mdl.skinHeight))  # TODO check invalid 0-1 uv space
                    file.write(data)  # uv

        # #################################
        # ### write triangle index data ###
        ofsetVertID = 0
        for tmp_mesh in mdl.frMeData[0]:
            face = tmp_mesh[kpc.IDX_IDC_V]
            uv = tmp_mesh[kpc.IDX_IDC_UV]
            for idx in range(tmp_mesh[kpc.IDX_I_FACE]):
                # 0,2,1 for good cw/ccw
                data = struct.pack(
                    "<3H",  # ### write vert indices ###
                    face[idx * 3 + 0] + ofsetVertID,
                    face[idx * 3 + 2] + ofsetVertID,
                    face[idx * 3 + 1] + ofsetVertID)
                file.write(data)  # vert uv index data

                data = struct.pack(
                    "<3H",  # ### write tex cord indices ###
                    uv[idx * 3 + 0] + ofsetVertID,  # (uv idc)
                    uv[idx * 3 + 2] + ofsetVertID,  # (uv idc)
                    uv[idx * 3 + 1] + ofsetVertID)  # (uv idc)
                file.write(data)  # uv index

            ofsetVertID += len(tmp_mesh[kpc.IDX_IDC_V])
            # self.vertCounter.append(len(tmp_mesh[kpc.IDX_XYZ_V]))

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
                data = struct.pack(
                    "<iL",
                    glCmd[0],  # TrisTypeNum
                    glCmd[1])  # SubObjectID
            else:
                data = struct.pack(
                    "<i",
                    glCmd[0])  # TrisTypeNum
            file.write(data)

            for cmd in glCmd[2]:
                data = struct.pack(
                    "<ffI",
                    cmd[0],  # texture X
                    cmd[1],  # texture Y
                    cmd[2])  # vertex index
                file.write(data)
        # NULL GLCommand
        data = struct.pack("<I", 0)
        file.write(data)

        ###################
        # ### mdx stuff ###
        if cfg.isMdx:
            # ofsVertexInfo #mdx
            for mdxObj, tmp_mesh in enumerate(mdl.frMeData[0]):
                for _ in range(tmp_mesh[kpc.IDX_I_VERT]):
                    if cfg.ui_opt_use_hitbox:
                        bits = 1 << mdxObj
                    else:
                        bits = 1
                    data = struct.pack("<i", bits)  # fill as object #1 TODO
                    file.write(data)  # vert index

            # ofsSfxDefines #mdx
            # ofsSfxEntries #mdx
            # ofsBBoxFrames #mdx
            for mdxObj in range(mdl.hdr.numSubObjects):
                for i in range(mdl.hdr.numFrames):
                    data = struct.pack(
                        "<6f",
                        mdl.hitbox[i][mdxObj][0],
                        mdl.hitbox[i][mdxObj][1],
                        mdl.hitbox[i][mdxObj][2],
                        mdl.hitbox[i][mdxObj][3],
                        mdl.hitbox[i][mdxObj][4],
                        mdl.hitbox[i][mdxObj][5])
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

    export_mdls = []
    # gather all needed objects. make unique models for multi export
    if cfg.ui_opt_is_player:
        export_mdls.append(kpc.mdl_export(obj_player, True, "head"))
        export_mdls.append(kpc.mdl_export(obj_player, True, "body"))
        export_mdls.append(kpc.mdl_export(obj_player, True, "legs"))
        if cfg.ui_opt_exp_weps:
            for o in obj_vis:
                if o not in obj_player: # weapons etc..
                    export_mdls.append(kpc.mdl_export(
                        [o], False, o.name.split('.')[0]))
    else:
        export_mdls.append(kpc.mdl_export(
            obj_sel, False, cfg.f_name.split('.')[0]))

    ret_error = False
    try:
        setup_data_fn(cfg, export_mdls)  # context)
        print("Writing...")

        for mdl in export_mdls:
            if mdl.valid:
                name = "%s/%s%s" % (cfg.f_path, mdl.save_name, cfg.f_ext) # filepath
                write_fn(name, mdl, cfg) # todo fix export names

        # total time
        kpc.printDone_fn(startTime, "Total time")  # Done.

    except IOError:
        print("IO Error")
        ret_error = True
    except Exception as e:
        print("Caught error exporting model")
        print(e)
        ret_error = True
        # traceback.print_exc()
        # raise RuntimeError("Only mesh objects can be exported")

    return ret_error
