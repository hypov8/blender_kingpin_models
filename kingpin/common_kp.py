'''
common_kp.py file

File limitations
blender compatability tools
'''

from ast import excepthandler
import bpy
from timeit import default_timer as timer


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
    (-0.688191, -0.587785, -0.425325)
)


def printProgress_fn(self, frame, total, prefix):
    # Display the progress status in console
    progressStatus = float(frame / total) * 100
    if total < 50 or (frame % 20) == 0:
        print("%-25s %6.2f%%\r" % (prefix + ":", progressStatus), end='')


def printDone_fn(self, prefix):
    # Display the progress status in console
    print("%-25s 100%% Done. (%.2f sec)" % (prefix + ":", timer() - self.time))


def get_preferences(context=None):
    ''' Multi version compatibility for getting preferences
    https://theduckcow.com/2019/update-addons-both-blender-28-and-27-support/#synved-sections-1-7
    '''
    if not context:
        context = bpy.context
    if hasattr(context, "user_preferences"):  # B2.7
        return context.user_preferences
    elif hasattr(context, "preferences"):   # B2.8
        return context.preferences
    else:
        raise Exception("Could not fetch user preferences")


def get_addon_preferences(context=None):
    ''' Multi version compatibility for getting preferences
    https://theduckcow.com/2019/update-addons-both-blender-28-and-27-support/#synved-sections-1-7
    '''
    if not context:
        context = bpy.context
    prefs = None
    if hasattr(context, "user_preferences"):  # B2.7
        prefs = context.user_preferences.addons.get(__package__, None)
    elif hasattr(context, "preferences"):
        prefs = context.preferences.addons.get(__package__, None)
    if prefs:
        return prefs.preferences
    else:
        raise Exception("Could not fetch user addon preferences")


# todo fix this
def get_collection(context):
    if hasattr(context, "collection"):
        return context.collection.objects  # B2.8
    else:
        return context.scene.groups


def get_contex_obj(context):
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


def get_hide(context):
    if hasattr(context, "hide_viewport"):
        return context.hide_viewport  # B2.8
    else:
        return context.hide


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


def set_uv_array(context, index, x, y):
    return context


def set_uv_data_active(context, obj):
    if hasattr(context, "uv_layers"):
        context.uv_layers.active = obj
    else:
        context.tessface_uv_textures.active = obj


def set_coll_group_link(b, name):
    if hasattr(b, "collection"):
        # return b.collection.objects  # B2.8
        return b.collection.children.link(name)
    else:
        return b.scene.groups


def update_matrices(obj):
    '''https://stackoverflow.com/a/57485640'''
    if obj.parent is None:
        obj.matrix_world = obj.matrix_basis
    else:  # TODO @
        obj.matrix_world = obj.parent.matrix_world * \
            obj.matrix_parent_inverse * \
            obj.matrix_basis


def make_annotations_old(cls):
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


#
#
def set_obj_group(object, new_group=None):
    """
    https://theduckcow.com/2019/update-addons-both-blender-28-and-27-support/#synved-sections-1-4

    """
    if not new_group:
        raise Exception("cant assign object to group")

    if hasattr(object, "layers"):  # B 2.7x
        for layer in bpy.data.scenes:
            # remove object from layer if present
            if object not in layer.objects[:]:
                continue
            else:
                layer.objects.unlink(object)
        new_group.objects.link(object)
    else:  # B2.8
        # remove object from sub-colection if present
        for layer in bpy.data.collections:
            if object in layer.objects[:]:
                layer.objects.unlink(object)
        # remove object from master collection if present
        '''for layer in bpy.data.scenes[0].collection:
            if object in layer.objects[:]:
                layer.objects.unlink(object)'''
        if object in bpy.context.scene.collection.objects[:]:
            bpy.context.scene.collection.objects.unlink(object)
        # assign object to collection
        new_group.objects.link(object)


