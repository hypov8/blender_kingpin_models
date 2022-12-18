
"""
Toolbar grid
"""


import bpy
from bpy.types import (
    Operator,
    Panel,
    WindowManager,
    # AddonPreferences,
)
from bpy.props import (
    BoolProperty,
    StringProperty,
    EnumProperty,
    IntProperty,
    PointerProperty,
)

from mathutils import Vector, kdtree  # Matrix, Euler

# from . import common_kp
from .common_kp import (
    make_annotations,
    set_select_state,
    get_objects,
    getMeshArrays_fn,
    refresh_ui_keyframes,
    IDX_XYZ_V
)


# TODO move to common
def set_mode_get_obj(context):
    '''set object mode=OBJECT, get active.object and selected.objects
    : return(
        : current object mode,
        : active object
        : selected objects (array)
    )
    '''
    edit_mode = context.mode
    retObj = None
    if edit_mode == 'EDIT_MESH':
        edit_mode = 'EDIT'
    # TODO add extra modes

    act_obj = bpy.context.active_object
    if edit_mode != 'OBJECT':
        retObj = [act_obj]
        bpy.ops.object.mode_set(mode='OBJECT')
    else:
        retObj = bpy.context.selected_objects

    return edit_mode, act_obj, retObj


# Property Definitions
class KINGPIN_Tools_Properties(bpy.types.PropertyGroup):
    # UI varables
    ########
    # Grid #
    ui_use_solid = BoolProperty(
        name=" Solid mode:",
        description="Skinned or Wireframe",
        default=False,
    )
    ui_use_wire = BoolProperty(
        name=" Wireframe:",
        description="view as wireframe",
        default=True,
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
            "Kingpin plugin exported models are 256 units\n"
            "  so make sure its correct or you are using a custom bounding box(fix seams)"
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
        description=("At what frame to get the vertex position for driving the mesh\n" +
                     "Usage: Set a frame that both mesh are aligned. eg T-post.")

    )
    ui_drv_obj_picker = PointerProperty(
        name="Source",
        description="Pick the object/mesh you want to drive the selected object\\s.",
        type=bpy.types.Object,
        # poll=lambda self,
        # update=update
    )


# GUI #1 Grid
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


