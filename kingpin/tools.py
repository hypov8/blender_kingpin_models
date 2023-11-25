'''
=====================
kingpin tools Toolbar
=====================

md2 grid
retarget animation
smooth
'''


import bpy
from bpy.types import (
    Operator,
    Panel,
    WindowManager,
    # AddonPreferences,
)
from bpy.props import (
    BoolProperty,
    # StringProperty,
    EnumProperty,
    IntProperty,
    PointerProperty,
    FloatProperty,
)

from mathutils import Vector, kdtree  # Matrix, Euler

# from . import common_kp
from .common_kp import (
    get_ui_collection,
    make_annotations,
    get_objects_all,
    get_objects_selected,
    getMeshArrays_fn,
    set_select_state,
    set_mode_get_obj,
    refresh_ui_keyframes,
    printStart_fn,
    printProgress_fn,
    printDone_fn,
    IDX_XYZ_V,
    DATA_F_SCALE,
    DATA_V_BYTE,
    DATA_F_COUNT,
    DATA_V_COUNT,
)


def removeInvalidSource(array):
    ''' discard non mesh '''
    out = []
    for o in array:
        if o == None: continue
        if o.type == 'MESH':
            out.append(o)
    return out


def isValidMeshArray(array):
    ''' only mesh '''
    for o in array:
        if o == None: continue
        if o.type != 'MESH':
            return True
    return False


def insert_key(data, key, group=None):
    ''' insert key to vertex '''
    try:
        if group is not None:
            data.keyframe_insert(key, group=group)
        else:
            data.keyframe_insert(key)
    except print("ERROR: insert_key"):
        pass
# END insert_key()


# Property Definitions
class KINGPIN_Tools_Properties(bpy.types.PropertyGroup):
    '''UI varables '''

    #################
    # import/export #
    # TODO
    # ui_import_
    # ui_export_

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
        description=(
            "Pick the object/mesh you want to use to" +
            "drive the selected object\\s."
        ),
        type=bpy.types.Object,
        # poll=lambda self,
        # update=update
    )

    ui_group_type = get_ui_collection(bpy.types)  # bpy.types.Collection
    ui_drv_obj_picker_group = PointerProperty(
        name="Source",
        description=(
            "Pick the object/mesh you want to use to" +
            "drive the selected object\\s."
        ),
        type=ui_group_type
    )
    ###########
    # Smooth #
    ui_smooth_scale = FloatProperty(
        name="scale:",
        min=0.01,
        max=1.0,
        default=1.0,
        description=("How much to snooth verts. Relative to previous/next frame")
    )
    ui_smooth_method = EnumProperty(
        name="Mode",
        description="Differnt calculation modes to smooth vertex positions",
        items=[
            ('1', "1. SMOOTH 3AVG", "get average of 3 position.", 1),
            ('2', "2. SMOOTH 3DIF", "add the differnce of f 3 position. normailized", 2),
            ('3', "3. SMOOTH FWD+", "search forward untill no match(2> grid). then average it", 3),
            ('4', "4. SMOOTH POW+", "serach forward but add falloff values", 4),
            ('5', "5. SMOOTH 5AVG", "get average of 5 position", 5),
            ('6', "6. SMOOTH 6AVG", "get average of 5 position", 6),
            ('7', "7. SMOOTH 7AVG", "get average of 5 position", 7),
            ('8', "8. SMOOTH 8AVG", "get average of 5 position", 8),
            ('9', "9. Tri-Smooth 5x", "Average -2 & +2 frames, triangle weighted", 9),
            ('10', "10. Tri-Smooth 3x", "Average -2 & +2 frames, triangle weighted", 10)

        ],
        default='10'
    )
    # ui_smooth_method = BoolProperty(
    #     name="Vanila Method",
    #     description=(
    #         "Enabled: assumes md2 export used truncated values. no rounding(vanila)\n" +
    #         "Disabled: use when mesh was exported using some rounding method (blender, max)\n"),
    #     default=True,
    # )
    # frame range
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
        default=41, #385,
        description="Set End frame to copy animation data"
    )
    # options
    ui_smooth_use_bbox = BoolProperty(
        name="Automatic Grid",
        description=(
            "Calculate 256 grid spacing, used in mesh export's\n" +
            "Automactic: uses bbox/256 to calculate grid spacing. (Select whole model for PPM)\n" +
            "Manual: spacing finds x/y/z distance between verts.\n" +
            " Not all verts may fall on each row. So a multiplicator factor is added"
        ),
        default=True,
    )
    ui_smooth_x = IntProperty(
        name="X:",
        min=1,
        max=256,
        default=1,
        description=("X scale for manual spacing")
    )
    ui_smooth_y = IntProperty(
        name="Y:",
        min=1,
        max=256,
        default=1,
        description=("Y scale for manual spacing")
    )
    ui_smooth_z = IntProperty(
        name="Z:",
        min=1,
        max=256,
        default=1,
        description=("Z scale for manual spacing")
    )
    ui_smooth_loop = BoolProperty(
        name="Looping Anim",
        description=(
            "Enabled: first and last fame will be included in the smooth process\n" +
            "  Use when you want to effect a pose, eg.. idle\n" +
            "Disabled: smooth all frame 'between' the start/end times\n"),
        default=True, # False
    )


