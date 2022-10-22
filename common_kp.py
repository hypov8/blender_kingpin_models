'''
common_kp.py file

File limitations
'''

import bpy

MD2_MAX_TRIANGLES = 4096
MD2_MAX_VERTS = 2048
MD2_MAX_FRAMES = 1024  # 512 - 1024 is an UFO:AI extension.
MD2_MAX_SKINS = 32
MD2_MAX_SKINNAME = 63
MD2_VN = (
    (-0.525731, 0.000000, 0.850651),
    (-0.442863, 0.238856, 0.864188),
    (-0.295242, 0.000000, 0.955423),
    (-0.309017, 0.500000, 0.809017),
    (-0.162460, 0.262866, 0.951056),
    (0.000000, 0.000000, 1.000000),
    (0.000000, 0.850651, 0.525731),
    (-0.147621, 0.716567, 0.681718),
    (0.147621, 0.716567, 0.681718),
    (0.000000, 0.525731, 0.850651),
    (0.309017, 0.500000, 0.809017),
    (0.525731, 0.000000, 0.850651),
    (0.295242, 0.000000, 0.955423),
    (0.442863, 0.238856, 0.864188),
    (0.162460, 0.262866, 0.951056),
    (-0.681718, 0.147621, 0.716567),
    (-0.809017, 0.309017, 0.500000),
    (-0.587785, 0.425325, 0.688191),
    (-0.850651, 0.525731, 0.000000),
    (-0.864188, 0.442863, 0.238856),
    (-0.716567, 0.681718, 0.147621),
    (-0.688191, 0.587785, 0.425325),
    (-0.500000, 0.809017, 0.309017),
    (-0.238856, 0.864188, 0.442863),
    (-0.425325, 0.688191, 0.587785),
    (-0.716567, 0.681718, -0.147621),
    (-0.500000, 0.809017, -0.309017),
    (-0.525731, 0.850651, 0.000000),
    (0.000000, 0.850651, -0.525731),
    (-0.238856, 0.864188, -0.442863),
    (0.000000, 0.955423, -0.295242),
    (-0.262866, 0.951056, -0.162460),
    (0.000000, 1.000000, 0.000000),
    (0.000000, 0.955423, 0.295242),
    (-0.262866, 0.951056, 0.162460),
    (0.238856, 0.864188, 0.442863),
    (0.262866, 0.951056, 0.162460),
    (0.500000, 0.809017, 0.309017),
    (0.238856, 0.864188, -0.442863),
    (0.262866, 0.951056, -0.162460),
    (0.500000, 0.809017, -0.309017),
    (0.850651, 0.525731, 0.000000),
    (0.716567, 0.681718, 0.147621),
    (0.716567, 0.681718, -0.147621),
    (0.525731, 0.850651, 0.000000),
    (0.425325, 0.688191, 0.587785),
    (0.864188, 0.442863, 0.238856),
    (0.688191, 0.587785, 0.425325),
    (0.809017, 0.309017, 0.500000),
    (0.681718, 0.147621, 0.716567),
    (0.587785, 0.425325, 0.688191),
    (0.955423, 0.295242, 0.000000),
    (1.000000, 0.000000, 0.000000),
    (0.951056, 0.162460, 0.262866),
    (0.850651, -0.525731, 0.000000),
    (0.955423, -0.295242, 0.000000),
    (0.864188, -0.442863, 0.238856),
    (0.951056, -0.162460, 0.262866),
    (0.809017, -0.309017, 0.500000),
    (0.681718, -0.147621, 0.716567),
    (0.850651, 0.000000, 0.525731),
    (0.864188, 0.442863, -0.238856),
    (0.809017, 0.309017, -0.500000),
    (0.951056, 0.162460, -0.262866),
    (0.525731, 0.000000, -0.850651),
    (0.681718, 0.147621, -0.716567),
    (0.681718, -0.147621, -0.716567),
    (0.850651, 0.000000, -0.525731),
    (0.809017, -0.309017, -0.500000),
    (0.864188, -0.442863, -0.238856),
    (0.951056, -0.162460, -0.262866),
    (0.147621, 0.716567, -0.681718),
    (0.309017, 0.500000, -0.809017),
    (0.425325, 0.688191, -0.587785),
    (0.442863, 0.238856, -0.864188),
    (0.587785, 0.425325, -0.688191),
    (0.688191, 0.587785, -0.425325),
    (-0.147621, 0.716567, -0.681718),
    (-0.309017, 0.500000, -0.809017),
    (0.000000, 0.525731, -0.850651),
    (-0.525731, 0.000000, -0.850651),
    (-0.442863, 0.238856, -0.864188),
    (-0.295242, 0.000000, -0.955423),
    (-0.162460, 0.262866, -0.951056),
    (0.000000, 0.000000, -1.000000),
    (0.295242, 0.000000, -0.955423),
    (0.162460, 0.262866, -0.951056),
    (-0.442863, -0.238856, -0.864188),
    (-0.309017, -0.500000, -0.809017),
    (-0.162460, -0.262866, -0.951056),
    (0.000000, -0.850651, -0.525731),
    (-0.147621, -0.716567, -0.681718),
    (0.147621, -0.716567, -0.681718),
    (0.000000, -0.525731, -0.850651),
    (0.309017, -0.500000, -0.809017),
    (0.442863, -0.238856, -0.864188),
    (0.162460, -0.262866, -0.951056),
    (0.238856, -0.864188, -0.442863),
    (0.500000, -0.809017, -0.309017),
    (0.425325, -0.688191, -0.587785),
    (0.716567, -0.681718, -0.147621),
    (0.688191, -0.587785, -0.425325),
    (0.587785, -0.425325, -0.688191),
    (0.000000, -0.955423, -0.295242),
    (0.000000, -1.000000, 0.000000),
    (0.262866, -0.951056, -0.162460),
    (0.000000, -0.850651, 0.525731),
    (0.000000, -0.955423, 0.295242),
    (0.238856, -0.864188, 0.442863),
    (0.262866, -0.951056, 0.162460),
    (0.500000, -0.809017, 0.309017),
    (0.716567, -0.681718, 0.147621),
    (0.525731, -0.850651, 0.000000),
    (-0.238856, -0.864188, -0.442863),
    (-0.500000, -0.809017, -0.309017),
    (-0.262866, -0.951056, -0.162460),
    (-0.850651, -0.525731, 0.000000),
    (-0.716567, -0.681718, -0.147621),
    (-0.716567, -0.681718, 0.147621),
    (-0.525731, -0.850651, 0.000000),
    (-0.500000, -0.809017, 0.309017),
    (-0.238856, -0.864188, 0.442863),
    (-0.262866, -0.951056, 0.162460),
    (-0.864188, -0.442863, 0.238856),
    (-0.809017, -0.309017, 0.500000),
    (-0.688191, -0.587785, 0.425325),
    (-0.681718, -0.147621, 0.716567),
    (-0.442863, -0.238856, 0.864188),
    (-0.587785, -0.425325, 0.688191),
    (-0.309017, -0.500000, 0.809017),
    (-0.147621, -0.716567, 0.681718),
    (-0.425325, -0.688191, 0.587785),
    (-0.162460, -0.262866, 0.951056),
    (0.442863, -0.238856, 0.864188),
    (0.162460, -0.262866, 0.951056),
    (0.309017, -0.500000, 0.809017),
    (0.147621, -0.716567, 0.681718),
    (0.000000, -0.525731, 0.850651),
    (0.425325, -0.688191, 0.587785),
    (0.587785, -0.425325, 0.688191),
    (0.688191, -0.587785, 0.425325),
    (-0.955423, 0.295242, 0.000000),
    (-0.951056, 0.162460, 0.262866),
    (-1.000000, 0.000000, 0.000000),
    (-0.850651, 0.000000, 0.525731),
    (-0.955423, -0.295242, 0.000000),
    (-0.951056, -0.162460, 0.262866),
    (-0.864188, 0.442863, -0.238856),
    (-0.951056, 0.162460, -0.262866),
    (-0.809017, 0.309017, -0.500000),
    (-0.864188, -0.442863, -0.238856),
    (-0.951056, -0.162460, -0.262866),
    (-0.809017, -0.309017, -0.500000),
    (-0.681718, 0.147621, -0.716567),
    (-0.681718, -0.147621, -0.716567),
    (-0.850651, 0.000000, -0.525731),
    (-0.688191, 0.587785, -0.425325),
    (-0.587785, 0.425325, -0.688191),
    (-0.425325, 0.688191, -0.587785),
    (-0.425325, -0.688191, -0.587785),
    (-0.587785, -0.425325, -0.688191),
    (-0.688191, -0.587785, -0.425325))


