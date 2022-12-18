# SPDX-License-Identifier: GPL-2.0-or-later
# "Daniel Salazar <zanqdo@gmail.com>"

'''
hypov8
using animall plugin tool bar with only vertex/ShapeKey enabled

added:
- key to update frame data

Note: Use full 'AnimAll' plugin if you want full control.
      This light version is only suitable for an imported mesh via the kingpin script
'''


from ensurepip import version
import bpy
from bpy.types import (
    Operator,
    Panel,
    # AddonPreferences,
)
from bpy.props import (
    BoolProperty,
    EnumProperty,
    StringProperty,
    IntProperty,
    CollectionProperty,
    PointerProperty,
)

from bpy.app.handlers import persistent

from . import common_kp

from .common_kp import (
    get_preferences,
    make_annotations,
    get_menu_import,
    get_menu_export,
    set_select_state,
    get_layers,
)


# Utility functions
def refresh_ui_keyframes():
    try:
        for area in bpy.context.screen.areas:
            if area.type in ('TIMELINE', 'GRAPH_EDITOR', 'DOPESHEET_EDITOR'):
                area.tag_redraw()
    except print("ERROR: refresh_ui_keyframes"):
        pass


def insert_key(data, key, group=None):
    data_ = None
    try:
        if group is not None:
            data.keyframe_insert(key, group=group)
        else:
            data.keyframe_insert(key)
    except print("ERROR: insert_key"):
        pass


def delete_key(data, key):
    try:
        data.keyframe_delete(key)
    except print("ERROR: delete_key"):
        pass


@persistent
def post_frame_change(dummy):
    if bpy.context.mode != 'OBJECT':
        mode = bpy.context.object.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        obj = bpy.context.active_object
        sk_data = obj.data.shape_keys
        is_vertex = (not obj.active_shape_key and
                     not obj.active_shape_key_index and
                     not sk_data)
        bpy.context.scene.objects.active = bpy.context.scene.objects.active
        bpy.ops.object.mode_set(mode=mode)

        print("post_frame_change1")
    pass


@persistent
def pre_frame_change(dummy):
    if bpy.context.mode != 'OBJECT':
        bpy.context.active_object.update_from_editmode()
        bpy.context.scene.objects.active = bpy.context.scene.objects.active
        print("pre_frame_change1")
    pass


# Property Definitions
class AnimallProperties_KP(bpy.types.PropertyGroup):
    # auto update frame change
    def chkBox_autoUpdateFrame(self, context):
        if self.key_frame:
            bpy.app.handlers.frame_change_pre.append(pre_frame_change)
            bpy.app.handlers.frame_change_post.append(post_frame_change)
            print("Enable class: frame change")
        else:
            bpy.app.handlers.frame_change_pre.remove(pre_frame_change)
            bpy.app.handlers.frame_change_post.remove(post_frame_change)
            print("Disable class: frame change")

    key_keytype_in = EnumProperty(
        name="Type",
        description="interpolation for keyframe F-Curve",
        items=[
            ('NONE', "-----", "Use Default interpolation", 0),
            ('CONSTANT', "Constant",
             "No interpolation, value of A gets held until B is encountered", 'IPO_CONSTANT', 1),
            ('LINEAR', "Linear",
             "Straight-line interpolation between A and B (i.e. no ease in/out).", 'IPO_LINEAR', 2),
            ('BEZIER', "Bezier",
             "Smooth interpolation between A and B, with some control over curve shape.", 'IPO_BEZIER', 3),
            ('SINE', "Sinusoidal",
             "Sinusoidal easing (weakest, almost linear but with a slight curvature).", 'IPO_SINE', 4),
            ('QUAD', "Quadratic",
             "Quadratic easing", 'IPO_QUAD', 5),
            ('CUBIC', "Cubic",
             "Cubic easing", 'IPO_CUBIC', 6),
            ('QUART', "Quartic",
             "Quartic easing", 'IPO_QUART', 7),
            ('QUINT', "Quintic",
             "Quintic easing", 'IPO_QUINT', 8),
            ('EXPO', "Exponential",
             "Exponential easing (dramatic)", 'IPO_EXPO', 9),
            ('CIRC', "Circular",
             "Circular easing (strongest and most dynamic)", 'IPO_CIRC', 10),
            ('BACK', "Back",
             "Cubic easing with overshoot and settle", 'IPO_BACK', 11),
            ('BOUNCE', "Bounce",
             "Exponentially decaying parabolic bounce, like when objects collide.", 'IPO_BOUNCE', 12),
            ('ELASTIC', "Elastic",
             "Exponentially decaying sine wave, like an elastic band.", 'IPO_ELASTIC', 13),
        ],
        default="NONE",
    )
    key_keytype_out = EnumProperty(
        name="Mode",
        description="Easing Type",
        items=[
            ('AUTO', "Automatic", "Easing type is chosen automatically based on what the type of interpolation", 0),
            ('EASE_IN', "Ease In", "Only on the end closest to the next keyframe.", 1),
            ('EASE_OUT', "Ease Out", "Only on the end closest to the first keyframe.", 2),
            ('EASE_IN_OUT', "Ease In-Out", "Segment between both keyframes.", 3),
        ],
        default="AUTO",
    )

    # used
    key_frame = BoolProperty(
        name="Live Update",
        description="Update mesh every time the frame is chaged",
        update=chkBox_autoUpdateFrame,
        default=False
    )