# -=| GUI |=- #1 Grid
class VIEW3D_PT_Tool_GUI_GRID(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS' if bpy.app.version < (2, 80, 0) else 'UI'
    bl_category = 'Kingpin'
    bl_label = 'MD2 Grid'
    bl_options = {'DEFAULT_CLOSED'}
    # bl_options = {'HEADER_LAYOUT_EXPAND'}
    # UI

    def draw(self, context):
        kp_tool_ = context.window_manager.kp_tool_

        layout = self.layout

        col = layout.column(align=True)
        # Build Grid #
        row = col.row()
        # row.alignment = 'CENTER'
        row.label(text="Build Grid:")
        box = col.box()
        row = box.row()  # align=True # row.alignment = 'EXPAND'
        row.prop(kp_tool_, "ui_use_solid")
        row = box.row()
        row.prop(kp_tool_, "ui_floor_cube")
        row = box.row()
        row.prop(kp_tool_, "ui_subdiv")
        row = box.row()
        row.operator("kp.ui_btn_grid")


# -=| GUI |=- #2 Mesh deform
class VIEW3D_PT_Tool_GUI_DEFORM(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS' if bpy.app.version < (2, 80, 0) else 'UI'
    bl_category = 'Kingpin'
    bl_label = 'RETARGET ANIM'
    bl_options = {'DEFAULT_CLOSED'}
    # bl_options = {'HEADER_LAYOUT_EXPAND'}
    # UI

    def draw(self, context):
        kp_tool = context.window_manager.kp_tool_
        layout = self.layout
        col = layout.column(align=True)
        # Vertex Driver #
        row = col.row()
        # row.alignment = 'CENTER'
        row.label(text="Vertex Driver:")
        box = col.box()
        row = box.row()
        row.prop(kp_tool, "ui_drv_start")
        row.prop(kp_tool, "ui_drv_end")
        row = box.row()
        row.prop(kp_tool, "ui_drv_bind_fr")

        row = box.row()  # object/collection
        row.prop(kp_tool, "ui_drv_is_collection")
        row = box.row()
        if kp_tool.ui_drv_is_collection == True:
            row.prop(kp_tool, "ui_drv_obj_picker_group")
        else:
            row.prop(kp_tool, "ui_drv_obj_picker")

        row = box.row()
        row.operator("kp.ui_btn_driver")
        row = box.row()
        row.alignment = 'CENTER'
        row.operator("kp.ui_btn_driver_clear")


# -=| GUI |=- #3 Smooth md2 compresion
class VIEW3D_PT_Tool_GUI_SMOOTH(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS' if bpy.app.version < (2, 80, 0) else 'UI'
    bl_category = 'Kingpin'
    bl_label = 'MD2 Smooth'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        kp_tool = context.window_manager.kp_tool_
        layout = self.layout
        col = layout.column(align=True)
        # Build smooth #
        # row = col.row()
        # row.label(text="Smooth Compresion:")
        box = col.box()
        bRow = box.row()
        bRow.prop(kp_tool, "ui_smooth_scale")
        # range
        bRow = box.row()
        bRow.prop(kp_tool, "ui_smooth_start")
        bRow.prop(kp_tool, "ui_smooth_end")
        # options
        bRow = box.row()
        bRow.prop(kp_tool, "ui_smooth_method")
        bRow = box.row()
        bRow.prop(kp_tool, "ui_smooth_loop")
        bRow = box.row()
        bRow.prop(kp_tool, "ui_smooth_use_bbox")
        if kp_tool.ui_smooth_use_bbox == False:
            bRow = box.row()
            bRow.prop(kp_tool, "ui_smooth_x")
            bRow.prop(kp_tool, "ui_smooth_y")
            bRow.prop(kp_tool, "ui_smooth_z")
        # button
        bRow = box.row()
        bRow.alignment = 'CENTER'
        bRow.operator("kp.ui_btn_smooth")


# button remove animation
class KINGPIN_UI_BUTTON_DRIVER_CLEAR(Operator):
    '''remove all animation data'''
    bl_idname = "kp.ui_btn_driver_clear"
    bl_label = "Clear Anim"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = ("Remove all animations and shape keys")

    @classmethod
    def poll(self, context):
        return (context.selected_objects and
                context.selected_objects[0].type in {'MESH'}
                )

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_confirm(self, event)

    def execute(self, context):
        edit_mode, act_obj, sel_objs = set_mode_get_obj(context)
        frame = bpy.context.scene.frame_current

        if not len(sel_objs) or (sel_objs[0].type != 'MESH'):
            print("No valid mesh selected")
            self.report({'WARNING'}, "Select a valid mesh")
            return {'FINISHED'}

        for obj in sel_objs:
            if not obj.data:
                continue
            set_select_state(context=obj, opt=False)  # select object

            vArray = []
            # get vertex pos at current frame
            mesh = getMeshArrays_fn([obj])
            for v in mesh[0][IDX_XYZ_V]:
                vArray.append(v)

            # remove parent
            if obj.parent:
                # mat_copy = obj.matrix_world.copy()
                obj.parent = None
                # obj.matrix_world = mat_copy

            # clear the animation data
            obj.data.animation_data_clear()
            obj.animation_data_clear()
            # clear shapekey data
            sk_data = obj.data.shape_keys
            if sk_data:
                obj.active_shape_key_index = 0
                obj.data.update()
                sk_data.animation_data_clear()
                # if bpy.app.version >= (2, 80, 0):
                #    obj.shape_key_clear()
                keyblocks = reversed(sk_data.key_blocks)
                for sk in keyblocks:
                    obj.shape_key_remove(sk)

            # apply current position to vertex
            for i, v in enumerate(obj.data.vertices[:]):
                v.co = Vector(vArray[i])
            obj.data.update()

        for obj in sel_objs:
            if not obj.data:
                continue
            set_select_state(context=obj, opt=True)

        # return to edit mode if neded
        bpy.ops.object.mode_set(mode=edit_mode)

        refresh_ui_keyframes()
        self.report({'INFO'}, "Clear Animation: Done")
        return {'FINISHED'}


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

    @classmethod
    def poll(self, context):
        return (context.selected_objects and context.selected_objects[0].type in {'MESH'})
        # and not context.selected_objects[0].data.animation_data)

    def execute(self, context):
        '''add driver
        : data.vertices[0].co[0] (sum values) '''

        # def get_KdTree_for_vArray(vArray):
        #     '''https://blender.stackexchange.com/a/274223'''
        #     # mesh = blenderObject.data
        #     size = len(vArray)
        #     kd = kdtree.KDTree(size)
        #     for i, v in enumerate(vArray):
        #         kd.insert(v, i)
        #         # kd.insert(v.co, i)
        #     kd.balance()
        #     return kd
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

        def updateShapekeys(objs):
            '''update model shape keys(bug?)'''
            # bpy.context.view_layer.update()
            for ob in objs:
                ob.active_shape_key_index = 1
                ob.data.update()
                ob.active_shape_key_index = 0
                # if ob.data:  # and ob.data.shape_keys:
                ob.data.update()

        src_Objs = []
        edit_mode, act_obj, sel_objs = set_mode_get_obj(context)
        key_prop = context.window_manager.kp_tool_
        if key_prop.ui_drv_is_collection:
            if key_prop.ui_drv_obj_picker_group is not None:
                src_Objs = key_prop.ui_drv_obj_picker_group.objects
        else:
            src_Objs = [key_prop.ui_drv_obj_picker]
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
        src_Objs = removeInvalidSource(src_Objs)
        isFail = False if len(sel_objs) and len(src_Objs) else True
        isFail = isValidMeshArray(sel_objs) if not isFail else True
        # isFail = isValidMeshArray(src_Objs) if not isFail else True
        if isFail:
            print("No valid mesh selected")
            self.report({'WARNING'}, "Select a valid mesh")
            return {'FINISHED'}

        # updateShapekeys(sel_objs)  # outdated?

        # source mesh T-Pose
        ret = getMeshArrays_fn(src_Objs)
        kdTree = get_KdTree_for_vArray(ret)
        # kdTree = get_KdTree_for_vArray(ret[0][IDX_XYZ_V])

        # dest mesh T-Pose
        objData_dst = getMeshArrays_fn(sel_objs)

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
            # updateShapekeys(sel_objs)  # outdated?
            ret = getMeshArrays_fn(src_Objs)
            for o in ret:
                for v in o[IDX_XYZ_V]:
                    vPos_src.append(v)

            # animate the destination mesh.
            vOffs = 0
            for obj in sel_objs:
                for vIdx, vert in enumerate(obj.data.vertices):
                    # vert.co = Vector(vPos_src[bind])
                    vert.co = Vector(vPos_src[bind_array[vOffs+ vIdx]])
                    insert_key(vert, 'co', group="Vertex %s" % vIdx)
                vOffs += len(obj.data.vertices)

        for obj in sel_objs:
            obj.data.calc_normals_split()
            obj.data.update()

        # set frame
        bpy.context.scene.frame_set(cur_frame)
        # return to edit mode if neded
        if act_obj:
            get_objects_all(bpy.context).active = act_obj
            bpy.ops.object.mode_set(mode=edit_mode)
        # updateShapekeys(sel_objs)  # outdated?

        refresh_ui_keyframes()

        printDone_fn(start_time, prefix)
        self.report({'INFO'}, "Retarget Animation: Done")
        print("===================")
        return {'FINISHED'}


# button grid
class KINGPIN_UI_BUTTON_GRID(Operator):
    bl_idname = "kp.ui_btn_grid"
    bl_label = "Add Grid (for selected)"
    bl_description = (
        "Adds a bounding box grid set to 256 units.\n"
        "Use this tool so you can snap vertex to suit md2/x compresion grid\n"
        "Repeat clicking 'Add Grid' will delete/update the existing grid dimensions"
    )

    @classmethod
    def poll(self, context):
        return (context.selected_objects and context.selected_objects[0].type in {'MESH'})

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
        for obj in sel_objs:
            bMin = obj.bound_box[0]
            bMax = obj.bound_box[6]
            for i in range(3):
                if objMin[i] > bMin[i]:
                    objMin[i] = bMin[i]
                if objMax[i] < bMax[i]:
                    objMax[i] = bMax[i]
        # done get all objects bbox

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
        divFix = devis if bpy.app.version < (3, 00, 0) else (devis - 1)
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
            if hasattr(obj, "draw_type"):  # if bpy.app.version < (2, 80, 0):
                obj.draw_type = drawType
            else:
                obj.display_type = drawType
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
    bl_idname = "kp.ui_btn_smooth"  # "kp.ui_btn_grid"
    bl_label = "Smooth Vertex"
    bl_description = (
        "After importing an animated md2/x, run this tool to smooth vertex position.\n" +
        "Use this tool for HD exports.")

    @classmethod
    def poll(self, context):
        return context.selected_objects and context.selected_objects[0].type in {'MESH'}

    def execute(self, context):
        ''' '''
        # get selected objects
        edit_mode, act_obj, sel_objs = set_mode_get_obj(context)

        # check valid selections
        isFail = False if len(sel_objs) else True
        isFail = isValidMeshArray(sel_objs) if not isFail else True
        if isFail:
            print("No valid mesh selected")
            self.report({'WARNING'}, "Select a valid mesh")
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
            if (not DATA_V_BYTE in obj.data or
                    not DATA_F_SCALE in obj.data or
                    not  DATA_F_COUNT in obj.data or
                    not  DATA_V_COUNT in obj.data):
                hasAributes = False
                break
            fr_count = obj.data[DATA_F_COUNT]
            v_count = obj.data[DATA_V_COUNT]
            if DATA_F_COUNT in obj.data and obj.data[DATA_F_COUNT] < end_fr:
                hasAributes = False
                break
            if DATA_V_COUNT in obj.data and obj.data[DATA_V_COUNT] < len(obj.data.vertices):
                hasAributes = False
                break

        ################################
        # get all object/frames
        #fr_ob_v_pos = []
        #fr_ob_min_v = [] # [frame] [(x,y,z)]
        #fr_ob_max_v = [] # [frame] [(x,y,z)]
        #fr_ob_v_idx = [] # [frame] [object] [(x,y,z)] # note: grid index
        # fr_scale = [] # [frame] [(scaleX, scaleY, scaleZ)]
        fr_ob_scale = [] # [frame] [object] [(scaleX, scaleY, scaleZ)]

        fr_ob_v_pos = [  # [frame] [object] [(x,y,z)]
            [[[0] * 3 for v in range(len(o.data.vertices))]
                for o in sel_objs]
            for f in range(total_fr)
        ]
        fr_ob_scale = [[0] * len(sel_objs) for f in range(total_fr)]

        # get model imported scale
        tmp_xyz = [0] * 3
        for oIdx, obj in enumerate(sel_objs):
            dat_scale = obj.data[DATA_F_SCALE]
            for fr in range(total_fr):
                fr_cur = fr + start_fr
                for i in range(3):
                    tmp_xyz[i] = dat_scale[fr_cur*3+i]
                fr_ob_scale[fr][oIdx] = (tmp_xyz[0], tmp_xyz[1], tmp_xyz[2])

        # todo option.. if more then 1 object. find max
        # sstore vertex pos data
        for oIdx, obj in enumerate(sel_objs):
            anim = obj.data.animation_data
            if anim is None or anim.action is None:
                continue
            # l1 = len(anim.action.fcurves)
            # l2 = numVerts * 3
            # loop through vertex array
            for i in range(len(obj.data.vertices)):
                for j in range(3):
                    fcu = anim.action.fcurves[i*3+j] # x0, y0, z0, x1, y1, z1
                    # loop through frame time
                    for fr in range(total_fr):
                        fr_cur = fr + start_fr
                        #    [frame] [object] [vertex](x,y,z)
                        fr_ob_v_pos[fr][oIdx][i][j] = fcu.keyframe_points[fr_cur].co.y

        ######### old ##################
        # old method...
        for fr in range(0): #total_fr):
            fr_ob_v = []
            fr_cur = fr + start_fr
            bpy.context.scene.frame_set(fr_cur)
            ret = getMeshArrays_fn(sel_objs)
            for o in ret:
                pos = []
                for v in o[IDX_XYZ_V]:
                    pos.append(v)
                fr_ob_v.append(pos)
            fr_ob_v_pos.append(fr_ob_v)

            # get bbox from blender object
            if key_prop.ui_smooth_use_bbox == True:
                objMin = [99999.0] * 3
                objMax = [-99999.0] * 3
                for obj in sel_objs:
                    bMin = obj.bound_box[0]  # -x,-y,-z
                    bMax = obj.bound_box[6]  # +x,+y,+z
                    for i in range(3):
                        if objMin[i] > bMin[i]: objMin[i] = bMin[i]
                        if objMax[i] < bMax[i]: objMax[i] = bMax[i]
                # grid scale factor. use bounds/256
                if not hasAributes:
                    fr_scale.append((((objMax[0] - objMin[0]) / 256),
                                     ((objMax[1] - objMin[1]) / 256),
                                     ((objMax[2] - objMin[2]) / 256)))
                fr_ob_min_v.append((objMin[0], objMin[1], objMin[2]))
                fr_ob_max_v.append(((objMax[0] - objMin[0]),
                                    (objMax[1] - objMin[1]),
                                    (objMax[2] - objMin[2])))
            else:
                # add vertex data to frame array
                ob_x, ob_y, ob_z = [], [], []
                for o in ret:
                    pX, pY, pZ = [], [], []
                    for v in o[IDX_XYZ_V]:
                        pX.append(v[0])
                        pY.append(v[1])
                        pZ.append(v[2])
                    ob_x.append(pX)
                    ob_y.append(pY)
                    ob_z.append(pZ)
                ob_x.sort()
                ob_y.sort()
                ob_z.sort()

                sX = sY = sZ = 9999999.0
                vCount = len(ob_x)
                # get shortest dist for each axis
                for i in range(vCount-1): #, (x, y, z) in enumerate(zip(pX, pY, pZ)):
                    px_ = ob_x[i+1] - ob_x[i]
                    py_ = ob_y[i+1] - ob_y[i]
                    pz_ = ob_z[i+1] - ob_z[i]
                    if px_ != 0.0 and sX > px_:
                         sX = px_
                    if py_ != 0.0 and sY > py_:
                         sY = py_
                    if pz_ != 0.0 and sZ > pz_:
                         sZ = pz_
                # add user scale factor
                sX *= key_prop.ui_smooth_x
                sY *= key_prop.ui_smooth_y
                sZ *= key_prop.ui_smooth_z
                if not hasAributes:
                    fr_scale.append((sX, sY, sZ))
                fr_ob_min_v.append((ob_x[0], ob_y[0], ob_z[0]))
                fr_ob_max_v.append((ob_x[vCount-1], ob_y[vCount-1], ob_z[vCount-1]))

            # isdx = float(255.0 / xMax) if xMax != 0.0 else 0.0
            # isdy = float(255.0 / yMax) if yMax != 0.0 else 0.0
            # isdz = float(255.0 / zMax) if zMax != 0.0 else 0.0
            #     int(((vert[0] - min[0]) * isdx) + 0.5),
            #     int(((vert[1] - min[1]) * isdy) + 0.5),
            #     int(((vert[2] - min[2]) * isdz) + 0.5),
            # fr_ob_min_v = [] # [frame] [(x,y,z)]
            # fr_ob_max_v = [] # [frame] [(x,y,z)]


            ############
            # build 256 grid for each object
            fr_ob_id = []
            isd = [0] * 3
            xMax = fr_ob_max_v[fr][0]  #- fr_ob_min_v[fr][0]  # bbox size
            yMax = fr_ob_max_v[fr][1]  #- fr_ob_min_v[fr][1]  # bbox size
            zMax = fr_ob_max_v[fr][2]  #- fr_ob_min_v[fr][2]  # bbox size
            isd[0] = float(255.0 / xMax) if xMax != 0.0 else 0.0
            isd[1] = float(255.0 / yMax) if yMax != 0.0 else 0.0
            isd[2] = float(255.0 / zMax) if zMax != 0.0 else 0.0

            # build
            if hasAributes:
                minSc = [99999999.0] * 3

                for oIdx, obj in enumerate(sel_objs):
                    pos = []
                    dat_scale = obj.data[DATA_F_SCALE]
                    dat_vIdx = obj.data[DATA_V_BYTE]
                    dat_vCount = obj.data[DATA_V_COUNT]
                    curIdx = fr_cur * (dat_vCount*3) # start vertex index
                    for xyz in range(dat_vCount):
                        # curIdx = startIdx+(xyz*3)
                        # vertex XYZ
                        pos.append((dat_vIdx[curIdx], dat_vIdx[curIdx+1], dat_vIdx[curIdx+2]))
                        curIdx += 3
                    fr_ob_id.append(pos)

                    # TODO report scale missmatch??
                    for i in range(3):
                        sc = dat_scale[fr_cur*3+i]
                        if minSc[i] > sc:
                            minSc[i] = sc
                #store new scale
                fr_scale.append((minSc[0], minSc[1], minSc[2]))
            else:
                # for oIdx in range(len(fr_ob_v_pos[fr])):
                for oIdx in range(len(sel_objs)):
                    pos = []
                    for xyz in fr_ob_v_pos[fr][oIdx]:
                        idx = [0] * 3
                        for v in range(3): # vertex xyz
                            idx[v] = int(((xyz[v] - fr_ob_min_v[fr][v]) * isd[v]) + 0.1)
                        pos.append(idx)
                    fr_ob_id.append(pos)

            # append vertex grid location
            fr_ob_v_idx.append(fr_ob_id)

        # if self.numFrames < 50 or (frame % 20) == 0:
        printProgress_fn(1, 1, prefix)  # print progress
        printDone_fn(start_time, prefix)

        prefix = "Shifting vertex"
        start_time = printStart_fn()  # start timmer
        printProgress_fn(0, 1, prefix)  # print progress

        ################################
        # smooth animations in mesh.
        # todo animation types. shapekey, vert..
        # st_index = 0 if (key_prop.ui_smooth_method == '3' or
        #                  key_prop.ui_smooth_method == '4' or
        #                  key_prop.ui_smooth_method == '5' or
        #                  key_prop.ui_smooth_method == '6') else 1
        # start at frame2 for 3 average mode
        st_index = 1 if (key_prop.ui_smooth_method == '1' or
                         key_prop.ui_smooth_method == '2' or
                         key_prop.ui_smooth_method == '3') else 0
        loop_fr = 0
        if key_prop.ui_smooth_loop == False:
            if st_index == 1:
                loop_fr = 2
            else:  # if st_index == 0:
                loop_fr = 1

        # mode 10.
        if key_prop.ui_smooth_method == '10':  # and use_vert_anims == True:
            for o_idx, obj in enumerate(sel_objs):
                # use_vert_anims = False
                numVerts = len(obj.data.vertices)
                fr1_ob = fr_ob_v_pos[fr][o_idx]
                # has vertex animation data? (import vertex mode)
                anim = obj.data.animation_data
                if anim is not None and anim.action is not None:
                    l1 = len(anim.action.fcurves)
                    l2 = numVerts * 3
                    if l1 != l2:
                        continue
                        #use_vert_anims = True
                # vShift = [0] * 3
                for vIdx in range(numVerts):
                    tmp_fr = [0] * total_fr
                    for fr in range(total_fr - loop_fr): #-2 or exact frames
                        fr_max = total_fr if key_prop.ui_smooth_loop else total_fr - fr
                        fr_cur = fr + start_fr
                        # fr1_sc = fr_scale[fr]
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
                            fcu.keyframe_points[fr_cur].co = fr_cur, tmp_fr[fr][i]  # x,y cords
                        fcu.update()

        ########### old ################
        # loop through all frames
        for fr in range(0): # total_fr - loop_fr): #-2 or exact frames
            fr_cur = fr + start_fr + st_index
            fr_max = total_fr if key_prop.ui_smooth_loop else total_fr - fr
            # bpy.context.scene.frame_set(fr_cur)
            fr_sc1 = fr_scale[fr]  # %total_fr
            vShift = [0] * 3
            for o_idx, obj in enumerate(sel_objs):
                use_vert_anims = False
                numVerts = len(obj.data.vertices)
                fr1_ob = fr_ob_v_pos[fr][o_idx]
                # has vertex animation data? (import vertex mode)
                anim = obj.data.animation_data
                if anim is not None and anim.action is not None:
                    l1 = len(anim.action.fcurves)
                    l2 = numVerts * 3
                    if l1 == l2:
                        use_vert_anims = True

                ##########################
                # mode 1. average 3 vertex
                if key_prop.ui_smooth_method == '1':
                    fr2_ob = fr_ob_v_pos[(fr+1) % total_fr][o_idx]
                    fr3_ob = fr_ob_v_pos[(fr+2) % total_fr][o_idx]
                    fr_sc2 = fr_scale[(fr+1) % total_fr]
                    fr_sc3 = fr_scale[(fr+2) % total_fr]
                    for vIdx, vert in enumerate(obj.data.vertices):
                        vFr1, vFr2, vFr3 = fr1_ob[vIdx], fr2_ob[vIdx], fr3_ob[vIdx]
                        vShift[0], vShift[1], vShift[2] = vert.co.x, vert.co.y, vert.co.z
                        isShift = 0
                        for i in range(3):
                            if (abs(vFr1[i]-vFr2[i]) < (fr_sc2[i]*2) and abs(vFr3[i]-vFr2[i]) < (fr_sc2[i]*2)):
                                vShift[i] = (vFr1[i] + vFr2[i] + vFr3[i]) / 3
                                isShift = 1
                        if isShift:
                            vert.co = Vector(vShift)
                            insert_key(vert, 'co', group="Vertex %s" % vIdx)
                #######################################
                # mode 2.  average 3 vertex. normalized
                elif key_prop.ui_smooth_method == '2':
                    fr2_ob = fr_ob_v_pos[(fr+1) % total_fr][o_idx]
                    fr3_ob = fr_ob_v_pos[(fr+2) % total_fr][o_idx]
                    fr_sc2 = fr_scale[(fr+1) % total_fr]
                    fr_sc3 = fr_scale[(fr+2) % total_fr]
                    oFr1_min = fr_ob_min_v[fr]
                    oFr2_min = fr_ob_min_v[(fr+1) % total_fr]
                    oFr3_min = fr_ob_min_v[(fr+2) % total_fr]
                    for vIdx, vert in enumerate(obj.data.vertices):
                        vFr1, vFr2, vFr3 = fr1_ob[vIdx], fr2_ob[vIdx], fr3_ob[vIdx]
                        vShift[0], vShift[1], vShift[2] = vert.co.x, vert.co.y, vert.co.z
                        isShift = 0
                        for i in range(3):
                            gIdx1 = int((vFr1[i]-oFr1_min[i]) * fr_sc1[i]+ 0.5)
                            gIdx2 = int((vFr2[i]-oFr2_min[i]) * fr_sc2[i]+ 0.5)
                            gIdx3 = int((vFr3[i]-oFr3_min[i]) * fr_sc3[i]+ 0.5)

                            # dist1 = abs(vFr1[i]-vFr2[i])
                            # dist2 = abs(vFr3[i]-vFr2[i])
                            # dist3 = abs(vFr1[i]-vFr3[i])
                            if (gIdx1+1 >= gIdx2 and gIdx1-1 <= gIdx2 and
                                gIdx3+1 >= gIdx2 and gIdx3-1 <= gIdx2):
                                #if (abs(vFr1[i]-vFr2[i]) < (obSc[i]*2) and abs(vFr3[i]-vFr2[i]) < (obSc[i]*2)):
                                # ofD = abs(vFr1[i] - vFr3[i]) # get differnce
                                # vShift[i] += ofD * 0.5 * key_prop.ui_smooth_scale # add midpoint
                                # ofD =  abs(vFr1[i] - vFr3[i]) * 0.5 * key_prop.ui_smooth_scale
                                # ofD2 = vFr1[i] if vFr1[i] < vFr3[i] else vFr3[i]
                                # vShift[i] = (ofD2 + ofD)  # add midpoint

                                ofD = (vFr1[i] + vFr3[i]) / 2

                                # ofD = (vFr1[i] +vFr3[i])/2
                                # ofD = vFr1[i] if vFr1[i] < vFr3[i] else vFr3[i]
                                vShift[i] = ofD  # add midpoint
                                # TODO method blender
                                isShift = 1

                            # vert.co = Vector(vPos_src[bind])
                            # TODO check shapekey
                        if isShift:
                            vert.co = Vector(vShift)
                            insert_key(vert, 'co', group="Vertex %s" % vIdx)
                    # vOffs += len(obj.data.vertices)
                ######################################
                # mode 3. look forward until no match. then avaerage
                elif key_prop.ui_smooth_method == '3':
                    numVerts = len(obj.data.vertices)
                    # oFr1_min = fr_ob_min_v[fr]
                    # oFr2_min = fr_ob_min_v[(fr+1) % total_fr]
                    # oFr3_min = fr_ob_min_v[(fr+2) % total_fr]
                    for vIdx, vert in enumerate(obj.data.vertices):
                        vFr1 = fr1_ob[vIdx]
                        vShift[0], vShift[1], vShift[2] = vert.co.x, vert.co.y, vert.co.z

                        j = 0
                        while j < total_fr:
                            fr2_ob = fr_ob_v_pos[(fr+j+1) % total_fr][o_idx]
                            vFr2 = fr2_ob[(vIdx) % numVerts]
                            fr_sc2 = fr_scale[(fr+j+1) % total_fr]
                            isShift = 0
                            for i in range(3):
                                dif = vFr2[i] - vFr1[i]
                                if (dif != 0.0 and abs(dif) < (fr_sc2[i]*2)):
                                    vShift[i] += (dif/2) / ((j+1)*2)
                                    isShift = 1
                            if isShift:
                                vert.co = Vector(vShift)
                                insert_key(vert, 'co', group="Vertex %s" % vIdx)
                                j += 1
                            else:
                                j = numVerts  #exit
                ######################################
                # mode 4. look forward untill no match
                elif key_prop.ui_smooth_method == '4':
                    for vIdx, vert in enumerate(obj.data.vertices):
                        vFr1 = fr1_ob[vIdx]
                        vShift[0], vShift[1], vShift[2] = vert.co.x, vert.co.y, vert.co.z
                        fr1_vIdx = fr_ob_v_idx[fr][o_idx][vIdx]
                        j = 0
                        isShift = 0
                        while j < fr_max or j < 10: # TODO limit to 10?
                            fr2_vIdx = fr_ob_v_idx[(fr+j+1) % total_fr][o_idx][vIdx]
                            fr_sc2 = fr_scale[(fr+j+1) % total_fr]
                            pow1 = 2** (j+1)
                            pow2 = ((j+1)*2)
                            for i in range(3):
                                diff_idx = fr2_vIdx[i] - fr1_vIdx[i]
                                dif = diff_idx * fr_sc2[i]
                                if isShift == 0 and diff_idx == 0: isShift = 2
                                if (diff_idx == -1  or diff_idx == 1 or
                                    diff_idx == -2  or diff_idx == 2 or
                                    diff_idx == -3  or diff_idx == 3):

                                    # vShift[i] += dif/(2+j)
                                    # vShift[i] += (dif/2) / ((j+1)/2) #
                                    # vShift[i] += (dif) / ((j+1)*2)   # <1.0> /2,    /4,   /6,   /8,   /10,
                                    vShift[i] += (dif/2) / ((j+1)*2) # <0.5> /2,    /4,   /6,   /8,   /10,
                                    # vShift[i] += (dif/2) * (2/(j+2)) # <0.5> *1, *0.66, *0.5, *0.4, *0.33, *0.285
                                    # vShift[i] += (dif/2) / ((j+1)*2)
                                    # vShift[i] += (dif/2) / pow1
                                    # if diff_idx > 0:
                                    #     vShift[i] += (fr_sc1[i]/2) / pow1
                                    isShift = 1
                            if isShift == 0:
                                j = total_fr  #exit
                            else:
                                j += 1
                        # write to vert cord
                        if isShift == 1 and use_vert_anims == True:
                            for i in range(3):
                                fcu = anim.action.fcurves[vIdx*3+i]
                                kf = fcu.keyframe_points[fr]
                                kf.co = kf.co.x, vShift[i]
                                fcu.update()
                # todo
                elif key_prop.ui_smooth_method == '5':
                    for vIdx, vert in enumerate(obj.data.vertices):
                        vFr1 = fr1_ob[vIdx]
                        fr1_vIdx = fr_ob_v_idx[fr][o_idx][vIdx]
                        vShift[0], vShift[1], vShift[2] = vert.co.x, vert.co.y, vert.co.z
                        j = 0
                        isShift = [0] *3
                        while j < fr_max and j < 5:
                            fr2_vIdx = fr_ob_v_idx[(fr+j+1) % total_fr][o_idx][vIdx]
                            fr_sc2 = fr_scale[(fr+j+1) % total_fr]
                            # pow1 = 2** (j+1)
                            # pow2 = ((j+1)*2)
                            for i in range(2, 3):
                                diff_idx = fr2_vIdx[i] - fr1_vIdx[i]
                                if isShift[i] == 0 and diff_idx == 0:
                                    isShift[i] = 2  # not moved. but next frame might shift
                                if diff_idx != 0:
                                    if  diff_idx >= -2 and diff_idx <= 2: #2
                                        # invert distance
                                        dif = (3 - diff_idx) if diff_idx > 0 else (3 + diff_idx)
                                        dif *= fr_sc2[i]    #2(-diff_idx) *
                                        vShift[i] += (dif/4) / ((j+1)*2) # <0.5> /2,    /4,   /6,   /8,   /10,
                                        isShift[i] = 1
                                    else:
                                         isShift[i] = 0
                            if isShift[0] == 0 and  isShift[1] == 0 and isShift[2] == 0:
                                j = total_fr  # exit
                            else:
                                j += 1
                        # write to vert cord
                        if use_vert_anims == True:
                            for i in range(3):
                                if isShift[i] == 1:
                                    fcu = anim.action.fcurves[vIdx*3+i]
                                    kf = fcu.keyframe_points[fr_cur]
                                    kf.co = kf.co.x, vShift[i]
                                    fcu.update()

                elif key_prop.ui_smooth_method == '6':
                    for vIdx, vert in enumerate(obj.data.vertices):
                        # vFr1 = fr1_ob[vIdx]
                        fr1_vIdx = fr_ob_v_idx[fr][o_idx][vIdx]
                        vShift[0], vShift[1], vShift[2] = vert.co.x, vert.co.y, vert.co.z
                        if fr_cur == 20 and vIdx == 21:
                            junk = 1 # debugger
                        for i in range(3):
                            j = 0
                            isShift = 0
                            while j < fr_max and j < 5:
                                fr2_vIdx = fr_ob_v_idx[(fr+j+1) % total_fr][o_idx][vIdx]
                                fr_sc2 = fr_scale[(fr+j+1) % total_fr]
                                diff_idx = fr2_vIdx[i] - fr1_vIdx[i]
                                # not shifted. but next frame might shift
                                if diff_idx == 0:
                                    j += 1
                                # has moved within 2 grid tolerence?
                                elif diff_idx >= -2 and diff_idx <= 2:
                                    dif = (3 - diff_idx) if diff_idx > 0 else (-3 - diff_idx)
                                    dif *= fr_sc2[i]    #2(-diff_idx) *
                                    vShift[i] += (dif/4) / ((j+1)*2) # <0.5> /2,    /4,   /6,   /8,   /10,
                                    isShift = 1
                                    j += 1
                                else:
                                    j = total_fr  # break loop
                            # write to vert cord
                            if use_vert_anims == True and isShift == 1:
                                fcu = anim.action.fcurves[vIdx*3+i]
                                kf = fcu.keyframe_points[fr_cur]
                                kf.co = kf.co.x, vShift[i]  # x,y cords
                                fcu.update()
                ######################################
                # mode 7.
                elif key_prop.ui_smooth_method == '7':
                    for vIdx, vert in enumerate(obj.data.vertices):
                        fr1_vIdx = fr_ob_v_idx[fr][o_idx][vIdx]
                        vShift[0], vShift[1], vShift[2] = vert.co.x, vert.co.y, vert.co.z
                        # if fr_cur == 3 and vIdx == 213:
                        if fr_cur == 0 and vIdx == 197:
                            junk = 1 # debugger
                        for i in range(1):
                            j = 0
                            isShift = 0
                            while j < fr_max and j < 7:
                                # fr1_vIdx = fr_ob_v_idx[(fr+j+0) % total_fr][o_idx][vIdx]
                                fr2_vIdx = fr_ob_v_idx[(fr+j+1) % total_fr][o_idx][vIdx]
                                diff_idx = abs(fr2_vIdx[i] - fr1_vIdx[i])
                                # has moved within 2 grid tolerence?
                                if diff_idx >= 0 and diff_idx <= 2:
                                    fr1_vPos = fr_ob_v_pos[(fr+j+0) % total_fr][o_idx][vIdx]
                                    fr2_vPos = fr_ob_v_pos[(fr+j+1) % total_fr][o_idx][vIdx]
                                    diff_pos = fr2_vPos[i] - fr1_vPos[i]
                                    if diff_idx > 0: diff_idx -= 1
                                    diff_idx = (3 - diff_idx) / 3 # invert, scale 0.0 to 1.0
                                    dif = diff_pos * diff_idx
                                    vShift[i] += dif/(j*1+2)
                                    isShift = 1
                                    j += 1
                                else:
                                    j = total_fr  # break loop
                            # write to vert cord
                            if use_vert_anims == True and isShift == 1:
                                fcu = anim.action.fcurves[vIdx*3+i]
                                kf = fcu.keyframe_points[fr_cur]
                                kf.co = kf.co.x, vShift[i]  # x,y cords
                                fcu.update()
                ######################################
                # mode 8.
                elif key_prop.ui_smooth_method == '8':
                    for vIdx, vert in enumerate(obj.data.vertices):
                        fr1_sc = fr_scale[fr]
                        fr1_vPos = fr_ob_v_pos[fr][o_idx][vIdx]
                        fr1_vIdx = fr_ob_v_idx[fr][o_idx][vIdx]
                        vShift[0], vShift[1], vShift[2] = fr1_vPos[0], fr1_vPos[1], fr1_vPos[2]
                        # vShift[0], vShift[1], vShift[2] = vert.co.x, vert.co.y, vert.co.z

                        # if fr_cur == 3 and vIdx == 213:
                        if fr_cur == 24 and vIdx == 58:
                            junk = 1 # debugger
                        for i in range(3):
                            j = 0
                            isShift = 0
                            while j < fr_max and j < 5:
                                fr2_sc = fr_scale[(fr+j+1) % total_fr]
                                # fr1_vIdx = fr_ob_v_idx[(fr+j+0) % total_fr][o_idx][vIdx]
                                #fr2_vIdx = fr_ob_v_idx[(fr+j+1) % total_fr][o_idx][vIdx]
                                #diff_idx = abs(fr2_vIdx[i] - fr1_vIdx[i])

                                fr2_vPos = fr_ob_v_pos[(fr+j+1) % total_fr][o_idx][vIdx]

                                diff_pos = fr2_vPos[i] - fr1_vPos[i]
                                diff_pos_abs = abs(diff_pos)
                                fr1_sc_x2 = fr1_sc[i]*2.5
                                #fr2_sc_x2 = fr2_sc[i]*2.5
                                # has moved within 2 grid tolerence?
                                if diff_pos_abs < fr1_sc_x2:
                                    # fr3_vPos = fr_ob_v_pos[(fr+j+0) % total_fr][o_idx][vIdx]
                                    # diff_pos_23 = fr2_vPos[i] - fr3_vPos[i]
                                    diff_pos_abs = fr1_sc_x2 - diff_pos_abs # inverse
                                    diff_pos_abs = diff_pos_abs / fr1_sc[i] # fr1_sc_x2  # 1.0 to 0.0
                                    diff_pos_abs = min(1.0, diff_pos_abs)
                                    # if diff_pos_abs > 1.0: diff_pos_abs = 1.0
                                    dif = diff_pos * diff_pos_abs
                                    #dif = diff_pos_23 * diff_pos_abs
                                    # pow1 = (j*1+2)    # 2, 3, 4,  5,  6, , , , ,
                                    pow2 = ((j+1)*2)  # 2, 4, 6,  8, 10, , , , ,
                                    # pow3 = 2 **(j+1)  # 2, 4, 8, 16, 32, , , , ,
                                    # pow4 = pow(2, j+1)
                                    #pow2 = ((j+2)*2)  # 2, 6, 8,  10, 12, , , , ,
                                    vShift[i] += dif/pow2
                                    isShift = 1
                                    j += 1
                                else:
                                    j = total_fr  # break loop
                            # write to vert cord
                            if use_vert_anims == True and isShift == 1:
                                fcu = anim.action.fcurves[vIdx*3+i]
                                kf = fcu.keyframe_points[fr_cur]
                                kf.co = kf.co.x, vShift[i]  # x,y cords
                                fcu.update()

                ######################################
                # mode 9. copy 8
                elif key_prop.ui_smooth_method == '9':
                    for vIdx in range(numVerts): # enumerate(obj.data.vertices):
                        fr1_sc = fr_scale[fr]
                        fr1_vPos = fr_ob_v_pos[fr][o_idx][vIdx]
                        fr1_vIdx = fr_ob_v_idx[fr][o_idx][vIdx]
                        vShift[0], vShift[1], vShift[2] = fr1_vPos[0], fr1_vPos[1], fr1_vPos[2]
                        # vShift[0], vShift[1], vShift[2] = vert.co.x, vert.co.y, vert.co.z
                        if fr_cur == 0 and vIdx == 23:
                            junk = 1 # debugger
                        for i in range(3):
                            j = 0
                            isShift = 0
                            fr1_sc_x2 = fr1_sc[i]*3.0
                            #fr2_sc_x2 = fr2_sc[i]*2.5
                            while j < fr_max and j < 8:
                                fr2_vPos = fr_ob_v_pos[(fr+j+1) % total_fr][o_idx][vIdx]
                                diff_pos = fr2_vPos[i] - fr1_vPos[i]
                                diff_pos_abs = abs(diff_pos)
                                # has moved within 2 grid tolerence?
                                if diff_pos_abs < fr1_sc_x2:
                                    diff_pos_abs = fr1_sc_x2 - diff_pos_abs # inverse
                                    # diff_pos_abs = diff_pos_abs / fr1_sc[i] # fr1_sc_x2  # 1.0 to 0.0
                                    diff_pos_abs = (diff_pos_abs / fr1_sc_x2)*1.25  # 1.0 to 0.0
                                    dif = diff_pos * min(1.0, diff_pos_abs)
                                    pow1 = (j*1+2)    # 2, 3, 4,  5,  6, , , , ,
                                    pow2 = ((j+1)*2)  # 2, 4, 6,  8, 10, , , , ,
                                    pow3 = 2 **(j+1)  # 2, 4, 8, 16, 32, , , , ,
                                    # pow4 = pow(2, j+1)
                                    vShift[i] += dif/pow3
                                    isShift = 1
                                    j += 1
                                else:
                                    j = total_fr  # break loop
                            # write to vert cord
                            if use_vert_anims == True and isShift == 1:
                                fcu = anim.action.fcurves[vIdx*3+i]
                                kf = fcu.keyframe_points[fr_cur]
                                kf.co = kf.co.x, vShift[i]  # x,y cords
                                fcu.update()

                ######################################
                # mode 9. triangle smooth, 5 frames
                elif key_prop.ui_smooth_method == '210':
                    # vShift = [0.0] * 3
                    for vIdx, vert in enumerate(obj.data.vertices):
                        # vShift[0], vShift[1], vShift[2] = vert.co.x, vert.co.y, vert.co.z
                        fr1_vPos = fr_ob_v_pos[(fr-2) % total_fr][o_idx][vIdx]
                        fr2_vPos = fr_ob_v_pos[(fr-1) % total_fr][o_idx][vIdx]
                        fr3_vPos = fr_ob_v_pos[(fr+0) % total_fr][o_idx][vIdx]
                        fr4_vPos = fr_ob_v_pos[(fr+1) % total_fr][o_idx][vIdx]
                        fr5_vPos = fr_ob_v_pos[(fr+2) % total_fr][o_idx][vIdx]
                        # pos5 = [[0.0]*3] * 5
                        pos5 = [[0.0 for xyz in range(3)] for tm in range(5)]

                        for i in range(3):
                            if key_prop.ui_smooth_loop:
                                pos5[0][i] = fr1_vPos[i] - fr3_vPos[i]
                                pos5[1][i] = fr2_vPos[i] - fr3_vPos[i]
                                pos5[3][i] = fr4_vPos[i] - fr3_vPos[i]
                                pos5[4][i] = fr5_vPos[i] - fr3_vPos[i]
                            else:
                                # negative numbers
                                if fr > 1:
                                    pos5[0][i] = fr1_vPos[i] - fr3_vPos[i]
                                    pos5[1][i] = fr2_vPos[i] - fr3_vPos[i]
                                elif fr > 0:
                                    pos5[1][i] = fr2_vPos[i] - fr3_vPos[i]

                                # positive numbers
                                if fr < total_fr-1: # -2??
                                    pos5[3][i] = fr4_vPos[i] - fr3_vPos[i]
                                    pos5[4][i] = fr5_vPos[i] - fr3_vPos[i]
                                elif  fr < total_fr: # -1??
                                    pos5[3][i] = fr4_vPos[i] - fr3_vPos[i]

                                # av = (pos5[0][i] + pos5[1][i]*2 + pos5[2][i]*3 + pos5[3][i]*2 + pos5[4][i]) / 9
                                av = fr3_vPos[i] + (pos5[1][i]/2 + pos5[3][i]/2 )
                                # write to vert cord
                                if use_vert_anims == True:
                                    fcu = anim.action.fcurves[vIdx*3+i]
                                    kf = fcu.keyframe_points[fr_cur]
                                    kf.co = kf.co.x, av  # vShift[i]  # x,y cords
                                    fcu.update()

                #########################
                # todo junk
                elif key_prop.ui_smooth_method == '22':
                    for vIdx, vert in enumerate(obj.data.vertices):
                        vFr1 = fr1_ob[vIdx]
                        vFr2 = fr2_ob[vIdx]
                        vFr3 = fr3_ob[vIdx]
                        vShift[0] = vert.co.x
                        vShift[1] = vert.co.y
                        vShift[2] = vert.co.z
                        isShift = 0
                        for i in range(3):
                            dist1 = abs(vFr1[i]-vFr2[i])
                            dist2 = abs(vFr3[i]-vFr2[i])
                            dist3 = abs(vFr1[i]-vFr3[i])

                            if (abs(vFr1[i]-vFr2[i]) < (obSc[i]*2) and abs(vFr3[i]-vFr2[i]) < (obSc[i]*2)):
                                # check is if moved within 1 grid
                                # method vanila

                                # ofD = abs(vFr1[i] - vFr3[i]) # get differnce
                                # vShift[i] += ofD * 0.5 * key_prop.ui_smooth_scale # add midpoint

                                # ofD =  abs(vFr1[i] - vFr3[i]) * 0.5 * key_prop.ui_smooth_scale
                                # ofD2 = vFr1[i] if vFr1[i] < vFr3[i] else vFr3[i]
                                # vShift[i] = (ofD2 + ofD)  # add midpoint

                                ofD = (vFr1[i] + vFr2[i] +vFr3[i])/3
                                # ofD2 = vFr1[i] if vFr1[i] < vFr3[i] else vFr3[i]
                                vShift[i] = ofD  # add midpoint
                                # TODO method blender
                                isShift = 1

                            # vert.co = Vector(vPos_src[bind])
                            # TODO check shapekey
                        if isShift:
                            vert.co = Vector(vShift)
                            insert_key(vert, 'co', group="Vertex %s" % vIdx)
                    # vOffs += len(obj.data.vertices)

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


classes = [
    KINGPIN_Tools_Properties,
    VIEW3D_PT_Tool_GUI_GRID,  # toolbar
    VIEW3D_PT_Tool_GUI_DEFORM,
    VIEW3D_PT_Tool_GUI_SMOOTH,
    KINGPIN_UI_BUTTON_GRID,
    KINGPIN_UI_BUTTON_DRIVER,
    KINGPIN_UI_BUTTON_DRIVER_CLEAR,
    KINGPIN_UI_BUTTON_SMOOTH,
]


def register():
    for cls in classes:
        make_annotations(cls)
        bpy.utils.register_class(cls)
    WindowManager.kp_tool_ = PointerProperty(type=KINGPIN_Tools_Properties)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del WindowManager.kp_tool_
