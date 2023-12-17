'''
=====================
kingpin tools Toolbar
=====================

key frames
import/export
Quake3 to Kingpin
md2 grid
retarget animation
md2 smooth mesh
'''


import bpy
from bpy.types import (
    Operator,
    Panel,
    PropertyGroup
)
from bpy.props import (
    BoolProperty,
    IntProperty,
    PointerProperty
)
from mathutils import Vector, kdtree  # Matrix, Euler
from . export_kp import draw_export
from . import_kp import draw_import
from . common_kp import (
    check_version,
    set_ui_panel_string,
    get_ui_collection,
    get_objects_all,
    get_objects_selected,
    getMeshArrays_fn,
    set_select_state,
    set_mode_get_obj,
    set_obj_draw_type,
    refresh_ui_keyframes,
    printStart_fn,
    printProgress_fn,
    printDone_fn,
    get_mesh_objects,
    is_selected_mesh,
    get_addon_preferences,
    IDX_XYZ_V,
    DATA_F_SCALE,
    DATA_F_COUNT,
)


# Property Definitions
class KINGPIN_Tools_props(PropertyGroup):
    ''' UI varables '''
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
    ui_floor_cube = BoolProperty(
        name="Z-Grid Only (No X/Y)",
        description=(
            "Generate a grid for floor only\n"
            "Disabled: Adds grid to all 3 axis"),
        default=True,
    )
    ui_subdiv = IntProperty(
        name="Subdivide",
        min=2,
        max=256,
        default=256,
        description=(
            "Change grid subdivision. Default: 256\n" +
            "Kingpin plugin exported models are 256 units\n" +
            "  so make sure its correct or you are using a\n" +
            "  custom bounding box(fix seams)"
        )
    )
    ###########
    # Drivers #
    ui_drv_start = IntProperty(
        name="Start:",
        min=0,
        max=1022,
        default=0,
        description="Set Start frame to copy animation data"
    )
    ui_drv_end = IntProperty(
        name="End:",
        min=1,
        max=1023,
        default=385,
        description="Set End frame to copy animation data"
    )
    ui_drv_bind_fr = IntProperty(
        name="Bind Frame:",
        min=-500,
        max=1023,
        default=-1,
        description=(
            "At what frame to get the vertex position for driving the mesh\n" +
            "Usage: Set a frame that both mesh are aligned. eg T-post.")
    )
    # object/collection selection
    ui_drv_is_collection = BoolProperty(
        name="Use Collection",
        description=(
            "Use all objects in collection"),
        default=False,
    )

    ui_drv_obj_picker = PointerProperty(
        name="Source",
        type=bpy.types.Object, #  todo ok?object,
        description=(
            "Pick the object/mesh you want to use to" +
            "drive the selected object\\s."
        ),
        # poll=lambda self,
        # update=update
    )

    ui_group_type = get_ui_collection(bpy.types)  # bpy.types.Collection
    ui_drv_obj_picker_group = PointerProperty(
        name="Source",
        type=ui_group_type,
        description=(
            "Pick the object/mesh you want to use to" +
            "drive the selected object\\s."
        ),
    )
    #############
    # UI Smooth #
    ui_smooth_start = IntProperty(
        name="Start:",
        min=0,
        max=1022,
        default=0,
        description="Set Start frame to copy animation data"
    )
    ui_smooth_end = IntProperty(
        name="End:",
        min=1,
        max=1023,
        default=385,
        description="Set End frame to copy animation data"
    )
    ui_smooth_loop = BoolProperty(
        name="Looping Anim",
        description=(
            "Enabled: first and last fame will be included in the smooth process\n" +
            "  Use when you want to effect a pose, eg.. idle\n" +
            "Disabled: smooth all frame 'between' the start/end times\n"),
        default=True,
    )