def get_preferences(context=None):
    ''' Multi version compatibility for getting preferences
    https://theduckcow.com/2019/update-addons-both-blender-28-and-27-support/#synved-sections-1-7
    '''
    if not context:
        context = bpy.context
    prefs = None
    if hasattr(context, "user_preferences"):
        prefs = context.user_preferences.addons.get(__package__, None)
    elif hasattr(context, "preferences"):
        prefs = context.preferences.addons.get(__package__, None)
    if prefs:
        return prefs.preferences
    else:
        raise Exception("Could not fetch user preferences")


def get_collection(context):
    if hasattr(context, "collection"):
        return context.collection.objects  # B2.8
    else:
        return context.scene.objects


def get_objects(context):
    if hasattr(context, "view_layer"):
        return context.view_layer.objects  # B2.8
    else:
        return context.scene.objects


def get_layers(context):
    if hasattr(context, "view_layer"):
        return context.view_layer  # B2.8
    else:
        return context.scene


def get_menu_import():
    if hasattr(bpy.types, "TOPBAR_MT_file_import"):
        return bpy.types.TOPBAR_MT_file_import
    elif hasattr(bpy.types, "INFO_MT_file_import"):
        return bpy.types.INFO_MT_file_import
    else:
        raise Exception("Could not fetch menu")