# GUI (Panel)
class VIEW3D_PT_animall_KP(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS' if bpy.app.version < (2, 80, 0) else 'UI'
    bl_category = 'Kingpin'
    bl_label = 'KEY FRAMES'
    bl_options = {'DEFAULT_CLOSED'}
    # bl_options = {'HEADER_LAYOUT_EXPAND'}

    '''@classmethod
    def poll(self, context):
        return context.active_object and context.active_object.type in {'MESH'}'''

    def draw(self, context):
        obj = context.active_object
        if not obj:
            layout = self.layout
            col = layout.column(align=True)
            row = col.row(align=True)
            row.label(text="No Active Object")
            return

        kp_tool_anim = context.window_manager.kp_tool_anim
        sk_activ = obj.active_shape_key
        sk_index = obj.active_shape_key_index
        sk_data = obj.data.shape_keys  # 2.79 fix
        is_vertex = (not sk_data or
                     (sk_activ and not sk_index))

        # print("sk_a={}\nsk_id={}\nsk_dat={}\n".format(sk_activ, sk_index, "true" if sk_data else "false"))

        layout = self.layout
        col = layout.column(align=True)

        box = col.box()
        if not is_vertex and (sk_data and sk_data.use_relative):  # sk absolute
            box.enabled = False  # disable setting keyframes for shape keys
        row = box.row(align=True)
        row.alignment = 'EXPAND'
        row.label(text="Selected")
        row.label(text="All Vertex")
        row = box.row()
        row.alignment = 'EXPAND'  # 'EXPAND', 'LEFT', 'CENTER', 'RIGHT']
        row.scale_y = 1.2
        row.operator("anim.insert_keyframe_animall_kp", icon="KEY_HLT")
        row.operator("anim.insert_keyframe_animall_all_kp", icon="KEYINGSET")
        row = box.row()
        row.scale_y = 1.2
        row.operator("anim.delete_keyframe_animall_kp", icon="KEY_DEHLT")
        row.operator("anim.delete_keyframe_animall_all_kp", icon="KEY_DEHLT")
        # box.separator()
        row = box.row(align=True)
        row.operator("anim.clear_animation_animall_kp", icon="X")

        # keyframe Types in/out
        row = box.row()
        row.label(text="Interpolation", icon="IPO_CONSTANT")
        row = box.row()
        row.prop(kp_tool_anim, "key_keytype_in")
        row = box.row()
        row.prop(kp_tool_anim, "key_keytype_out")
        # end box #
        ###########

        # frame change box. fix for vertex animation bug
        col.separator()
        box = col.box()

        # live update option for vertex? not working
        # row = box.row(align=True)  # row 1
        # row.alignment = 'LEFT'
        # row.prop(kp_tool_anim, "key_frame")

        row = box.row(align=True)  # row 1. mode
        row.alignment = 'LEFT'
        if is_vertex:
            row.label(text="Vertex Mode", icon="VERTEXSEL")
        else:
            row.label(text="Shape Key Mode", icon="SHAPEKEY_DATA")

        # arrows
        row = box.row(align=True)  # row 2
        row.alignment = 'LEFT'
        row.operator("anim.frame_prev_kp")  # left arrow
        row.operator("anim.frame_next_kp")  # right arror
        row.operator("anim.frame_update_kp")  # update/sync button

        # frame number
        row = box.row()
        row.alignment = 'LEFT'
        strRow = ("Fr: %i" % bpy.context.scene.frame_current)

        # new objects wint have this updated yet
        sk_name = "Error:" if sk_activ is None else sk_activ.name

        if not is_vertex:
            ####################
            # absalute shapekeys
            if not sk_data.use_relative:  # sk absolute
                row.label(text="%s   SK: %s" % (strRow, sk_name))  # , icon="SHAPEKEY_DATA")
                if (sk_data and sk_data.key_blocks):
                    sk_frame = sk_data.key_blocks[sk_index].frame
                    curFrame = bpy.context.scene.frame_current
                    val = float(curFrame * 10)
                    frame_min = val - 0.01  # find close float
                    frame_max = val + 0.01  #
                    if not (sk_frame > frame_min and sk_frame < frame_max):
                        row = box.row()  # row 4
                        row.label(text="Shape Key Not sync'd", icon="INFO")
            ####################
            # relative shapekeys
            elif (sk_index > 0):
                row.label(text="%s   SK: %s" % (strRow, sk_name))  # , icon="SHAPEKEY_DATA")
                if sk_activ.value < 1:
                    row = box.row()  # row 4
                    row.label(text='sKey not 1.0? sync?', icon="INFO")
            elif (sk_activ or sk_data):
                key0_Name = sk_data.key_blocks[0].name if sk_data else sk_name
                row.label(text="%s   SK: %s (Base)" % (strRow, key0_Name))  # , icon="SHAPEKEY_DATA")
                row = box.row()  # row 4
                row.label(text="sKey: Index 0", icon="ERROR")  # index invalid
        # else:
        #    row.label(text="Vertex Mode", icon="VERTEXSEL")


# button frame 'prev'
class ANIM_OT_frame_prev_KP(Operator):
    bl_label = "<--"
    bl_idname = "anim.frame_prev_kp"
    bl_description = "Move timeline to previous frame. Auto Sync"
    bl_options = {'REGISTER'}  # , 'UNDO'}

    def execute(op, context):
        obj = context.active_object
        sk_data = obj.data.shape_keys
        is_vertex = (not obj.active_shape_key and
                     not obj.active_shape_key_index and
                     not sk_data)

        origFrame = bpy.context.scene.frame_current
        if origFrame >= 0:
            mode = context.object.mode
            if context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            if origFrame > 0:
                bpy.context.scene.frame_set(origFrame - 1, subframe=0.0)
                # select previous shapekey
                if not is_vertex:
                    if (obj.active_shape_key_index) > 0:
                        obj.active_shape_key_index -= 1

            bpy.ops.object.mode_set(mode=mode)
        return {'FINISHED'}


# button frame 'next'
class ANIM_OT_frame_next_KP(Operator):
    bl_label = "-->"
    bl_idname = "anim.frame_next_kp"
    bl_description = "Move timeline to next frame. Auto Sync"
    bl_options = {'REGISTER'}  # , 'UNDO'}

    def execute(op, context):
        obj = context.active_object
        sk_data = obj.data.shape_keys
        is_vertex = (not obj.active_shape_key and
                     not obj.active_shape_key_index and
                     not sk_data)

        mode = context.object.mode
        origFrame = bpy.context.scene.frame_current
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.scene.frame_set(origFrame + 1, subframe=0.0)
        bpy.ops.object.mode_set(mode=mode)
        # select next shapekey
        if not is_vertex:
            # print(len(obj.data.shape_keys.key_blocks))
            if (obj.active_shape_key_index + 1) < len(obj.data.shape_keys.key_blocks):
                obj.active_shape_key_index += 1

        return {'FINISHED'}


# button frame update/sync
class ANIM_OT_frame_update_KP(Operator):
    """
    """
    bl_label = "Sync"
    bl_idname = "anim.frame_update_kp"
    bl_description = ("Update/Sync Mesh. Use This after changing the Timeline\n"
                      "Shape key mode: will search for SK with 1.0 value, to match current frame\n"
                      "Vertex mode: will goto object mode, advance 1 frame then return to previous frame")
    bl_options = {'REGISTER'}  # , 'UNDO'}

    message = StringProperty(default="unset")

    def execute(op, context):
        obj = context.active_object
        sk_data = obj.data.shape_keys
        is_vertex = (not obj.active_shape_key and
                     not obj.active_shape_key_index and
                     not sk_data)
        mode = context.object.mode
        origFrame = bpy.context.scene.frame_current

        if context.mode != 'OBJECT':
            obj.update_from_editmode()
            bpy.ops.object.mode_set(mode='OBJECT')

        if is_vertex:
            bpy.context.scene.frame_set(origFrame + 1)
            bpy.context.scene.frame_set(origFrame)
            # TODO work out blender update().
            # only frame change working?

            # obj.update_tag(refresh={'OBJECT'})  # 'DATA' too if you care about geometry
            # context.scene.update()

            # obj.data.update()
            # context.scene.update()
            # obj.update_tag({'OBJECT', 'DATA', 'TIME'})
            # bpy.context.view_layer.depsgraph.update()  # 2.8
            # bpy.context.view_layer.update()  # 2.8
        elif not sk_data.use_relative:  # sk absolute
            val = float(origFrame * 10)
            frame_min = val - 0.01  # find close float
            frame_max = val + 0.01  #
            foundIdx = 0
            for i, sk in enumerate(sk_data.key_blocks):
                # var2 = sk.data
                if (sk.frame > frame_min and sk.frame < frame_max):
                    foundIdx = i
                    break
            obj.active_shape_key_index = foundIdx

        else:  # shape key relative
            active_sk = len(sk_data.key_blocks)
            foundIdx = 0
            for i, sk in enumerate(reversed(sk_data.key_blocks)):
                if sk.value == 1.0:  # find if shape key that matches active frame
                    foundIdx = active_sk - i - 1
                    break
            obj.active_shape_key_index = foundIdx

        bpy.ops.object.mode_set(mode=mode)

        '''obj.hide_render = obj.hide_render
        obj.data.update()
        context.scene.update()
        obj.update_tag({'OBJECT', 'DATA', 'TIME'})
        obj.update_from_editmode()'''

        # if not is_vertex:
        #     if (obj.active_shape_key_index + 1) < len(obj.data.shape_keys.key_blocks):
        #         obj.active_shape_key_index += 1

        return {'FINISHED'}


def insertKey_kp(context, allVerts=False):
    animProp_KP = context.window_manager.kp_tool_anim
    frame = bpy.context.scene.frame_current
    frame_min = bpy.context.scene.frame_current - 0.01  # find close float
    frame_max = bpy.context.scene.frame_current + 0.01  #

    if context.mode == 'OBJECT':
        objects = context.selected_objects
    else:
        if hasattr(context, 'objects_in_mode_unique_data'):
            objects = context.objects_in_mode_unique_data[:]
        else:
            objects = context.selected_objects  # 2.79

    mode = context.object.mode
    bpy.ops.object.mode_set(mode='OBJECT')

    for obj in [o for o in objects if o.type in {'MESH'}]:
        sk_data = obj.data.shape_keys  # 2.79 fix
        is_vertex = (not obj.active_shape_key and
                     not obj.active_shape_key_index and
                     not sk_data)

        data = obj.data
        selVerts = [False] * len(data.vertices)
        if obj.type == 'MESH':
            ###############
            # vertex mode #
            if is_vertex:
                # if kp_tool_anim.key_points:
                for v_i, vert in enumerate(data.vertices):
                    if allVerts or vert.select:
                        insert_key(vert, 'co', group="Vertex %s" % v_i)
                        selVerts[v_i] = True

                # set interpolation TODO move to function
                if (animProp_KP.key_keytype_in != 'NONE'):
                    anim = obj.data.animation_data
                    if anim is not None and anim.action is not None:
                        for fcu in anim.action.fcurves:
                            for v_i, kf in enumerate(fcu.keyframe_points):
                                if (selVerts[v_i] is True and kf.co[0] > frame_min and kf.co[0] < frame_max):
                                    kf.interpolation = animProp_KP.key_keytype_in
                                    kf.easing = animProp_KP.key_keytype_out
                            fcu.update()

            ##################
            # shape key mode (absolute)#
            elif not sk_data.use_relative:  # sk absolute
                sk_data.eval_time = (frame * 10)
                sk_data.keyframe_insert(data_path='eval_time')  # , frame=frame)

                # set interpolation TODO move to function
                if (animProp_KP.key_keytype_in != 'NONE'):
                    anim = obj.data.shape_keys.animation_data
                    if anim is not None and anim.action is not None:
                        for fcu in anim.action.fcurves:
                            for v_i, kf in enumerate(fcu.keyframe_points):
                                if (kf.co[0] > frame_min and kf.co[0] < frame_max):
                                    kf.interpolation = animProp_KP.key_keytype_in
                                    kf.easing = animProp_KP.key_keytype_out
                            fcu.update()

            ##################
            # shape key mode (multi)#
            else:
                if obj.active_shape_key_index > 0:  # TODO ok?
                    sk_name = obj.active_shape_key.name
                    for v_i, vert in enumerate(obj.active_shape_key.data):
                        if allVerts or data.vertices[v_i].select:
                            insert_key(vert, 'co', group="%s Vertex %s" % (sk_name, v_i))

    bpy.ops.object.mode_set(mode=mode)
    refresh_ui_keyframes()


# button insert key 'selected'
class ANIM_OT_insert_keyframe_animall_KP(Operator):
    bl_label = "Add"
    bl_idname = "anim.insert_keyframe_animall_kp"
    bl_description = "Insert Keys for selected vertex"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(op, context):
        insertKey_kp(context, False)

        return {'FINISHED'}


# button insert key 'all'
class ANIM_OT_insert_keyframe_animall_all_KP(Operator):
    bl_label = "Add"
    bl_idname = "anim.insert_keyframe_animall_all_kp"
    bl_description = "Insert Keys for all vertex"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(op, context):
        insertKey_kp(context, True)

        return {'FINISHED'}


def deleteKey_kp(context, allVerts=False):
    kp_tool_anim = context.window_manager.kp_tool_anim

    if context.mode == 'OBJECT':
        objects = context.selected_objects
    else:
        if hasattr(context, 'objects_in_mode_unique_data'):
            objects = context.objects_in_mode_unique_data[:]
        else:
            objects = context.selected_objects  # 2.79

    mode = context.object.mode
    bpy.ops.object.mode_set(mode='OBJECT')  # hypov8 add

    for obj in objects:
        data = obj.data
        sk_data = data.shape_keys  # 2.79 fix
        is_vertex = (not obj.active_shape_key and
                     not obj.active_shape_key_index and
                     not sk_data)

        if obj.type == 'MESH':
            # if kp_tool_anim.key_points:
            if is_vertex:
                for vert in data.vertices:
                    if allVerts or vert.select:
                        delete_key(vert, 'co')
            elif not sk_data.use_relative:  # sk absolute
                delete_key(sk_data, 'eval_time')
            else:
                for v_i, vert in enumerate(obj.active_shape_key.data):
                    if allVerts or data.vertices[v_i].select:
                        delete_key(vert, 'co')

    bpy.ops.object.mode_set(mode=mode)
    refresh_ui_keyframes()


class ANIM_OT_delete_keyframe_animall_KP(Operator):
    bl_label = "Delete"
    bl_idname = "anim.delete_keyframe_animall_kp"
    bl_description = "Delete Key for selected vertex"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(op, context):
        deleteKey_kp(context, False)

        return {'FINISHED'}


class ANIM_OT_delete_keyframe_animall_all_KP(Operator):
    bl_label = "Delete"
    bl_idname = "anim.delete_keyframe_animall_all_kp"
    bl_description = "Delete Key for all vertex"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(op, context):
        deleteKey_kp(context, True)

        return {'FINISHED'}


#  clear animation button
class ANIM_OT_clear_animation_animall_KP(Operator):
    bl_label = "Clear Animation"
    bl_idname = "anim.clear_animation_animall_kp"
    bl_description = ("Delete all keyframes for this object\n"
                      "If in a specific case it doesn't work\n"
                      "try to delete the keys manually")
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_confirm(self, event)

    def execute(self, context):
        if context.mode == 'OBJECT':
            objects = context.selected_objects
        else:
            if hasattr(context, 'objects_in_mode_unique_data'):
                objects = context.objects_in_mode_unique_data[:]
            else:
                objects = context.selected_objects  # 2.79

        for obj in objects:
            try:
                data = obj.data
                data.animation_data_clear()
            except print("ERROR: clear"):
                self.report({'WARNING'}, "Clear Animation could not be performed")
                return {'CANCELLED'}

        refresh_ui_keyframes()

        return {'FINISHED'}


classes = [
    AnimallProperties_KP,  # toolbar
    VIEW3D_PT_animall_KP,
    ANIM_OT_insert_keyframe_animall_KP,
    ANIM_OT_insert_keyframe_animall_all_KP,
    ANIM_OT_delete_keyframe_animall_KP,
    ANIM_OT_delete_keyframe_animall_all_KP,
    ANIM_OT_clear_animation_animall_KP,
    ANIM_OT_frame_prev_KP,
    ANIM_OT_frame_next_KP,
    ANIM_OT_frame_update_KP,
]


def register():
    for cls in classes:
        make_annotations(cls)  # v1.2.2
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.kp_tool_anim = PointerProperty(type=AnimallProperties_KP)


def unregister():
    # bpy.app.handlers.frame_change_post.remove(post_frame_change)
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.WindowManager.kp_tool_anim
    # del bpy.types.WindowManager.kp_tool_q3tokp