'''
get mesh data at current frame

'''
import bmesh
IDX_IDC_V = 0   # indices (vert)
IDX_IDC_UV = 1  # indices (vert uv)
IDX_XYZ_V = 2   # xyz (pos vert)
IDX_XYZ_VN = 3  # xyz (pos vert normal)
IDX_XY_UV = 4   # XY (pos UV)
IDX_I_FACE = 5  # COUNT (face)
IDX_I_VERT = 6  # COUNT (vertex)
IDX_I_UV = 7    # COUNT (UV)


def getMeshArrays_fn(self, obj_group=[], frame=0, getUV=True, isPlayer=0):
    '''Return collapsed mesh data at current frame
    :parm self
    :type
    :obj_group = grouped objects

    :rtype: array
    :return: obj_array(
        : IDX_IDC_V = 0   # indices (vert)
        : IDX_IDC_UV = 1  # indices (vert uv)
        : IDX_XYZ_V = 2   # xyz (pos vert)
        : IDX_XYZ_VN = 3  # xyz (pos vert normal)
        : IDX_XY_UV = 4   # XY (pos UV)
        : IDX_I_FACE = 5  # COUNT (face)
        : IDX_I_VERT = 6  # COUNT (vertex)
        : IDX_I_UV = 7    # COUNT (UV)
    )
    '''

    # convert poly to tri
    def triangulateMesh_fn(self, object, depsgraph):
        me = None
        depMesh = None
        if bpy.app.version >= (2, 80):  # B2.8
            depMesh = object.evaluated_get(depsgraph)
            try:
                me = depMesh.to_mesh()
            except RuntimeError:
                depMesh.to_mesh_clear()
                return None
            # if not me.loop_triangles and me.polygons:
            #     me.calc_loop_triangles()
        else:  # B2.79
            try:
                me = object.to_mesh(
                    bpy.context.scene,
                    True,
                    calc_tessface=False,
                    settings='PREVIEW')  # 'RENDER' 'PREVIEW')
            except RuntimeError:
                return None  # return None
            # mesh.calc_tessface()

        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.triangulate(bm, faces=bm.faces)  # triaglulate
        bm.to_mesh(me)
        bm.free()

        me.transform(object.matrix_world)
        if object.matrix_world.determinant() < 0.0:
            me.flip_normals()
            print("Note: transform is negative, normals fliped")

        return me, depMesh
        # done getMeshArrays_fn()

    def fillMeshArrays(self, frame, me, faceuv, uv_texture, uv_layer):
        # Make our own list so it can be sorted to reduce context switching
        face_index_pairs = [(face, index) for index, face in enumerate(me.polygons)]
        me_verts = me.vertices[:]  # get vert array
        me.calc_normals_split()
        loops = me.loops

        # counters
        face_count = len(me.polygons)
        vert_count = len(me_verts)

        tmp_idc_vert = []  # * (face_count * 3)  # IDX_IDC_V = 0   # indices
        tmp_idc_uv = []  # * (face_count * 3)    # IDX_IDC_UV = 1  # indices
        tmp_XYZ_vert = []  # * vert_count        # IDX_XYZ_V = 2   # xyz
        tmp_XYZ_norm = []  # * vert_count        # IDX_XYZ_VN = 3  # xyz
        tmp_XY_uv = []                         # IDX_XY_UV = 4   # XY

        # mats. TODO not needed?
        ''' if faceuv: '''

        # Vert
        for i, v in enumerate(me_verts):
            tmp_XYZ_vert.append(v.co[:])   # XYZ float
            tmp_XYZ_norm.append(v.normal[:])  # XYZ float

        # UV
        uv_unique_count = 0  # IDX_I_UV
        if faceuv:
            uv = f_index = uv_index = uv_key = uv_val = uv_ls = None
            uv_face_mapping = [None] * len(face_index_pairs)
            uv_dict = {}
            uv_get = uv_dict.get
            for f, f_index in face_index_pairs:
                uv_ls = uv_face_mapping[f_index] = []
                for uv_index, l_index in enumerate(f.loop_indices):
                    uv = uv_layer[l_index].uv
                    uv_key = loops[l_index].vertex_index, (uv[0], uv[1])
                    uv_val = uv_get(uv_key)
                    if uv_val is None:
                        uv_val = uv_dict[uv_key] = uv_unique_count
                        tmp_XY_uv.append((uv[0], uv[1]))  # XY float
                        uv_unique_count += 1
                    uv_ls.append(uv_val)
            del uv_dict, uv, f_index, uv_index, uv_ls, uv_get, uv_key, uv_val
            # Only need uv_unique_count and uv_face_mapping

        # vertex indicies
        for f, f_index in face_index_pairs:
            f_v = [(vi, me_verts[v_idx], l_idx)
                   for vi, (v_idx, l_idx) in enumerate(zip(f.vertices, f.loop_indices))]

            for i, (vi, v, li) in enumerate(f_v):
                tmp_idc_vert.append(v.index)  # vert (indices)
                if faceuv:
                    tmp_idc_uv.append(uv_face_mapping[f_index][vi])  # uv (indices)

        # ###### end ###### #
        return (tmp_idc_vert,  # IDX_IDC_V = 0   # indices
                tmp_idc_uv,    # IDX_IDC_UV = 1  # indices
                tmp_XYZ_vert,  # IDX_XYZ_V = 2   # xyz
                tmp_XYZ_norm,  # IDX_XYZ_VN = 3  # xyz
                tmp_XY_uv,     # IDX_XY_UV = 4   # XY
                face_count,    # IDX_I_FACE = 5  # COUNT
                vert_count,    # IDX_I_VERT = 6  # COUNT
                uv_unique_count)  # IDX_I_UV = 7 #COUNT
    # done... fillMeshArrays()
    ##########################

    tmp_data = []

    if bpy.app.version >= (2, 80):  # B2.80
        depsgraph = bpy.context.evaluated_depsgraph_get()
        for obj in obj_group:
            obj = bpy.data.objects[obj.name].evaluated_get(depsgraph)
            me, depMesh = triangulateMesh_fn(self, obj, depsgraph)
            if me is None:
                continue
            faceuv = uv_layer = None
            if frame == 0 and getUV:
                faceuv = len(me.uv_layers) > 0
                if not faceuv:
                    me.uv_layers.new()  # add uv map
                    faceuv = True
                uv_layer = me.uv_layers.active.data[:]
            # mesh array
            tmp_data.append(
                fillMeshArrays(self, frame, me, faceuv, None, uv_layer))
            # clean up
            depMesh.to_mesh_clear()
    else:  # B2.79
        for obj in obj_group:
            me, depMesh = triangulateMesh_fn(self, obj, None)
            if me is None:
                continue
            faceuv = uv_texture = uv_layer = None
            if frame == 0 and getUV:
                faceuv = len(me.uv_textures) > 0
                if not faceuv:
                    me.uv_textures.new()  # add uv map
                    faceuv = True
                uv_texture = me.uv_textures.active.data[:]
                uv_layer = me.uv_layers.active.data[:]
            # mesh array
            tmp_data.append(
                fillMeshArrays(self, frame, me, faceuv, uv_texture, uv_layer,
                               get_UV=getUV))
            # clean up
            bpy.data.meshes.remove(me)
    # frame array
    '''if isPlayer:
        self.frameDataBBox.append(tmp_data)
    else:
        self.frameData.append(tmp_data)
    del tmp_data'''

    if not len(tmp_data):
        raise Exception("No mesh in array")

    return tmp_data
# end getMeshArrays_fn


# Utility functions
def refresh_ui_keyframes():
    '''use after a scrip update of annimation data'''
    try:
        for area in bpy.context.screen.areas:
            if area.type in ('TIMELINE', 'GRAPH_EDITOR', 'DOPESHEET_EDITOR'):
                area.tag_redraw()
    except print("ERROR: refresh_ui_keyframes"):
        pass