def get_menu_export():
    if hasattr(bpy.types, "TOPBAR_MT_file_export"):
        return bpy.types.TOPBAR_MT_file_export
    elif hasattr(bpy.types, "INFO_MT_file_export"):
        return bpy.types.INFO_MT_file_export
    else:
        raise Exception("Could not fetch menu")


def get_groups():
    if hasattr(bpy.data, "collections"):
        mygroup = bpy.data.collections.get("MyGroup")
    else:
        mygroup = bpy.data.groups.get("MyGroup")


def get_uv_data_new(context, uv_name=""):
    ret = (0, None)
    if hasattr(context, "uv_textures"):
        # print("found uv_textures")
        ret = (1, context.uv_textures.new(name=uv_name))  # tessface_uv_textures
        context.uv_textures.active = ret[1]
    else:
        # print("found uv_layers")  # B2.8
        ret = (2, context.uv_layers.new(name=uv_name))
        context.uv_layers.active = ret[1]
    return ret


def get_uv_data(context):
    ret = (0, None)
    if hasattr(context, "uv_textures"):
        return context.uv_textures
    else:
        return context.uv_layers  # B2.8


def set_select_state(context, opt):
    """Multi version compatibility for setting object selection
    https://theduckcow.com/2019/update-addons-both-blender-28-and-27-support/#synved-sections-1-11
    """
    if hasattr(context, "select_set"):
        context.select_set(state=opt)  # B2.8
    else:
        context.select = opt


def set_mode_state(context, opt):
    """Multi version compatibility for setting object selection
    https://theduckcow.com/2019/update-addons-both-blender-28-and-27-support/#synved-sections-1-11
    """
    if hasattr(context, "mode_set"):
        context.mode_set(state=opt)  # B2.8
    else:
        context.mode = opt


'''
def set_uv_data(context, index, x, y):
    if hasattr(context.data[index], "uv"):
        # print("uv_1")
        context.data[index].uv = (x, y)
    else:
        # print("uv_2")
        context.data[index].uv = (x, y)
        # context[index].uv = (x, y)'''


def set_uv_array(context, index, x, y):
    return context


def set_uv_data_active(context, obj):
    if hasattr(context, "uv_layers"):
        context.uv_layers.active = obj
    else:
        context.tessface_uv_textures.active = obj


def make_annotations1(cls):
    ''' Converts class fields to annotations if running with Blender 2.8
    https://theduckcow.com/2019/update-addons-both-blender-28-and-27-support/#synved-sections-1-1
    '''
    if bpy.app.version < (2, 80):
        print("skip")
        return cls
    bl_props = {k: v for k, v in cls.__dict__.items() if isinstance(v, tuple)}
    if bl_props:
        if '__annotations__' not in cls.__dict__:
            setattr(cls, '__annotations__', {})
        annotations = cls.__dict__['__annotations__']
        for k, v in bl_props.items():
            annotations[k] = v
            delattr(cls, k)
    print("found")
    return cls


def make_annotations(cls):
    """Add annotation attribute to fields to avoid Blender 2.8+ warnings
    https://github.com/OpenNaja/cobra-tools/blob/master/addon_updater_ops.py"""
    if not hasattr(bpy.app, "version") or bpy.app.version < (2, 80):
        return cls
    if bpy.app.version < (2, 93, 0):
        bl_props = {k: v for k, v in cls.__dict__.items()
                    if isinstance(v, tuple)}
    else:
        bl_props = {k: v for k, v in cls.__dict__.items()
                    if isinstance(v, bpy.props._PropertyDeferred)}
    if bl_props:
        if '__annotations__' not in cls.__dict__:
            setattr(cls, '__annotations__', {})
        annotations = cls.__dict__['__annotations__']
        for k, v in bl_props.items():
            annotations[k] = v
            delattr(cls, k)
    return cls


def get_user_preferences(context=None):
    """Intermediate method for pre and post blender 2.8 grabbing preferences
    https://github.com/OpenNaja/cobra-tools/blob/master/addon_updater_ops.py"""
    if not context:
        context = bpy.context
    prefs = None
    if hasattr(context, "user_preferences"):
        prefs = context.user_preferences.addons.get(__package__, None)
    elif hasattr(context, "preferences"):
        prefs = context.preferences.addons.get(__package__, None)
    if prefs:
        return prefs.preferences
    # To make the addon stable and non-exception prone, return None
    # raise Exception("Could not fetch user preferences")
    return None