# -=| GUI |=- #1 Import
class VIEW3D_PT_Tool_GUI_IMPORT(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = set_ui_panel_string()
    bl_category = 'Kingpin'
    bl_label = 'Import'
    bl_options = {'DEFAULT_CLOSED'} # {'HEADER_LAYOUT_EXPAND'}

    def draw(self, context):
        user_prefs = get_addon_preferences(context)
        if user_prefs.pref_kp_import_button_use_dialog:
            layout = self.layout
            row = layout.row()
            row.alignment = 'CENTER'
            row.operator("kp.import_model_dialog")
        else:
            draw_import(self, context)
            layout = self.layout
            col = layout.column(align=True)
            row = col.row()
            row.alignment = 'CENTER'
            row.operator("kp.import_model_button")


# -=| GUI |=- #1 Export
class VIEW3D_PT_Tool_GUI_EXPORT(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = set_ui_panel_string()
    bl_category = 'Kingpin'
    bl_label = 'Export'
    bl_options = {'DEFAULT_CLOSED'} # {'HEADER_LAYOUT_EXPAND'}

    def draw(self, context):
        user_prefs = get_addon_preferences(context)
        if user_prefs.pref_kp_export_button_use_dialog:
            layout = self.layout
            row = layout.row()
            row.alignment = 'CENTER'
            row.operator("kp.export_model_dialog")
        else:
            draw_export(self, context)
            #
            kp_export_ = context.window_manager.kp_export_
            layout = self.layout
            box3 = layout.box()
            row = box3.column()
            row.prop(kp_export_, "ui_opt_model_ext")

            # file name
            row = box3.row(align=True)
            col1 = row.column()
            col1.alignment = 'EXPAND'
            col1.prop(kp_export_, "ui_opt_export_name")
            col2 = row.column()
            col2.alignment = 'RIGHT'
            col2.operator("kp.export_button_file",
                translate=False, icon='IMPORT')

            # folder string
            row = box3.row(align=True)
            col1 = row.column()
            col1.alignment = 'EXPAND'
            col1.enabled = False  # input box (no edit)
            col1.prop(kp_export_, "ui_opt_export_path")
            # folder button
            col2 = row.column()
            col2.alignment = 'RIGHT'
            col2.operator("kp.export_button_folder",
                translate=False, icon='FILE_FOLDER', text="")

            # export button
            row = layout.row()
            row.alignment = 'CENTER'
            row.operator("kp.export_button_model")


# -=| GUI |=- #1 Grid
class VIEW3D_PT_Tool_GUI_GRID(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = set_ui_panel_string()
    bl_category = 'Kingpin'
    bl_label = 'MD2 Grid'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        kp_tool_ = context.window_manager.kp_tool_

        layout = self.layout
        box1 = layout.box()
        row = box1.column_flow(columns=1, align=True)
        row.prop(kp_tool_, "ui_use_solid")
        row.prop(kp_tool_, "ui_floor_cube")
        row.prop(kp_tool_, "ui_subdiv")
        #button
        row = layout.row()
        row.alignment = 'CENTER'
        row.operator("kp.ui_btn_grid")


# -=| GUI |=- #2 Mesh deform
class VIEW3D_PT_Tool_GUI_DEFORM(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = set_ui_panel_string()
    bl_category = 'Kingpin'
    bl_label = 'RETARGET ANIM'
    bl_options = {'DEFAULT_CLOSED'}


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
        if kp_tool.ui_drv_is_collection == True:
            row.prop(kp_tool, "ui_drv_obj_picker_group")
        else:
            row.prop(kp_tool, "ui_drv_obj_picker")
        # buttons
        row = layout.row()
        row.operator("kp.ui_btn_driver")
        row = layout.row()
        row.alignment = 'CENTER'
        row.operator("kp.ui_btn_driver_clear")


# -=| GUI |=- #3 Smooth md2 compresion
class VIEW3D_PT_Tool_GUI_SMOOTH(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = set_ui_panel_string()
    bl_category = 'Kingpin'
    bl_label = 'MD2 Smooth'
    bl_options = {'DEFAULT_CLOSED'}

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
        row.alignment = 'CENTER'
        row.operator("kp.ui_btn_smooth")


# button add vertex keyframes animation
class KINGPIN_UI_BUTTON_DRIVER(Operator):
    '''Drivers'''
    bl_idname = "kp.ui_btn_driver"
    bl_label = "Animate Mesh"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = (
        "Animate a mesh using vertex keyframes.\n"
        "Set 'Start:' and 'End:' time range that you want animations.\n"
        "Set 'Bind Frame' to a frame that both models are in close proximity(T-Pose)\n"
        "Set the 'Source:' object(that have the animations you want)\n"
        "Press Animate Mesh.\n"
        "Done: The static mesh should be vertex animated based on 'Source:' object."
    )

    # @classmethod
    # def poll(self, context):
    #     return (context.selected_objects and context.selected_objects[0].type in {'MESH'})
    #     # and not context.selected_objects[0].data.animation_data)

    def execute(self, context):
        '''add driver
        : data.vertices[0].co[0] (sum values) '''

        def insert_key(data, key, group=None):
            ''' insert key to vertex '''
            try:
                if group is not None:
                    data.keyframe_insert(key, group=group)
                else:
                    data.keyframe_insert(key)
            except print("ERROR: insert_key"):
                pass

        def get_KdTree_for_vArray(meshArray):
            '''https://blender.stackexchange.com/a/274223'''
            size = 0
            for m in meshArray:
                size += len(m[IDX_XYZ_V])
            kd = kdtree.KDTree(size)
            iIdx = 0
            for m in meshArray:
                for i, v in enumerate(m[IDX_XYZ_V]):
                    kd.insert(v, iIdx)  # kd.insert(v.co, i)
                    iIdx += 1
            kd.balance()
            return kd
        # END get_KdTree_for_vArray()

        src_Objs = []
        edit_mode, act_obj, sel_objs = set_mode_get_obj(context)

        key_prop = context.window_manager.kp_tool_
        if key_prop.ui_drv_is_collection:
            if key_prop.ui_drv_obj_picker_group is not None:
                src_Objs = key_prop.ui_drv_obj_picker_group.objects
        else:
            src_Objs = [key_prop.ui_drv_obj_picker]
        src_Objs = get_mesh_objects(src_Objs)

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
        start_time = printStart_fn()
        prefix = "Retargeting"
        printProgress_fn(0, total_frames, prefix)

        # check valid selections
        if not is_selected_mesh(self, sel_objs) or not is_selected_mesh(self, src_Objs):
            print("No valid mesh selected")
            self.report({'WARNING'}, "Select a valid mesh")
            return {'FINISHED'}

        # source mesh T-Pose
        ret = getMeshArrays_fn(src_Objs)
        kdTree = get_KdTree_for_vArray(ret)
        # kdTree = get_KdTree_for_vArray(ret[0][IDX_XYZ_V])

        # dest mesh T-Pose
        objData_dst = getMeshArrays_fn(sel_objs)

        # reset matrix. vert pos in world space
        from mathutils import Matrix
        matrix_array = []
        for obj in sel_objs:
            matrix_array.append(obj.matrix_world.copy()) # store transform
            # obj.data.transform(Matrix.Identity(4)) # set default transform
            # obj.matrix_basis = Matrix.Identity(4) # set default transform

        ###############################
        # get vertex bind array indices
        bind_array = []  # * len(objData_dst)
        for obj in objData_dst:
            v_array = []
            verts_dst = obj[IDX_XYZ_V]  # get vert array
            for vert in verts_dst:
                # bestIdx = 0
                co_find = (vert[0], vert[1], vert[2])
                co, bestIdx, dist = kdTree.find(co_find)
                # v_array.append(bestIdx)  # TODO add src mesh index..
                bind_array.append(bestIdx)
            # bind_array.append(v_array)

        ################
        # loop through each frame, get animation data from source
        for fr in range(end_fr + 1 - start_fr):
            vPos_src = []
            fr_cur = fr + start_fr

            # print progress
            if total_frames < 50 or (fr % 20) == 0:
                printProgress_fn(fr_cur, total_frames, prefix)

            bpy.context.scene.frame_set(fr_cur)

            ret = getMeshArrays_fn(src_Objs)
            for o in ret:
                for v in o[IDX_XYZ_V]:
                    vPos_src.append(v)

            # animate the destination mesh.
            vOffs = 0
            for obj in sel_objs:
                for vIdx, vert in enumerate(obj.data.vertices):
                    # add local transforms
                    vert.co = Vector(vPos_src[bind_array[vOffs+ vIdx]])
                    # vert.co = v_pos * obj.matrix_world * obj.matrix_world.inverted()
                    # add vertex keyframe
                    insert_key(vert, 'co', group="Vertex %s" % vIdx)
                vOffs += len(obj.data.vertices)

        for i, obj in enumerate(sel_objs):
            # obj.matrix_basis = matrix_array[i]
            # obj.data.transform(matrix_array[i].inverted())
            obj.data.calc_normals_split()
            obj.data.update()

        # set frame
        bpy.context.scene.frame_set(cur_frame)
        # return to edit mode if neded
        if act_obj:
            get_objects_all(bpy.context).active = act_obj
            bpy.ops.object.mode_set(mode=edit_mode)

        refresh_ui_keyframes()

        printDone_fn(start_time, prefix)
        self.report({'INFO'}, "Retarget Animation: Done")
        print("===================")
        return {'FINISHED'}


# button grid
class KINGPIN_UI_BUTTON_GRID(Operator):
    bl_idname = "kp.ui_btn_grid"
    bl_label = "Add Grid"
    bl_description = (
        "Adds a bounding box grid set to 256 units.\n"
        "Use this tool so you can snap vertex to suit md2/x compresion grid\n"
        "Repeat clicking 'Add Grid' will delete/update the existing grid dimensions"
    )

    # @classmethod
    # def poll(self, context):
    #     return (context.selected_objects and context.selected_objects[0].type in {'MESH'})

    def execute(self, context):
        names = ["kp_grid_x", "kp_grid_y", "kp_grid_z"]
        objMin = [99999.0] * 3
        objMax = [-99999.0] * 3
        key_prop = context.window_manager.kp_tool_
        devis = key_prop.ui_subdiv

        #set mode object
        if not (bpy.context.mode == 'OBJECT'):
            bpy.ops.object.mode_set(mode='OBJECT')  # , toggle=False)

        #remove grid from selection
        # active
        # context.selected_objects:  # bpy.data.objects:
        for obj in get_objects_selected(context): #.selected:
            for i in range(3):
                ln = len(names[i])
                if obj.name[:ln] == names[i]:
                    set_select_state(context=obj, opt=False)

        # get selected array
        edit_mode, act_obj, sel_objs = set_mode_get_obj(context)
        # check array length
        if len(sel_objs) < 1:  # not context.selected_objects:
            print("Nothing selected")
            return {'FINISHED'}

        # deselect any objects
        for obj in get_objects_selected(context): # .selected:  # bpy.data.objects:
            set_select_state(context=obj, opt=False)

        ###############################
        # get bounding box in selection
        bMin = [] * 3
        bMax = [] * 3
        vX = []
        vY = []
        vZ = []
        ret_objs = getMeshArrays_fn(sel_objs)
        for obj in ret_objs:
            for v in obj[IDX_XYZ_V]:
                vX.append(v[0])
                vY.append(v[1])
                vZ.append(v[2])
        objMin[0], objMin[1], objMin[2] = min(vX), min(vY), min(vZ)
        objMax[0], objMax[1], objMax[2] = max(vX), max(vY), max(vZ)


        ############################
        # find existing grid. delete
        for obj in get_objects_all(context): #bpy.data.objects:
            found = False
            for i in range(3):
                if obj.name[:len(names[i])] == names[i]:
                    found = True
                    break
            if found:
                bpy.data.objects.remove(obj) # todo 2.79?

        ################################
        # build bounds/position/rotation
        width = [
            (objMax[0] - objMin[0]),
            (objMax[1] - objMin[1]),
            (objMax[2] - objMin[2])
        ]
        widthXYZ = [
            [width[2], width[1], 0],
            [width[0], width[2], 0],
            [width[0], width[1], 0],
        ]
        midXYZ = [
            [objMin[0], (width[1] / 2 + objMin[1]), (width[2] / 2 + objMin[2])],
            [(width[0] / 2 + objMin[0]), objMin[1], (width[2] / 2 + objMin[2])],
            [(width[0] / 2 + objMin[0]), (width[1] / 2 + objMin[1]), objMin[2]]
        ]
        from math import radians
        rot = radians(90)
        rotXYZ = [
            [0, rot, 0], # x
            [rot, 0, 0], # y
            [0, 0, 0], # z
        ]
        # bpy.context.view_layer.objects.selected
        # bpy.context.view_layer.objects.active  #context.active_object
        ####################
        # generate new grid/s
        # subdivision in B3.0 uses face count
        divFix = devis if check_version(3, 00, 0) < 0 else (devis - 1)
        rng = 1 if key_prop.ui_floor_cube else 3  # skip X+Y grid
        for i in range(rng):
            bpy.ops.mesh.primitive_grid_add(x_subdivisions=divFix,
                                            y_subdivisions=divFix
                                            )  # size=width[i]) B2.8
            obj = get_objects_all(context).active
            if not obj or obj.name[0:4] != "Grid":
                raise Exception("Could not select grid")

            obj.name = names[(i+2)%3]  # z first
            obj.dimensions = widthXYZ[(i+2)%3]
            obj.location = midXYZ[(i+2)%3]
            obj.rotation_mode = 'XYZ'
            obj.rotation_euler = rotXYZ[(i+2)%3]
            obj.show_all_edges = True
            obj.show_wire = key_prop.ui_use_wire
            drawType = 'SOLID' if key_prop.ui_use_solid else 'WIRE'
            set_obj_draw_type(obj, drawType)

            set_select_state(context=obj, opt=False)

        #######################
        # select inital objects
        for obj in sel_objs:
            set_select_state(context=obj, opt=True)

        # return to edit mode
        if act_obj:  # TODO fix invalid state
            get_objects_all(bpy.context).active = act_obj
            bpy.ops.object.mode_set(mode=edit_mode)

        return {'FINISHED'}


# button smooth
class KINGPIN_UI_BUTTON_SMOOTH(Operator):
    bl_idname = "kp.ui_btn_smooth"
    bl_label = "Smooth Vertex"
    bl_description = (
        "After importing an animated md2/x, run this tool to smooth vertex position.\n" +
        "Use this tool for HD exports.")

    # @classmethod
    # def poll(self, context):
    #     return context.selected_objects and context.selected_objects[0].type in {'MESH'}

    def execute(self, context):
        ''' '''
        # get selected objects
        edit_mode, act_obj, sel_objs = set_mode_get_obj(context)

        # check valid selections
        if not is_selected_mesh(self, sel_objs):
            return {'FINISHED'}

        key_prop = context.window_manager.kp_tool_
        start_fr = key_prop.ui_smooth_start  # frame start
        end_fr = key_prop.ui_smooth_end  # frame end
        total_fr = end_fr - start_fr + 1
        cur_frame = bpy.context.scene.frame_current

        print("============\n"+
              "start smooth\n"+
              "============\nframes: %i" %(total_fr))
        prefix = "Get mesh data"
        start_time = printStart_fn()  # start timmer
        printProgress_fn(0, 1, prefix)  # print progress

        # check for md2 data attached to object
        hasAributes = True
        for oIdx, obj in enumerate(sel_objs):
            if DATA_F_SCALE not in obj.data or DATA_F_COUNT not in obj.data:
                print("No scale data(try re-import mesh)")
                self.report({'WARNING'}, "No Scale Data")
                return {'FINISHED'}

            # check model data count
            if obj.data[DATA_F_COUNT] < end_fr:
                end_fr = obj.data[DATA_F_COUNT]
                total_fr = end_fr - start_fr + 1
                print("WARNING: end frame set to %i (model: %s)" % (end_fr, obj.name))

        ################################
        # get all object/frames
        # [frame] [object] [(x,y,z)]
        fr_ob_v_pos = [
            [[[0] * 3 for v in range(len(o.data.vertices))]
             for o in sel_objs]
            for f in range(total_fr)
        ]
        # fr_ob_scale = [] # [frame] [object] [vIndex] [(scaleX, scaleY, scaleZ)]
        fr_ob_scale = [[0] * len(sel_objs) for f in range(total_fr)]

        # get model imported scale
        tmp_xyz = [0] * 3
        for oIdx, obj in enumerate(sel_objs):
            dat_scale = obj.data[DATA_F_SCALE]
            dat_f_count = obj.data[DATA_F_COUNT]
            for fr in range(total_fr):
                fr_cur = fr + start_fr
                if fr_cur >= dat_f_count:
                    fr_cur = dat_f_count-1 # stop overflow.
                for i in range(3):
                    tmp_xyz[i] = dat_scale[fr_cur*3+i]
                fr_ob_scale[fr][oIdx] = (tmp_xyz[0], tmp_xyz[1], tmp_xyz[2])

        # store vertex pos data
        for oIdx, obj in enumerate(sel_objs):
            dat_f_count = obj.data[DATA_F_COUNT]
            anim = obj.data.animation_data
            if anim is None or anim.action is None:
                print("No animation data(import anim as vertex)")
                self.report({'WARNING'}, "No animation data")
                return {'FINISHED'}
            # loop through vertex array
            for i in range(len(obj.data.vertices)):
                for j in range(3):
                    fcu = anim.action.fcurves[i*3+j] # x0, y0, z0, x1, y1, z1
                    # loop through frame time
                    for fr in range(total_fr):
                        fr_cur = fr + start_fr
                        if fr_cur >= dat_f_count:
                            fr_cur = dat_f_count-1 # stop overflow.

                        fr_ob_v_pos[fr][oIdx][i][j] = fcu.keyframe_points[fr_cur].co.y

        # if self.numFrames < 50 or (frame % 20) == 0:
        printProgress_fn(1, 1, prefix)  # print progress
        printDone_fn(start_time, prefix)

        prefix = "Shifting vertex"
        start_time = printStart_fn()  # start timmer
        printProgress_fn(0, 1, prefix)  # print progress

        ################################
        # smooth animations in mesh.
        # todo animation types. shapekey, vert..
        loop_fr = 0
        if key_prop.ui_smooth_loop == False:
            loop_fr = 1

        # mode 10.
        # if key_prop.ui_smooth_method == '10':
        for o_idx, obj in enumerate(sel_objs):
            dat_f_count = obj.data[DATA_F_COUNT]
            numVerts = len(obj.data.vertices)
            for vIdx in range(numVerts):
                tmp_fr = [0] * total_fr
                for fr in range(total_fr - loop_fr): #-2 or exact frames
                    fr_max = total_fr if key_prop.ui_smooth_loop else total_fr - fr
                    fr_cur = fr + start_fr
                    if fr_cur >= dat_f_count:
                        continue
                    fr1_sc = fr_ob_scale[fr][o_idx]
                    fr1_vPos = fr_ob_v_pos[fr][o_idx][vIdx]
                    vShift = list(fr1_vPos)
                    for i in range(3):
                        j = 0
                        while j < fr_max and j < 5:
                            fr2_vPos = fr_ob_v_pos[(fr+j+1) % total_fr][o_idx][vIdx]
                            diff_pos = fr2_vPos[i] - fr1_vPos[i]
                            diff_pos_abs = abs(diff_pos)
                            fr1_sc_x2 = fr1_sc[i]*2.5
                            if diff_pos_abs < fr1_sc_x2:
                                diff_pos_abs = (fr1_sc_x2 - diff_pos_abs) / fr1_sc[i]*2.0
                                dif = diff_pos * min(1.0, diff_pos_abs)
                                pow1 = (j*1+3)    # 2, 3, 4,  5,  6, , , , ,
                                #pow2 = ((j+1)*2)  # 2, 4, 6,  8, 10, , , , ,
                                #pow3 = 2 **(j+1)  # 2, 4, 8, 16, 32, , , , ,
                                vShift[i] += dif/pow1
                                j += 1
                            else:
                                j = 9999 # break loop
                    tmp_fr[fr] = (vShift[0], vShift[1], vShift[2])
                # write to vert cord
                for i in range(3):
                    fcu = anim.action.fcurves[vIdx*3+i]
                    for fr in range(total_fr - loop_fr):
                        fr_cur = fr + start_fr
                        if fr_cur >= dat_f_count:
                            continue
                        fcu.keyframe_points[fr_cur].co = fr_cur, tmp_fr[fr][i]  # x,y cords
                    fcu.update()


        for obj in sel_objs:
            # print("update..")
            obj.data.calc_normals_split()
            obj.data.update()

        #######################
        # done. select inital objects
        for obj in sel_objs:
            set_select_state(context=obj, opt=True)

        bpy.context.scene.frame_set(cur_frame)
        # return to edit mode
        if act_obj:  # TODO fix invalid state
            get_objects_all(bpy.context).active = act_obj
            bpy.ops.object.mode_set(mode=edit_mode)

        printDone_fn(start_time, prefix)  # Done.

        print("============")
        self.report({'INFO'}, "Smoothing Animation: Done")
        return {'FINISHED'}


classes = (
    KINGPIN_UI_BUTTON_GRID,
    KINGPIN_UI_BUTTON_DRIVER,
    KINGPIN_UI_BUTTON_SMOOTH,
    VIEW3D_PT_Tool_GUI_IMPORT,
    VIEW3D_PT_Tool_GUI_EXPORT,
    VIEW3D_PT_Tool_GUI_GRID,
    VIEW3D_PT_Tool_GUI_SMOOTH,
    VIEW3D_PT_Tool_GUI_DEFORM,
)


def register():
    for cls in classes:
        # make_annotations(cls)
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
