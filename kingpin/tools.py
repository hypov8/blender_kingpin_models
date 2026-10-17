"""
=====================
kingpin tools Toolbar
=====================

key frames
import/export
Quake3 to Kingpin
md2 grid
retarget animation
md2 smooth mesh
"""


import os
import bpy
from bpy.types import Operator, Panel, Object, PropertyGroup
from bpy.props import BoolProperty, IntProperty, PointerProperty, StringProperty, EnumProperty
from bpy_extras.io_utils import ImportHelper
from mathutils import kdtree  # Matrix, Euler
from math import radians
from . export_kp import draw_export
# from .import_kp import draw_import
from . import common_kp as kpc
import numpy as np
import itertools


# Property Definitions
class KINGPIN_Tools_props(PropertyGroup):
    """UI varables"""

    ########
    # Grid #
    ui_use_solid = BoolProperty(
        name=" Solid mode:",
        description="Skinned or Wireframe",
        default=False
    )
    ui_use_wire = BoolProperty(
        name=" Wireframe:",
        description="view as wireframe",
        default=True
    )
    ui_floor_cube = EnumProperty(
        name="grix axis",
        description="What axis to show grid on",
            items=(
            ('1', "Z", "Display a grid on Z axis"),
            ('2', "XYZ", "Display a grid on all 3 axis"),
        ),
        default='1'
    )
    ui_subdiv = IntProperty(
        name="Subdivide",
        min=2,
        max=256,
        default=256,
        description=(
            "Change grid subdivision.\n" +
            "Default/Exported: 256 (1-bit).\n" +
            "Note: change if imported model does not align, eg player body part."
        ),
    )
    ###########
    # Drivers #
    ui_drv_start = IntProperty(
        name="Start:",
        min=0,
        max=1022,
        default=0,
        description="Set Start frame to copy animation data",
    )
    ui_drv_end = IntProperty(
        name="End:",
        min=1,
        max=1023,
        default=385,
        description="Set End frame to copy animation data",
    )
    ui_drv_bind_fr = IntProperty(
        name="Bind Frame:",
        min=-500,
        max=1023,
        default=-1,
        description=(
            "At what frame to get the vertex position for driving the mesh\n" +
            "Usage: Set a frame that both mesh are aligned. eg T-post"
        ),
    )
    # object/collection selection
    ui_drv_is_collection = BoolProperty(
        name="Use Collection",
        description="Use all objects in collection",
        default=False,
    )

    ui_drv_obj_picker = PointerProperty(
        name="Source",
        type=Object,  # todo ok?bpy.types.Object,
        description=(
            "Pick the object/mesh you want to use to " +
            "drive the selected object\'s"
        ),
        # poll=lambda self,
        # update=update
    )

    ui_group_type = kpc.get_ui_collection(bpy.types)  # bpy.types.Collection
    ui_drv_obj_picker_group = PointerProperty(
        name="Source",
        type=ui_group_type,
        description="Pick the object/mesh you want to use to"
        " drive the selected object\'s",
    )
    #############
    # UI Smooth #
    ui_smooth_start = IntProperty(
        name="Start:",
        min=0,
        max=1022,
        default=0,
        description="Set Start frame to copy animation data",
    )
    ui_smooth_end = IntProperty(
        name="End:",
        min=1,
        max=1023,
        default=385,
        description="Set End frame to copy animation data",
    )
    ui_smooth_loop = BoolProperty(
        name="Looping Anim",
        description=(
            "Animation is looped. Smoothing will be calculated across first and last fame\n" +
            "Note: used for idle, walking etc. Not taunt, jump, death etc"
        ),
        default=True,
    )
    ###############
    # UI UV Merge #
    ui_uvmerge_max = IntProperty(
        name="Max dimension:",
        min=32,
        max=1024,
        default=512,
        description="Set the max image size. Width or height, scaled",
    )
    ui_uvmerge_path = StringProperty(
        name="Save",
        description="Output image file",
        options={"HIDDEN"},
        default="tris.tga",
        maxlen=1024,
        subtype="NONE"
    )