# GUI #2 Mesh deform
class VIEW3D_PT_Tool_GUI_DEFORM(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS' if bpy.app.version < (2, 80, 0) else 'UI'
    bl_category = 'Kingpin'
    bl_label = 'RETARGET ANIM'
    bl_options = {'DEFAULT_CLOSED'}
    # bl_options = {'HEADER_LAYOUT_EXPAND'}
    # UI

    def draw(self, context):
        kp_tool_ = context.window_manager.kp_tool_
        layout = self.layout
        col = layout.column(align=True)
        # Vertex Driver #
        row = col.row()
        # row.alignment = 'CENTER'
        row.label(text="Vertex Driver:")
        box = col.box()
        row = box.row()
        row.prop(kp_tool_, "ui_drv_start")
        row.prop(kp_tool_, "ui_drv_end")
        row = box.row()
        row.prop(kp_tool_, "ui_drv_bind_fr")
        row = box.row()
        # row.label(text="Driver (source mesh)")
        # row = box.row()
        row.prop(kp_tool_, "ui_drv_obj_picker")
        row = box.row()
        row.operator("kp.ui_btn_driver")
        row = box.row()
        row.alignment = 'CENTER'
        row.operator("kp.ui_btn_driver_clear")


# button remove animation
class KINGPIN_UI_BUTTON_DRIVER_CLEAR(Operator):
    '''remove all animation data'''
    bl_idname = "kp.ui_btn_driver_clear"
    bl_label = "Clear Anim"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = ("Remove all animations and shape keys")

    @classmethod
    def poll(self, context):
        return context.selected_objects and context.selected_objects[0].type in {'MESH'}

    def execute(self, context):
        edit_mode, act_obj, selObj = set_mode_get_obj(context)
        frame = bpy.context.scene.frame_current

        if not len(selObj) or (selObj[0].type != 'MESH'):
            print("No valid mesh selected")
            self.report({'WARNING'}, "Select a valid mesh")
            return {'FINISHED'}

        for obj in selObj:
            if not obj.data:
                continue
            set_select_state(context=obj, opt=False)  # select object

            vArray = []
            # get vertex pos at current frame
            mesh = getMeshArrays_fn(self, [obj], frame, False)
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
                obj.shape_key_clear()

            for i, v in enumerate(obj.data.vertices[:]):
                v.co = Vector(vArray[i])
            obj.data.update()

        for obj in selObj:
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
    bl_description = ("Animate a mesh using vertex keyframes.\n"
                      "Set 'Start:' and 'End:' time range that you want animations from\n"
                      "set 'Bind Frame' to a frame that both models are in close proximity(T-Pose)\n"
                      "Set the 'Source:' object(that have the animations you want)\n"
                      "Press Animate Mesh.\n"
                      "If all went well. The static mesh should be animated via 'Source:' object.")

    @classmethod
    def poll(self, context):
        return (context.selected_objects and context.selected_objects[0].type in {'MESH'})
        # and not context.selected_objects[0].data.animation_data)

    def execute(self, context):
        '''add driver
        : data.vertices[0].co[0] (sum values) '''

        def get_KdTree_for_vArray(vArray):
            '''https://blender.stackexchange.com/a/274223'''
            # mesh = blenderObject.data
            size = len(vArray)
            kd = kdtree.KDTree(size)
            for i, v in enumerate(vArray):
                kd.insert(v, i)
                # kd.insert(v.co, i)
            kd.balance()
            return kd
        # END get_KdTree_for_vArray()

        def insert_key(data, key, group=None):
            data_ = None
            try:
                if group is not None:
                    data.keyframe_insert(key, group=group)
                else:
                    data.keyframe_insert(key)
            except print("ERROR: insert_key"):
                pass
        # END insert_key()

        edit_mode, act_obj, sel_obj = set_mode_get_obj(context)
        key_prop = context.window_manager.kp_tool_
        src_Obj = [key_prop.ui_drv_obj_picker]
        # frame  data
        start_fr = key_prop.ui_drv_start
        end_fr = key_prop.ui_drv_end
        bind_fr = key_prop.ui_drv_bind_fr
        cur_frame = bpy.context.scene.frame_current
        bpy.context.scene.frame_set(bind_fr)
        getUV = 0

        if (not len(sel_obj) or not len(src_Obj) or
            (sel_obj[0].type != 'MESH') or (src_Obj[0].type != 'MESH') or
                src_Obj[0] in sel_obj):
            print("No valid mesh selected")
            self.report({'WARNING'}, "Select a valid mesh")
            return {'FINISHED'}

        # source mesh T-Pose

        ret = getMeshArrays_fn(self, src_Obj, bind_fr, False)
        kdTree = get_KdTree_for_vArray(ret[0][IDX_XYZ_V])
        # dest mesh T-Pose
        objData_dst = getMeshArrays_fn(self, sel_obj, bind_fr, False)

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
                v_array.append(bestIdx)
            bind_array.append(v_array)

        ################
        # loop through each frameget animation data from source
        for i in range(end_fr + 1 - start_fr):
            frIdx = i + start_fr
            bpy.context.scene.frame_set(frIdx)
            ret = getMeshArrays_fn(self, src_Obj, frIdx, False)
            vPos_src = ret[0][IDX_XYZ_V]

            # animate the  destination mesh
            for i, obj in enumerate(sel_obj):
                for j, (vert, bind) in enumerate(zip(obj.data.vertices, bind_array[i])):
                    vert.co = Vector(vPos_src[bind])
                    insert_key(vert, 'co', group="Vertex %s" % j)

        for obj in sel_obj:
            print("update..")
            obj.data.calc_normals_split()
            obj.data.update()

        print("Frames: %i" % (end_fr + 1 - start_fr))

        # return to edit mode if neded
        bpy.ops.object.mode_set(mode=edit_mode)  # if not (edit_mode == 'OBJECT'):
        # set frame
        bpy.context.scene.frame_set(cur_frame)

        refresh_ui_keyframes()
        self.report({'INFO'}, "Retarget Animation: Done")
        return {'FINISHED'}


# button grid
class KINGPIN_UI_BUTTON_GRID(Operator):
    bl_idname = "kp.ui_btn_grid"
    bl_label = "Add Grid (for selected)"
    bl_description = ("Adds a bounding box grid set to 256 units.\n"
                      "Use this feature so you can snap vertex to suit md2/x compresion grid\n"
                      "Repeat clicking 'Add Grid' will delete/update the existing grid dimensions")

    @classmethod
    def poll(self, context):
        return context.selected_objects and context.selected_objects[0].type in {'MESH'}

    def execute(self, context):
        edit_mode, act_obj, selObj = set_mode_get_obj(context)

        if len(selObj) < 1:  # not context.selected_objects:
            print("Nothing selected")
            return {'FINISHED'}

        names = ["kp_grid_x", "kp_grid_y", "kp_grid_z"]
        objMin = [99999.0] * 3
        objMax = [-99999.0] * 3
        key_prop = context.window_manager.kp_tool_
        devis = key_prop.ui_subdiv

        ###############################
        # get bounding box in selection
        for obj in context.selected_objects:
            skip = False
            for i in range(3):
                ln = len(names[i])
                if obj.name[:ln] == names[i]:
                    skip = True
                    break
            if not skip:
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
        for obj in bpy.data.objects:
            found = False
            for i in range(3):
                ln = len(names[i])
                if obj.name[:ln] == names[i]:
                    found = True
                    break
            if found:
                if obj in selObj:
                    selObj.remove(obj)  # remove from group
                bpy.data.objects.remove(obj)

        if len(selObj) < 1:
            print("No models selected")
            return {'FINISHED'}

        ################################
        # build bounds/position/rotation
        width = [(objMax[0] - objMin[0]), (objMax[1] - objMin[1]), (objMax[2] - objMin[2])]
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
            [0, rot, 0],
            [rot, 0, 0],
            [0, 0, 0],
        ]

        # subdivision in B3.0 uses face count
        divFix = devis if bpy.app.version < (3, 00, 0) else (devis - 1)

        ####################
        # generate new grid/s
        for i in range(3):
            if (i < 2) and key_prop.ui_floor_cube:
                continue  # skip X+Y grid

            bpy.ops.mesh.primitive_grid_add(x_subdivisions=divFix,
                                            y_subdivisions=divFix
                                            )  # size=width[i]) B2.8
            obj = context.selected_objects[0]  # get new onject
            if not obj:
                raise Exception("Could not get selection")

            obj.name = names[i]
            obj.dimensions = widthXYZ[i]
            obj.location = midXYZ[i]
            obj.rotation_mode = 'XYZ'
            obj.rotation_euler = rotXYZ[i]
            obj.show_all_edges = True
            obj.show_wire = key_prop.ui_use_wire
            if hasattr(obj, "draw_type"):  # if bpy.app.version < (2, 80, 0):
                obj.draw_type = 'SOLID' if key_prop.ui_use_solid else 'WIRE'
            else:
                obj.display_type = 'SOLID' if key_prop.ui_use_solid else 'WIRE'
            set_select_state(context=obj, opt=False)

        #######################
        # select inital objects
        for obj in selObj:
            if obj:
                if obj == act_obj:
                    get_objects(bpy.context).active = obj
                set_select_state(context=obj, opt=True)

        # return to edit mode
        get_objects(bpy.context).active = act_obj
        bpy.ops.object.mode_set(mode=edit_mode)  # if not (edit_mode == 'OBJECT'):

        return {'FINISHED'}


classes = [
    KINGPIN_Tools_Properties,
    VIEW3D_PT_Tool_GUI_GRID,  # toolbar
    KINGPIN_UI_BUTTON_GRID,
    VIEW3D_PT_Tool_GUI_DEFORM,
    KINGPIN_UI_BUTTON_DRIVER,
    KINGPIN_UI_BUTTON_DRIVER_CLEAR
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