# -=| GUI |=- #1 Import
class KINGPIN_PT_Tool_GUI_IMPORT(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = kpc.set_ui_panel_string()
    bl_category = "Kingpin"
    bl_label = "Import"
    # bl_options = {"DEFAULT_CLOSED"}  # {'HEADER_LAYOUT_EXPAND'}

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.alignment = "CENTER"
        row.operator("kp.import_model_dialog", icon="IMPORT")


# -=| GUI |=- #2 Export
class KINGPIN_PT_Tool_GUI_EXPORT(Panel):  #, AddonPreferences):  # KP_Preferences):
    bl_space_type = "VIEW_3D"
    bl_region_type = kpc.set_ui_panel_string()
    bl_category = "Kingpin"
    bl_label = "Export"
    bl_options = {"DEFAULT_CLOSED"}  # {'HEADER_LAYOUT_EXPAND'}

    def draw(self, context):
        user_prefs = kpc.get_addon_preferences()
        if user_prefs and user_prefs.pref_kp_export_button_use_dialog:
            layout = self.layout
            row = layout.row()
            row.alignment = "CENTER"
            row.operator("kp.export_model_dialog", icon="EXPORT")
        else:
            # common to toolpanel/export-dialog
            draw_export(self, context, True)

            # toolbar paths
            kp_export_ = context.window_manager.kp_export_
            layout = self.layout
            # grouped box
            box3 = layout.box()

            # file extension. buttons
            # row1 = box3.row()
            col = box3.column_flow(columns=1, align=True)
            row = col.row(align=True)
            row.prop(kp_export_, "ui_opt_model_ext", expand=True)

            # file name
            row = col.row(align=True)
            col1 = row.column()
            col1.alignment = "EXPAND"
            col1.prop(kp_export_, "ui_opt_export_name")
            col1.enabled = kp_export_.ui_opt_export_mode == "EXP_MERGED" # not object mode
            col2 = row.column()
            col2.alignment = "RIGHT"
            col2.operator( "kp.export_button_file", translate=False, icon="IMPORT")

            # folder string
            row = col.row(align=True)
            col1 = row.column()
            col1.alignment = "EXPAND"
            col1.enabled = False  # input box (no edit)
            col1.prop(kp_export_, "ui_opt_export_path")
            # folder button
            col2 = row.column()
            col2.alignment = "RIGHT"
            col2.operator(
                "kp.export_button_folder", translate=False, icon="FILE_FOLDER", text=""
            )

            # export button
            row = layout.row()
            row.alignment = "CENTER"
            row.operator("kp.export_button_model", icon="EXPORT")


# -=| GUI |=- #3 Grid
class KINGPIN_PT_Tool_GUI_GRID(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = kpc.set_ui_panel_string()
    bl_category = "Kingpin"
    bl_label = "MD2 Grid"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        kp_tool_ = context.window_manager.kp_tool_

        layout = self.layout
        box = layout.box()
        # row = box1.column_flow(columns=1, align=True)
        box.prop(kp_tool_, "ui_use_solid")

        row = box.row()
        row.prop(kp_tool_, "ui_floor_cube", expand=True)
        box.prop(kp_tool_, "ui_subdiv")
        # button
        row = layout.row()
        row.alignment = "CENTER"
        row.operator("kp.ui_btn_grid", icon="MOD_LATTICE") #GRID, MESH_GRID, MOD_LATTICE


# -=| GUI |=- #5 Mesh deform/retarget
class KINGPIN_PT_Tool_GUI_RETARGET(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = kpc.set_ui_panel_string()
    bl_category = "Kingpin"
    bl_label = "RETARGET ANIM"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        kp_tool = context.window_manager.kp_tool_
        layout = self.layout

        box = layout.box()
        row = box.column_flow(columns=2, align=True)
        row.prop(kp_tool, "ui_drv_start")
        row.prop(kp_tool, "ui_drv_end")

        row = box.column_flow(columns=1, align=True)
        row.prop(kp_tool, "ui_drv_bind_fr")
        row.prop(kp_tool, "ui_drv_is_collection")
        if kp_tool.ui_drv_is_collection is True:
            row.prop(kp_tool, "ui_drv_obj_picker_group")
        else:
            row.prop(kp_tool, "ui_drv_obj_picker")
        # buttons
        row = layout.row()
        row.operator("kp.ui_btn_driver", icon="DRIVER")
        row = layout.row()
        row.alignment = "CENTER"
        row.operator("kp.ui_btn_driver_clear", icon="X")


# -=| GUI |=- #4 Smooth md2 compresion
class KINGPIN_PT_Tool_GUI_SMOOTH(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = kpc.set_ui_panel_string()
    bl_category = "Kingpin"
    bl_label = "MD2 Smooth"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        kp_tool = context.window_manager.kp_tool_
        layout = self.layout
        box = layout.box()
        row = box.column_flow(columns=2, align=True)
        row.prop(kp_tool, "ui_smooth_start")
        row.prop(kp_tool, "ui_smooth_end")
        # option
        row = box.column()
        row.prop(kp_tool, "ui_smooth_loop")
        # button
        row = layout.row()
        row.alignment = "CENTER"
        row.operator("kp.ui_btn_smooth",icon="SMOOTHCURVE") # NORMALIZE_FCURVES


# -=| GUI |=- #6 UV Merger
class KINGPIN_PT_Tool_GUI_UV_MERGE(Panel):
    """ merge multiple materials into 1 image, fix uv"""
    bl_space_type = "VIEW_3D"
    bl_region_type = kpc.set_ui_panel_string()
    bl_category = "Kingpin"
    bl_label = "MD2 UV Merge"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        kp_tool = context.window_manager.kp_tool_
        layout = self.layout
        box = layout.box()
        box.label(text="Texture Atlas File")

        # file name
        row = box.row(align=True)
        col1 = row.column()
        col1.alignment = "EXPAND"
        col1.enabled = False  # input box (no edit)
        col1.prop(kp_tool, "ui_uvmerge_path")
        # file button
        col2 = row.column()
        col2.alignment = "RIGHT"
        col2.operator("kp.uvmerge_file_picker", translate=False, icon="FILE_FOLDER", text="")

        # button
        row = layout.row()
        row.alignment = "CENTER"
        row.operator("kp.ui_btn_uvmerge", icon="TEXTURE")


# button add vertex keyframes animation
class KINGPIN_UI_BUTTON_DRIVER(Operator):
    """ Drivers """
    bl_idname = "kp.ui_btn_driver"
    bl_label = "Animate Mesh"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = (
        "Vertex animate a static mesh based on the source object\n"
        "Set \'Start:\' and \'End:\' time range.\n"
        "Set \'Bind Frame\' to a frame with a simular pose.\n"
        "Set \'Source:\' to the object that has the animations you want.\n"
        "Press Animate Mesh."
    )

    # @classmethod
    # def poll(self, context):
    #     return (context.selected_objects and context.selected_objects[0].type in {'MESH'})
    #     # and not context.selected_objects[0].data.animation_data)

    def execute(self, context):
        """add driver
        : data.vertices[0].co[0] (sum values)"""

        def insert_key(data, key, group=None):
            """insert key to vertex"""
            try:
                if group is not None:
                    data.keyframe_insert(key, group=group)
                else:
                    data.keyframe_insert(key)
            except print("ERROR: insert_key"):
                pass

        def get_KdTree_for_vArray(vert_array):
            """https://blender.stackexchange.com/a/274223"""
            kd = kdtree.KDTree(len(vert_array))
            for iIdx, v in enumerate(vert_array):
                kd.insert(v, iIdx)  # kd.insert(v.co, i)
            kd.balance()
            return kd
        # END get_KdTree_for_vArray()

        src_Objs = []
        edit_mode, act_obj, sel_objs = kpc.set_mode_get_obj(context)

        key_prop = context.window_manager.kp_tool_
        if key_prop.ui_drv_is_collection:
            if key_prop.ui_drv_obj_picker_group is not None:
                src_Objs = key_prop.ui_drv_obj_picker_group.objects
        else:
            src_Objs = [key_prop.ui_drv_obj_picker]
        src_Objs = kpc.get_mesh_objects(src_Objs)

        # frame  data
        start_fr = key_prop.ui_drv_start
        end_fr = key_prop.ui_drv_end
        bind_fr = key_prop.ui_drv_bind_fr
        cur_frame = bpy.context.scene.frame_current
        total_frames = end_fr + 1 - start_fr
        bpy.context.scene.frame_set(bind_fr)

        # print status
        print("===================\n" +
              "Retarget Animation.\n" +
              "===================")
        print("Frames: %i" % (total_frames))
        start_time = kpc.printStart_fn()
        prefix = "Retargeting"
        kpc.printProgress_fn(0, total_frames, prefix)

        # check valid selections
        if not kpc.is_selected_mesh(self, sel_objs) or not kpc.is_selected_mesh(self, src_Objs):
            print("No valid mesh selected")
            self.report({"WARNING"}, "Select a valid mesh")
            return {"FINISHED"}

        depsgraph = kpc.getDepsgraph()

        # source vert positions. for bind matching
        ob_bind_pos = []
        for obj in src_Objs:
            ob_bind_pos.extend(kpc.getMeshWorldCords_fn(obj, depsgraph))
        kdTree_src = get_KdTree_for_vArray(ob_bind_pos) #flat positions

        # dest mesh T-Pose
        # get world vertex pos, so we can bind to our target
        ob_bind_pos = []
        for obj in sel_objs:
            ob_bind_pos.append(kpc.getMeshWorldCords_fn(obj, depsgraph, False))

        ###############################
        # get vertex bind array indices
        def findBestVertMatch(objData_dst, kdTree_src):
            ret = []  # * len(objData_dst)
            for verts_dst in objData_dst:
                v_array = []
                for vert in verts_dst:
                    # bestIdx = 0
                    co_find = (vert[0], vert[1], vert[2])
                    _, bestIdx, _ = kdTree_src.find(co_find) #co, bestIdx, dist
                    v_array.append(bestIdx)  # TODO add src mesh index..
                ret.append(v_array)
            return ret

        dst_ob_bind_idc = findBestVertMatch(ob_bind_pos, kdTree_src)

        ################
        # loop through each frame, get animation data from source
        for fr in range(end_fr + 1 - start_fr):
            # set current frame
            fr_cur = fr + start_fr
            bpy.context.scene.frame_set(fr_cur)
            # print progress
            if total_frames < 50 or (fr % 20) == 0:
                kpc.printProgress_fn(fr_cur, total_frames, prefix)

            # get current src positions
            depsgraph = kpc.getDepsgraph()
            src_ob_v_array = []
            for obj in src_Objs: #source
                v = kpc.getMeshWorldCords_fn(obj, depsgraph)
                src_ob_v_array.extend(v) # combine/flat cords

            # animate the destination mesh.
            for oIdx, obj in enumerate(sel_objs): #destination
                num_vert = len(obj.data.vertices)
                bind_idc = dst_ob_bind_idc[oIdx] #best match index
                new_dest = []
                # for i in range(num_vert):
                #     new_dest.append(src_ob_v_array[bind_idc[i]])

                new_dest = [src_ob_v_array[bind_idc[i]] for i in range(num_vert)]
                new_dest = kpc.setMeshLocalCords_fn(obj, new_dest)

                # set ketframe
                for vIdx, vert in enumerate(obj.data.vertices): #not in sync
                    # add local transforms
                    vert.co = new_dest[vIdx]
                    # add vertex keyframe
                    insert_key(vert, "co", group="Vertex %s" % vIdx)

        for obj in sel_objs:
            # obj.matrix_basis = matrix_array[i]
            # obj.data.transform(matrix_array[i].inverted())
            # calc_normals_split was removed in Blender 4.1; normals are
            # now computed automatically when mesh.update() runs.
            if hasattr(obj.data, "calc_normals_split"):  #B41+
                obj.data.calc_normals_split()
            obj.data.update()

        # set frame
        bpy.context.scene.frame_set(cur_frame)
        # return to edit mode if neded
        if act_obj:
            kpc.set_objects_active(bpy.context, act_obj)
            bpy.ops.object.mode_set(mode=edit_mode)

        kpc.refresh_ui_keyframes()

        kpc.printDone_fn(start_time, prefix)
        self.report({"INFO"}, "Retarget Animation: Done")
        print("===================")
        return {"FINISHED"}


# button grid
class KINGPIN_UI_BUTTON_GRID(Operator):
    bl_idname = "kp.ui_btn_grid"
    bl_label = "Show 1-bit Grid"
    bl_options = {'REGISTER'}
    bl_description = (
        "Adds a bounding box grid set to 256 units.\n"
        "Use this tool so you can snap vertex to suit md2/x compresion grid\n"
        "Repeat clicking 'Add Grid' will delete/update the existing grid dimensions"
    )

    # @classmethod
    # def poll(self, context):
    #     return (context.selected_objects and context.selected_objects[0].type in {'MESH'})

    def execute(self, context):
        grid_names = ["kp_grid_x", "kp_grid_y", "kp_grid_z"]
        objMin = [99999.0] * 3
        objMax = [-99999.0] * 3
        key_prop = context.window_manager.kp_tool_
        grid_div = key_prop.ui_subdiv

        # get selected array
        edit_mode, act_obj, sel_objs = kpc.set_mode_get_obj(context)

        # deselect any objects
        for obj in kpc.get_objects_selected(context):
            kpc.set_select_state(obj, False)
        if act_obj:
            kpc.set_select_state(act_obj, False)

        # remove grid from selection
        sel_objs = [obj for obj in sel_objs if not obj.name[:9] in grid_names]

        ############################
        # find existing grid. delete
        obj_all = kpc.get_objects_all(bpy.context)
        for obj in obj_all:
            ob_name = obj.name[:9]
            if ob_name in grid_names:
                bpy.data.objects.remove(obj)  # todo 2.79?

        # check array length
        if len(sel_objs) < 1:  # not context.selected_objects:
            # TODO use all scene objects?
            print("Nothing selected")
            self.report({"INFO"}, "Nothing selected")
            return {"FINISHED"}

        ###############################
        # get bounding box in selection
        vX = []
        vY = []
        vZ = []
        # todo cleanep, numpy
        ret_objs = kpc.getMeshArrays_fn(sel_objs)
        for obj in ret_objs:
            for v in obj.md_xyz_vert:
                vX.append(v[0])
                vY.append(v[1])
                vZ.append(v[2])
        objMin[0], objMin[1], objMin[2] = min(vX), min(vY), min(vZ)
        objMax[0], objMax[1], objMax[2] = max(vX), max(vY), max(vZ)

        ################################
        # build bounds/position/rotation
        width = [
            (objMax[0] - objMin[0]),
            (objMax[1] - objMin[1]),
            (objMax[2] - objMin[2]),
        ]
        widthXYZ = [
            [width[2], width[1], 0],
            [width[0], width[2], 0],
            [width[0], width[1], 0],
        ]
        midXYZ = [
            [objMin[0], (width[1] / 2 + objMin[1]), (width[2] / 2 + objMin[2])],
            [(width[0] / 2 + objMin[0]), objMin[1], (width[2] / 2 + objMin[2])],
            [(width[0] / 2 + objMin[0]), (width[1] / 2 + objMin[1]), objMin[2]],
        ]

        rot = radians(90)
        rotXYZ = [
            [0, rot, 0],  # x
            [rot, 0, 0],  # y
            [0, 0, 0],  # z
        ]

        ####################
        # generate new grid/s
        # subdivision in B3.0 uses face count
        grid_div = grid_div if kpc.check_version(3, 0, 0) < 0 else (grid_div - 1)
        rng = 1 if key_prop.ui_floor_cube == "1" else 3  # skip X+Y grid
        for i in range(rng):
            bpy.ops.mesh.primitive_grid_add(
                x_subdivisions=grid_div, y_subdivisions=grid_div
            )  # size=width[i]) B2.8
            obj = kpc.get_objects_active(context)
            if not obj or obj.name[0:4] != "Grid":
                raise ValueError("Could not select grid")
            idx = (i + 2) % 3
            obj.name = grid_names[idx]  # z first
            obj.dimensions = widthXYZ[idx]
            obj.location = midXYZ[idx]
            obj.rotation_mode = "XYZ"
            obj.rotation_euler = rotXYZ[idx]
            obj.show_all_edges = True
            obj.show_wire = key_prop.ui_use_wire
            drawType = "SOLID" if key_prop.ui_use_solid else "WIRE"
            kpc.set_obj_draw_type(obj, drawType)

            kpc.set_select_state(obj, False)

        #######################
        # select inital objects
        for obj in sel_objs:
            kpc.set_select_state(obj, True)

        # return to edit mode
        for obj in sel_objs:  # select inital objects
            kpc.set_select_state(obj, True)
        if act_obj:  # TODO fix invalid state
            kpc.set_objects_active(bpy.context, act_obj)
            bpy.ops.object.mode_set(mode=edit_mode)

        self.report({"INFO"}, "Grid Created")
        return {"FINISHED"}

# button grid
class KINGPIN_UI_BUTTON_UVMERGE(Operator):
    bl_idname = "kp.ui_btn_uvmerge"
    bl_label = "Merge UV/Image" #Merge into to 1 UV" # texture atlasing
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = (
        "Merge all materials assigned to the mesh and moves UV to match texture.\n"
        "A new image will be created and saved externaly.\n"
        "CAUTION: make sure you have a backup"
    )

    def execute(self, context):
        """ get all materials and merge into one UV """

        def get_next_multiple_of_16(value):
            if value <= 16:
                return 16
            return ((value + 15) // 16) * 16
        # end get_next_multiple_of_16

        obj = kpc.get_objects_active(context)
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh object first.")
            return {'CANCELLED'}

        kp_tool = context.window_manager.kp_tool_
        target_path = kp_tool.ui_uvmerge_path
        atlas_res = int(kp_tool.ui_uvmerge_max) # e.g. 1024 or 2048

        if not target_path:
            self.report({'ERROR'}, "Please select a destination TGA path.")
            return {'CANCELLED'}

        # 1. GATHER RAW IMAGES
        raw_images = []
        for index, slot in enumerate(obj.material_slots):
            mat = slot.material
            if mat and mat.node_tree:
                for node in mat.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image:
                        img = node.image
                        # Avoid adding identical image data blocks twice
                        if img not in [item['img'] for item in raw_images]:
                            raw_images.append({
                                'idx': index,
                                'img': img,
                                'w': img.size[0],
                                'h': img.size[1]
                            })

        if len(raw_images) < 2:
            self.report({'ERROR'}, "No textures found to merge.")
            return {'CANCELLED'}

        # 2. DEFINE OPTIMIZATION SORT STRATEGIES
        sort_strategies = [
            lambda item: item['h'],                # Height
            lambda item: item['w'],                # Width
            lambda item: item['w'] * item['h'],    # Area
            lambda item: max(item['w'], item['h'])  # Max side
        ]

        best_score = float('inf')
        best_image_positions = {}
        final_w = atlas_res
        final_h = atlas_res

        # 3. PERMUTATION LOOP (Find best packing arrangement)
        for strategy in sort_strategies:
            sorted_items = sorted(raw_images, key=strategy, reverse=True)
            num_images = len(sorted_items)

            # This generates a list of all binary combinations: e.g., [(False, False), (False, True), (True, False)...]
            # It creates a true independent pass for every permutation of rotated/unrotated states
            all_rotation_combinations = list(itertools.product([False, True], repeat=num_images))

            for rotation_mask in all_rotation_combinations:
                test_packer = kpc.TexturePacker(atlas_res, atlas_res)
                test_positions = {}
                max_x, max_y = 0, 0
                failed = False

                # Loop through the sorted items using an enumerator index
                for idx, item in enumerate(sorted_items):
                    w, h = item['w'], item['h']
                    is_rotated = False

                    # Read the independent true/false flag out of the current combination mask
                    if rotation_mask[idx] is True:
                        w, h = h, w  # Rotate this specific image regardless of its original shape
                        is_rotated = True

                    packed_coord = test_packer.pack(w, h)
                    if packed_coord is None:
                        failed = True
                        break

                    px, py = packed_coord
                    test_positions[item['idx']] = {
                        'x': px, 'y': py, 'w': w, 'h': h, 'rotated': is_rotated, 'img': item['img']
                    }

                    if px + w > max_x:
                        max_x = px + w
                    if py + h > max_y:
                        max_y = py + h

                if failed:
                    continue

                test_w = get_next_multiple_of_16(max_x)
                test_h = get_next_multiple_of_16(max_y)
                test_area = test_w * test_h

                if test_area < best_score:
                    best_score = test_area
                    final_w = test_w
                    final_h = test_h
                    best_image_positions = test_positions.copy()


        # 4. BLIT PIXELS INTO THE TIGHT ATLAS
        master_pixels = np.zeros((atlas_res, atlas_res, 4), dtype=np.float32)

        for mat_idx, pos in best_image_positions.items():
            img = pos['img']
            src_w, src_h = img.size
            px, py = pos['x'], pos['y']

            # Pull raw pixel source array safely via NumPy
            src_pixels = np.array(img.pixels, dtype=np.float32).reshape(src_h, src_w, 4)

            # Apply 90-degree counter-clockwise rotation matrix if optimization picked it
            if pos['rotated']:
                src_pixels = np.rot90(src_pixels, k=1)
                # Match the flipped dimensions for array insertion
                src_w, src_h = src_h, src_w

            master_pixels[py : py + src_h, px : px + src_w] = src_pixels

        # Crop the canvas buffer down to our winning 16px multiple bounding boundaries
        cropped_pixels = master_pixels[0:final_h, 0:final_w]

        # Create the unified texture reference inside Blender project data
        master_img = bpy.data.images.new("master_atlas", width=final_w, height=final_h, alpha=True)
        master_img.pixels = cropped_pixels.ravel()
        master_img.update()

        # Save physical TGA file asset
        master_img.filepath_raw = target_path
        master_img.file_format = 'TARGA'
        master_img.save()

        # 5. REMAP THE GEOMETRY MESH UVs
        current_mode = obj.mode
        if current_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        mesh = obj.data
        uv_layer = mesh.uv_layers.active
        if not uv_layer:
            uv_layer = mesh.uv_layers.new(name="Merged_UV")

        for poly in mesh.polygons:
            mat_idx = poly.material_index

            if mat_idx in best_image_positions:
                pos = best_image_positions[mat_idx]
                offset_x, offset_y = pos['x'], pos['y']
                orig_w, orig_h = pos['img'].size

                for loop_idx in poly.loop_indices:
                    uv_loop = uv_layer.data[loop_idx]
                    current_uv = uv_loop.uv

                    if pos['rotated']:
                        # FIX: Swap U and V, and invert the V coordinate to resolve the vertical flip
                        pixel_x = current_uv.y * orig_h
                        pixel_y = (1.0 - current_uv.x) * orig_w  # Inverts top/bottom safely

                        new_x = (pixel_x + offset_x) / final_w
                        new_y = (pixel_y + offset_y) / final_h
                    else:
                        # Standard matching layout path for non-rotated elements
                        new_x = ((current_uv.x * orig_w) + offset_x) / final_w
                        new_y = ((current_uv.y * orig_h) + offset_y) / final_h

                    uv_loop.uv = (new_x, new_y)

        # 6. ASSIGN MASTER MATERIAL
        obj.data.materials.clear()
        master_mat = bpy.data.materials.new(name="Master_Atlas_Material")
        obj.data.materials.append(master_mat)

        master_mat.use_nodes = True
        nodes = master_mat.node_tree.nodes
        links = master_mat.node_tree.links
        nodes.clear()

        node_output = nodes.new(type='ShaderNodeOutputMaterial')
        node_principled = nodes.new(type='ShaderNodeBsdfPrincipled')
        node_texture = nodes.new(type='ShaderNodeTexImage')

        node_texture.image = master_img
        links.new(node_texture.outputs['Color'], node_principled.inputs['Base Color'])
        links.new(node_principled.outputs['BSDF'], node_output.inputs['Surface'])

        if current_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode=current_mode)

        self.report({'INFO'}, "Optimized layout generated at %ix%i!" % (final_w, final_h))
        return {"FINISHED"}


# button uvmerge file
class KINGPIN_UI_BUTTON_UVMERGE_file_picker(Operator,
         ImportHelper, kpc.KINGPIN_FileSelect_file_Params_tga):
    """ export combined uv file name/path """
    bl_idname = "kp.uvmerge_file_picker" #export_button_folder
    bl_label = "Select TGA File"  # icon
    # bl_options = {'REGISTER'}
    # bl_description = "Copy selected objects @name to @file input box"
    # check_extension = True  # 2.8 allow typing md2/mdx
    filename_ext = ".tga"
    use_filter_folder = True

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def check(self, context):
        """Intercepts the path and forces the .tga extension"""
        print("check")
        if self.filepath:
            root, ext = os.path.splitext(self.filepath)
            if ext.lower() != ".tga":
                self.filepath = root + ".tga"
                return True # Updates the text box inside the file browser UI
        return False

    def execute(self, context):
        kp_tool_ = context.window_manager.kp_tool_
        kp_tool_.ui_uvmerge_path = self.filepath
        # self.report({'INFO'}, f"Saved TGA path: {self.filepath}")
        return {"FINISHED"}


# button smooth
class KINGPIN_UI_BUTTON_SMOOTH(Operator):
    bl_idname = "kp.ui_btn_smooth"
    bl_label = "Smooth Vertex"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = (
        "Smooth out the vertex compresion/wobble from importing an md2/x.\n" +
        "Use this tool for HD exports."
    )

    # @classmethod
    # def poll(self, context):
    #     return context.selected_objects and context.selected_objects[0].type in {'MESH'}

    def execute(self, context):
        """ _ """
        # get selected objects
        edit_mode, act_obj, sel_objs = kpc.set_mode_get_obj(context)

        # check valid selections
        if not kpc.is_selected_mesh(self, sel_objs):
            print("No mesh selected.")
            self.report({"WARNING"}, "No mesh selected")
            return {"FINISHED"}

        key_prop = context.window_manager.kp_tool_

        start_fr = key_prop.ui_smooth_start  # frame start
        end_fr = key_prop.ui_smooth_end  # frame end
        total_fr = end_fr - start_fr + 1
        cur_frame = bpy.context.scene.frame_current

        print(
            "============\n" +
            "start smooth\n" +
            "============\nframes: %i" % (total_fr)
        )
        prefix = "Get mesh data"
        start_time = kpc.printStart_fn()  # start timmer
        kpc.printProgress_fn(0, 1, prefix)  # print progress

        # check for md2 data attached to object
        for oIdx, obj in enumerate(sel_objs):
            if kpc.DATA_F_SCALE not in obj.data or kpc.DATA_F_COUNT not in obj.data:
                print("No scale data(try re-import mesh)")
                self.report({"WARNING"}, "No Scale Data")
                return {"FINISHED"}

            # check model data count
            if obj.data[kpc.DATA_F_COUNT] < end_fr:
                end_fr = obj.data[kpc.DATA_F_COUNT]
                total_fr = end_fr - start_fr + 1
                print("WARNING: end frame set to %i (model: %s)" %
                      (end_fr, obj.name))

        ################################
        # get all object/frames
        # [frame] [object] [(x,y,z)]
        fr_ob_v_pos = [
            [[[0] * 3 for v in range(len(o.data.vertices))] for o in sel_objs]
            for f in range(total_fr)
        ]
        # fr_ob_scale = [] # [frame] [object] [vIndex] [(scaleX, scaleY, scaleZ)]
        fr_ob_scale = [[0] * len(sel_objs) for f in range(total_fr)]

        fr_ob_v_byte = [
            [[[0] * 3 for v in range(len(o.data.vertices))] for o in sel_objs]
            for f in range(total_fr)
        ]
        # fr_ob_v_byte = [[0] * len(sel_objs) for f in range(total_fr)]

        # get model imported scale
        for oIdx, obj in enumerate(sel_objs):
            dat_scale = obj.data[kpc.DATA_F_SCALE]
            dat_byte = obj.data[kpc.DATA_V_BYTE]
            dat_f_count = obj.data[kpc.DATA_F_COUNT]
            dat_v_count = obj.data[kpc.DATA_V_COUNT]
            if dat_v_count != len(obj.data.vertices):
                print("ERROR: object %s vertex count changed since import"% (obj.name))
                continue

            # flat to 2d
            for fr in range(total_fr):
                fr_cur = min(start_fr + fr, dat_f_count - 1) # stop overflow.
                # scale data
                vert_idx = fr_cur * 3
                fr_ob_scale[fr][oIdx] = dat_scale[vert_idx:vert_idx + 3]
                # vertex data
                vert_idx = fr_cur * dat_v_count * 3 # TODO numpy
                for v in range(dat_v_count):
                    off = vert_idx + v*3
                    fr_ob_v_byte[fr][oIdx][v] = dat_byte[off:off + 3]

        # store vertex pos data
        for oIdx, obj in enumerate(sel_objs):
            dat_f_count = obj.data[kpc.DATA_F_COUNT]
            dat_v_count = obj.data[kpc.DATA_V_COUNT]
            if dat_v_count != len(obj.data.vertices):
                continue # skip invalid

            anim = obj.data.animation_data
            if anim is None or anim.action is None:
                print("No animation data(import anim as vertex)")
                self.report({"WARNING"}, "No animation data")
                return {"FINISHED"}
            # Resolve fcurves once per action; works on 4.4+ slotted actions.
            anim_fcurves = kpc.fcurves_get(anim.action)  #b44+
            # loop through vertex array
            for i in range(len(obj.data.vertices)):
                v_offs = i * 3
                for j in range(3):
                    # x0, y0, z0, x1, y1, z1
                    fcu = anim_fcurves[i*3+j]  # fcu = anim.action.fcurves[v_offs + j]
                    # loop through frame time
                    for fr in range(total_fr):
                        fr_cur = start_fr + fr
                        if fr_cur >= dat_f_count:
                            fr_cur = dat_f_count - 1  # stop overflow.
                        fr_ob_v_pos[fr][oIdx][i][j] = fcu.keyframe_points[fr_cur].co.y

        # if self.numFrames < 50 or (frame % 20) == 0:
        kpc.printDone_fn(start_time, prefix)

        prefix = "Shifting vertex"
        start_time = kpc.printStart_fn()  # start timmer
        kpc.printProgress_fn(0, 1, prefix)  # print progress

        ################################
        # smooth animations in mesh.
        loop_fr_count = total_fr
        # loop_fr_count -= 1 if key_prop.ui_smooth_loop == False else 0

        ################################
        # fredz generted smooth function
        def SmoothPoints_gaussian2(v_pos, v_scale, isLoop):
            """smooth over 5 vertex pos

            using decompred values, from the 256(1 byte) values
            v_pos is final vert positions in blender
            v_scale. is the size(float) used to scale original byte date. equilivent to 1bit on the compressed vert.
            v_scale*2.5 will capture changes only if withing ~2bits of movemeant
            """

            def gaussian_weight(distance, scale):
                return 2.718281 ** (-0.5 * (distance / scale) ** 2)

            len_array = len(v_pos)
            ret_array = [0] * len_array

            for fr in range(len_array):
                sum_weights = 0
                sum_positions = 0

                for j in range(-2, 3):  # Consider previous 2 and next 2 frames
                    fr2_idx = fr + j
                    if not isLoop and (fr2_idx < 0 or fr2_idx >= len_array):
                        continue
                    fr2_off_idx = fr2_idx % len_array
                    fr2_vPos = v_pos[fr2_off_idx]
                    diff_pos_abs = abs(fr2_vPos - v_pos[fr])

                    diff_sc_abs = abs(v_scale[fr2_off_idx] * 2.5)  # scale

                    weight = gaussian_weight(diff_pos_abs, diff_sc_abs)
                    sum_weights += weight
                    sum_positions += weight * fr2_vPos

                if sum_weights > 0:
                    ret_array[fr] = sum_positions / sum_weights
                else:
                    ret_array[fr] = v_pos[fr]

            return ret_array
        # end SmoothPoints_gaussian2

        # kpc.mod_hd_setup_weight()  # build lookup tables

        looped_anims = key_prop.ui_smooth_loop
        for o_idx, obj in enumerate(sel_objs):
            anim = obj.data.animation_data
            anim_fcurves = kpc.fcurves_get(anim.action) #b44+
            dat_f_count = obj.data[kpc.DATA_F_COUNT]
            for vIdx in range(len(obj.data.vertices)):
                v_offs = vIdx * 3
                for xyz in range(3):
                    vert_pos = []
                    vert_scl = []
                    vert_idx = []
                    for fr in range(loop_fr_count):
                        fr_cur = start_fr + fr
                        if fr_cur >= dat_f_count:
                            print("Error: end frame value larger then model file data")
                            continue
                        vert_pos.append(fr_ob_v_pos[fr][o_idx][vIdx][xyz])
                        vert_idx.append(fr_ob_v_byte[fr][o_idx][vIdx][xyz])
                        vert_scl.append(fr_ob_scale[fr][o_idx][xyz])
                    # todo clean this up

                    # process points
                    # smooth_data = SmoothPoints_gaussian2(vert_pos, vert_scl, looped_anims)
                    # smooth_data = kpc.bilateral_filter_circular(vert_pos, sigma_space=2.0, sigma_range=35.0)
                    # smooth_data = kpc.smooth_gauss_fast(vert_pos, vert_scl, looped_anims)
                    smooth_data = kpc.smooth_better(vert_pos, vert_scl, looped_anims)

                    # if xyz == 2:
                    #     print_z = True
                    # else:
                    #     print_z = False

                    # smooth_data = kpc.fast_threshold_bilateral_init(
                    #     vert_pos, vert_scl, vert_idx, print_z
                    # )

                    # write new vertex cord
                    fcu = anim_fcurves[v_offs + xyz] # fcu = anim.action.fcurves[v_offs + xyz]
                    for fr, dat in enumerate(smooth_data):
                        fcu.keyframe_points[start_fr + fr].co.y = dat  # vert_pos[fr] +
                    fcu.update()

        # update
        for obj in sel_objs:
            # print("update..")
            if hasattr(obj.data, "calc_normals_split"):
                obj.data.calc_normals_split()
            obj.data.update()

        #######################
        # done. select inital objects
        for obj in sel_objs:
            kpc.set_select_state(obj, True)

        bpy.context.scene.frame_set(cur_frame)
        # return to edit mode
        if act_obj:  # TODO fix invalid state
            kpc.set_objects_active(bpy.context, act_obj)
            bpy.ops.object.mode_set(mode=edit_mode)

        kpc.printDone_fn(start_time, prefix)  # Done.

        print("============")
        self.report({"INFO"}, "Smoothing Animation: Done")
        return {"FINISHED"}


classes = (
    KINGPIN_UI_BUTTON_GRID,
    KINGPIN_UI_BUTTON_DRIVER,
    KINGPIN_UI_BUTTON_SMOOTH,
    KINGPIN_UI_BUTTON_UVMERGE,
    KINGPIN_UI_BUTTON_UVMERGE_file_picker,
    KINGPIN_PT_Tool_GUI_IMPORT,
    KINGPIN_PT_Tool_GUI_EXPORT,
    KINGPIN_PT_Tool_GUI_GRID,
    KINGPIN_PT_Tool_GUI_SMOOTH,
    KINGPIN_PT_Tool_GUI_RETARGET,
    KINGPIN_PT_Tool_GUI_UV_MERGE,
)


def register():
    for cls in classes:
        # make_annotations(cls)
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
