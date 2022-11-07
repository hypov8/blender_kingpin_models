'''
exporter class/func

'''
import time  # debug
from timeit import default_timer as timer

import math
import os
import struct
import bmesh
# import shutil

if "bpy" in locals():
    import importlib
    importlib.reload(common_kp)
else:
    from . import common_kp

import bpy
from bpy_extras.io_utils import ExportHelper
# from math import pi
from mathutils import Matrix, Euler


from .common_kp import (
    MD2_MAX_TRIANGLES,
    MD2_MAX_VERTS,
    MD2_MAX_FRAMES,
    MD2_MAX_SKINS,
    MD2_MAX_SKINNAME,
    MD2_VN,
)


IDX_IDC_V = 0   # indices
IDX_IDC_UV = 1  # indices
IDX_XYZ_V = 2   # xyz
IDX_XYZ_VN = 3  # xyz
IDX_XY_UV = 4   # XY
IDX_I_FACE = 5   # COUNT
IDX_I_VERT = 6   # COUNT
IDX_I_UV = 7   # COUNT


def getMeshArrays_fn(self, obj_group, frame, getUV, isPlayer=0):
    def isDepsObj_aMatch(export_obj, sceene_obj):
        ''' does object exist in Dependency graph'''
        for obj in export_obj:
            if obj.name == sceene_obj.name:
                return True
        return False

    # convert poly to tri
    def triangulateMesh_fn(self, object, depsgraph):
        me = None
        depMesh = None
        if bpy.app.version >= (2, 80):  # B2.8
            depMesh = object.evaluated_get(depsgraph)
            try:
                if self.fApply_modifiers:
                    me = depMesh.to_mesh()
                else:
                    me = depMesh.original.to_mesh()
            except RuntimeError:
                depMesh.to_mesh_clear()
                return None
            # if not me.loop_triangles and me.polygons:
            #     me.calc_loop_triangles()
        else:  # B2.79
            try:
                me = object.to_mesh(
                    bpy.context.scene,
                    self.fApply_modifiers,
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
        def roundVec(v):
            # return float(v[0]), float(v[1]), float(v[2])
            return round(v[0], 6), round(v[1], 6), round(v[2], 6)

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
    isBlen_28x = False
    if bpy.app.version >= (2, 80):  # B2.80
        isBlen_28x = True
        depsgraph = bpy.context.evaluated_depsgraph_get()  # B2.8
        for object_instance in depsgraph.object_instances:
            obj = object_instance.object
            if isDepsObj_aMatch(obj_group, obj):  # find matching objects
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
                fillMeshArrays(self, frame, me, faceuv, uv_texture, uv_layer))
            # clean up
            bpy.data.meshes.remove(me)
    # frame array
    if isPlayer:
        self.frameDataBBox.append(tmp_data)
    else:
        self.frameData.append(tmp_data)
    del tmp_data
# end getMeshArrays_fn


def printProgress_fn(self, frame, prefix):
    # Display the progress status in console
    progressStatus = float(frame / self.numFrames) * 100
    if self.numFrames < 50 or (frame % 20) == 0:
        print("%-25s: %6.2f%%\r" % (prefix, progressStatus), end='')


def printDone_fn(self, prefix):
    # Display the progress status in console
    print("%-25s 100%% Done. (%.2f sec)" % (prefix + ":", timer() - self.time))


def setupInternalArrays_fn(self, context):
    '''get selected mesh data and store
       also store all viewable mesh for player models
    '''
    self.time = timer()  # reset timmer
    obj_sel = self.objects
    obj_vis = self.objectsVis
    scene = bpy.context.scene
    prefix = "Getting mesh data "
    for frame in range(self.numFrames):
        printProgress_fn(self, frame, prefix)  # print progress
        # --------------------------------------------
        # TODO find why this is taking lots of time...
        # 5 seconds with no items to seek 700 frames
        frameIdx = self.fStartFrame + frame
        scene.frame_set(frameIdx)
        # --------------------------------------------

        getUV = 1 if (frame == 0) else 0  # ignore uv for animated frames

        getMeshArrays_fn(self, obj_sel, frame, getUV, isPlayer=0)
        if self.fIsPlayerModel or self.fUseSharedBoundingBox:  # option
            getMeshArrays_fn(self, obj_vis, frame, 0, isPlayer=1)

    printDone_fn(self, prefix)  # Done.
# end setupInternalArrays_fn


def write_frame_fn(self, file, frame, frameName="frame"):
    ''' build frame data '''
    if not self.fUseSharedBoundingBox or self.fIsPlayerModel:  # .options
        min = self.bbox_min[frame]
        max = self.bbox_max[frame]
    else:
        min = self.bbox_min[0]
        max = self.bbox_max[0]

    # BL: some caching to speed it up:
    # -> sd_ gets the vertices between [0 and 255]
    #    which is our important quantization.
    sdx = (max[0] - min[0]) / 255.0
    sdy = (max[1] - min[1]) / 255.0
    sdz = (max[2] - min[2]) / 255.0
    isdx = float(255.0 / (max[0] - min[0])) if (max[2] - min[2]) != 0.0 else 0.0
    isdy = float(255.0 / (max[1] - min[1])) if (max[2] - min[2]) != 0.0 else 0.0
    isdz = float(255.0 / (max[2] - min[2])) if (max[2] - min[2]) != 0.0 else 0.0

    # note about the scale: self.object.scale is already applied via matrix_world
    data = struct.pack(
        "<6f16s",
        sdx, sdy, sdz,  # write scale of the model
        min[0], min[1], min[2],  # write offset (= min of bounding box)
        bytes(frameName[0:15], encoding="utf8"))  # write frame name.
    file.write(data)  # frame header

    ###########################
    # write vertex X,Y,Z,Normal
    ofsetVertID = 0  # multi object
    for mIdx, tmp_mesh in enumerate(self.frameData[frame]):
        for vIdx, vert in enumerate(tmp_mesh[IDX_XYZ_V]):
            # find the closest normal for every vertex
            bestNormalIndex = self.vNormData[frame][mIdx][vIdx]
            # write vertex pos and normal. (compressed position. 256 bytes)
            data = struct.pack(
                '<4B',
                int(((float(vert[0]) - min[0]) * isdx) + 0.5),
                int(((float(vert[1]) - min[1]) * isdy) + 0.5),
                int(((float(vert[2]) - min[2]) * isdz) + 0.5),
                bestNormalIndex)
            file.write(data)  # write vertex and normal
        ofsetVertID += len(tmp_mesh[IDX_XYZ_V])
# end write_frame_fn


def buildGLcommands_fn(self):
    ''' build gl commands '''
    self.time = timer()  # reset timmer
    prefix = "Building GLCommands"
    printProgress_fn(self, 0, prefix)  # print progress

    def findStripLength_fn(usedFace, mesh, startTri, startVert, numFaces,
                           cmdTris, cmdVerts, cmdUV):
        ''' triangle strips '''
        face_data = mesh[IDX_IDC_V]
        uv_data = mesh[IDX_IDC_UV]  # get_uv_data(mesh)
        usedFace[startTri] = 2  # make tri as currently testing

        # copy edge
        m1 = face_data[startTri * 3 + ((startVert + 2) % 3)]
        m2 = face_data[startTri * 3 + ((startVert + 1) % 3)]
        u1 = uv_data[startTri * 3 + ((startVert + 2) % 3)]
        u2 = uv_data[startTri * 3 + ((startVert + 1) % 3)]

        # store first tri
        cmdVerts.append(face_data[startTri * 3 + ((startVert + 0) % 3)])  # vIdc
        cmdVerts.append(m1)
        cmdVerts.append(m2)
        cmdUV.append(uv_data[startTri * 3 + ((startVert + 0) % 3)])
        cmdUV.append(u1)
        cmdUV.append(u2)

        cmdTris.append(startTri)

        cmdLength = 1  # stripCount
        for triIdx in range(startTri + 1, numFaces):
            if(usedFace[triIdx] == 0):
                for k in range(3):
                    # find 2 vertex that share vertex/UV data
                    if((m1 == face_data[triIdx * 3 + k]) and  # compare vertex indices
                       (m2 == face_data[triIdx * 3 + ((k + 1) % 3)]) and
                       (u1 == uv_data[triIdx * 3 + k]) and  # compare texture indices
                       (u2 == uv_data[triIdx * 3 + ((k + 1) % 3)])):

                        # move to next vertex loop
                        if(cmdLength % 2 == 1):  # flip?
                            m1 = face_data[triIdx * 3 + ((k + 2) % 3)]
                            u1 = uv_data[triIdx * 3 + ((k + 2) % 3)]
                        else:
                            m2 = face_data[triIdx * 3 + ((k + 2) % 3)]
                            u2 = uv_data[triIdx * 3 + ((k + 2) % 3)]

                        cmdVerts.append(face_data[triIdx * 3 + ((k + 2) % 3)])  # vIdx

                        cmdUV.append(uv_data[triIdx * 3 + ((k + 2) % 3)])
                        cmdLength += 1
                        cmdTris.append(triIdx)

                        usedFace[triIdx] = 2
                        triIdx = startTri + 1  # restart looking?

        # clear used counter
        for usedCounter in range(numFaces):
            if usedFace[usedCounter] == 2:
                usedFace[usedCounter] = 0

        return cmdLength
    #  end findStripLength_fn

    def findFanLength_fn(usedFace, mesh, startTri, startVert, numFaces,
                         cmdTris, cmdVerts, cmdUV):
        ''' triangle strips '''
        face_data = mesh[IDX_IDC_V]
        uv_data = mesh[IDX_IDC_UV]
        usedFace[startTri] = 2

        # copy edge
        m2 = face_data[startTri * 3 + ((startVert + 0) % 3)]
        m1 = face_data[startTri * 3 + ((startVert + 1) % 3)]
        u2 = uv_data[startTri * 3 + ((startVert + 0) % 3)]
        u1 = uv_data[startTri * 3 + ((startVert + 1) % 3)]

        # store first tri
        cmdVerts.append(m2)
        cmdVerts.append(face_data[startTri * 3 + ((startVert + 2) % 3)])
        cmdVerts.append(m1)
        cmdUV.append(u2)
        cmdUV.append(uv_data[startTri * 3 + ((startVert + 2) % 3)])
        cmdUV.append(u1)

        cmdLength = 1  # fanCount
        cmdTris.append(startTri)

        for triIdx in range(startTri + 1, numFaces):
            if(usedFace[triIdx] == 0):
                for k in range(3):
                    # find 2 vertex that share vertex/UV data
                    if((m1 == face_data[triIdx * 3 + k]) and  # compare vertex...
                       (m2 == face_data[triIdx * 3 + ((k + 1) % 3)]) and
                       (u1 == uv_data[triIdx * 3 + k]) and  # compare texture indices
                       (u2 == uv_data[triIdx * 3 + ((k + 1) % 3)])):

                        # move to next vertex loop
                        m1 = face_data[triIdx * 3 + ((k + 2) % 3)]
                        u1 = uv_data[triIdx * 3 + ((k + 2) % 3)]

                        cmdVerts.append(face_data[triIdx * 3 + ((k + 2) % 3)])
                        cmdUV.append(uv_data[triIdx * 3 + ((k + 2) % 3)])
                        cmdLength += 1
                        cmdTris.append(triIdx)

                        usedFace[triIdx] = 2
                        triIdx = startTri + 1  # restart looking
                        # hypo TODO: check this. go back n test all tri again?

        # clear used counter
        for usedCounter in range(numFaces):
            if usedFace[usedCounter] == 2:
                usedFace[usedCounter] = 0

        return cmdLength
    # end findFanLength_fn

    cmdTris = []
    cmdVerts = []
    cmdUV = []
    bestVerts = []
    bestTris = []
    bestUV = []
    mdxID = 0  # mdx hitbox index number
    ofsetVertID = 0   # multi object offset
    numCommands = 1  # add 1 for final NULL at end
    # loop through selected mesh
    for tmp_mesh in self.frameData[0]:
        numFaces = tmp_mesh[IDX_I_FACE]
        usedFace = [0] * numFaces  # has face been used. array
        for triIdx in range(numFaces):
            if not usedFace[triIdx]:
                # intialization
                bestLength = 0
                bestType = 0
                bestVerts = []
                bestTris = []
                bestUV = []

                for startVert in range(3):
                    cmdVerts = []
                    cmdTris = []
                    cmdUV = []
                    cmdLength = findFanLength_fn(
                        usedFace, tmp_mesh, triIdx, startVert, numFaces,
                        cmdTris, cmdVerts, cmdUV)
                    if (cmdLength > bestLength):
                        bestType = 1
                        bestLength = cmdLength
                        bestVerts = cmdVerts
                        bestTris = cmdTris
                        bestUV = cmdUV

                    cmdVerts = []
                    cmdTris = []
                    cmdUV = []
                    cmdLength = findStripLength_fn(
                        usedFace, tmp_mesh, triIdx, startVert, numFaces,
                        cmdTris, cmdVerts, cmdUV)
                    if (cmdLength > bestLength):
                        bestType = 0
                        bestLength = cmdLength
                        bestVerts = cmdVerts
                        bestTris = cmdTris
                        bestUV = cmdUV

                # mark tringle as used
                for usedCounter in range(bestLength):
                    usedFace[bestTris[usedCounter]] = 1

                cmd = []
                if bestType == 0:   # strip
                    num = bestLength + 2
                else:               # fan
                    num = (-(bestLength + 2))

                numCommands += 1
                if self.isMdx:  # mdx
                    numCommands += 1  # sub-object number

                uv_layer = tmp_mesh[IDX_XY_UV]  # uv_cords
                for cmdCounter in range(bestLength + 2):
                    cmd.append((0.0 + uv_layer[bestUV[cmdCounter]][0],  # X uv cords
                                1.0 - uv_layer[bestUV[cmdCounter]][1],  # Y uv cords
                                bestVerts[cmdCounter] + ofsetVertID))   # vertex number
                    numCommands += 3

                self.glCmdList.append((
                    num,   # fan/strip count
                    mdxID,  # object number
                    cmd))   # S, T, vIdx

        #  multi part object offset
        ofsetVertID += len(tmp_mesh[IDX_XYZ_V])
        mdxID += 1 if self.fSeparateHitbox else 0
        del usedFace

    printDone_fn(self, prefix)  # Done.
    # print("GLCommands. (Count: {})".format(numCommands))
    del cmdVerts, cmdUV, cmdTris, bestVerts, bestUV, bestTris
    return numCommands


def getSkins_fn(self, objects, method):
    '''TODO change this
    SKIN_MAT_NAME = get materal names, then check for valid images for size
    SKIN_TEX_NAME = get texture names, then check for valid image for size
    SKIN_TEX_PATH = use texture image path and size.
    TODO: UV image?
    '''
    def check_skip_material(mat):
        """Simple helper to check whether we actually support exporting that material or not"""
        return mat.type not in {'SURFACE'} or mat.use_nodes

    def stripLeadingPath(path):
        tmpPath = bpy.path.abspath(path)  # , library=n.image.library)
        tmpPath = os.path.normpath(tmpPath)
        tmpPath = tmpPath.replace('\\', '/')
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
            if texname not in skins and len(skins) <= MD2_MAX_SKINS:
                skins.append(texname)

    def updateWH(size, found, outW, outH):
        if size[0] > 0 and size[1] > 0:
            width = size[0]
            height = size[1]
            if not found:
                outW = height
                outH = width
                found = True
            else:
                if width > outW:
                    outW = width
                if height > outH:
                    outH = height
        return outW, outH, found

    self.time = timer()  # reset timmer
    prefix = "Getting Skins"
    printProgress_fn(self, 0, prefix)  # print progress
    skins = []
    width = height = 256
    foundWH = False  # find largest image

    triCount = 0
    for obj in self.objects:
        materials = obj.data.materials[:]
        # material_names = [m.name if m else None for m in materials]
        for m_idx, mat in enumerate(materials):
            if not mat:
                continue
            texname = mat.name
            if method == 'SKIN_MAT_NAME':
                appendSkins(skins, texname)

            # use nodes
            if mat.use_nodes:
                # search node images for dimensions/name
                for n in mat.node_tree.nodes:
                    if n and n.type == 'TEX_IMAGE' and n.image:
                        image = n.image
                        width, height, foundWH = updateWH(
                            image.size, foundWH, width, height)  # set image size
                        # set skin
                        if method == "SKIN_TEX_NAME":
                            texname = image.name
                            appendSkins(skins, texname)
                        elif method == "SKIN_TEX_PATH":
                            texname = stripLeadingPath(image.filepath)
                            appendSkins(skins, texname)
                        # elif method == 'SKIN_MAT_NAME':
            # B2.7 use 'texture'
            elif hasattr(mat, "texture_slots"):
                # search texture slots for dimensions/name
                for mtex in mat.texture_slots:
                    if mtex and mtex.texture.type == 'IMAGE' and mtex.texture.image:
                        image = mtex.texture.image
                        if mtex.use_map_color_diffuse:
                            width, height, foundWH = updateWH(
                                image.size, foundWH, width, height)  # set image size
                            # set skin
                            if method == "SKIN_TEX_NAME":
                                appendSkins(skins, image.name)
                            elif method == "SKIN_TEX_PATH":
                                texname = stripLeadingPath(image.filepath)
                                appendSkins(skins, texname)
                            # elif method == 'SKIN_MAT_NAME':
            '''else:  # TODO no nodes? use uv name?
                # use uv name/texture?'''

    printDone_fn(self, prefix)  # Done.
    print("Count:  {}\n".format(len(skins)) +
          "Width:  {}\n".format(width) +
          "Height: {}".format(height))
    for idx, skin in enumerate(skins):
        print("skin{}:  {}".format(idx + 1, skin[0:MD2_MAX_SKINNAME]))
    if height > 480 or width > 480:
        print("WARNING: found texture larger than kingpin max 480px")
    print("===============")

    if width < 8:
        width = 64
    if height < 8:
        height = 64

    self.skinWidth = width
    self.skinHeight = height
    self.skins = skins


def buildFrameNames_fn(self):
    '''
    sort the markers. The marker with the frame number closest to 0 will be the first marker in the list.
    The marker with the biggest frame number will be the last marker in the list'''
    name = []
    timeLineMarkers = []
    for marker in bpy.context.scene.timeline_markers:
        timeLineMarkers.append(marker)

    timeLineMarkers.sort(key=lambda marker: marker.frame)
    markerIdx = 0
    # delete markers at same frame positions
    if len(timeLineMarkers) > 1:
        markerFrame = timeLineMarkers[len(timeLineMarkers) - 1].frame
        for i in range(len(timeLineMarkers) - 2, -1, -1):
            if timeLineMarkers[i].frame == markerFrame:
                del timeLineMarkers[i]
            else:
                markerFrame = timeLineMarkers[i].frame
    for frame in range(self.numFrames):
        frameIdx = frame - self.fStartFrame + 1
        # build frame names
        if len(timeLineMarkers) != 0:
            fNameIdx = 1
            if markerIdx + 1 != len(timeLineMarkers):
                if frame >= timeLineMarkers[markerIdx + 1].frame:
                    markerIdx += 1
                    fNameIdx = 1
                else:
                    fNameIdx += 1
            name.append(timeLineMarkers[markerIdx].name + ('%02d' % fNameIdx))
        else:
            name.append("frame_" + str(frameIdx))
    return name


def calcSharedBBox_fn(self):
    ''' option to make bbox size across all frames the same
        this fixes vertex wobble in parts of mesh that dont move
    '''
    self.bbox_min = []
    self.bbox_max = []  # clear bbox
    min = [9999.0, 9999.0, 9999.0]
    max = [-9999.0, -9999.0, -9999.0]

    for frame in range(self.numFrames):
        if not self.fUseSharedBoundingBox:  # .options
            # reset bounding box
            min = [9999.0, 9999.0, 9999.0]
            max = [-9999.0, -9999.0, -9999.0]
        meshes = self.frameDataBBox[frame] if self.fIsPlayerModel else self.frameData[frame]
        for tmp_mesh in meshes:
            for vert in tmp_mesh[IDX_XYZ_V]:
                for i in range(3):
                    if vert[i] < min[i]:
                        min[i] = vert[i]
                    if vert[i] > max[i]:
                        max[i] = vert[i]

        # add new bbox for each frame
        if not self.fUseSharedBoundingBox or self.fIsPlayerModel:  # .options
            self.bbox_min.append(min)
            self.bbox_max.append(max)

    # store only 1 bbox
    if self.fUseSharedBoundingBox:  # .options
        self.bbox_min.append(min)
        self.bbox_max.append(max)


def calculateHitBox_fn(self):
    ''' mdx hitbox '''
    # if self.isMdx:
    for frame in range(self.numFrames):
        hitboxTmp = []
        hitboxMin = [9999, 9999, 9999]
        hitboxMax = [-9999, -9999, -9999]
        for tmp_mesh in self.frameData[frame]:
            if self.fSeparateHitbox:  # option: seperate hitbox for players
                hitboxMin = [9999, 9999, 9999]
                hitboxMax = [-9999, -9999, -9999]

            for vert in tmp_mesh[IDX_XYZ_V]:
                for i in range(3):
                    if vert[i] < hitboxMin[i]:
                        hitboxMin[i] = vert[i]
                    if vert[i] > hitboxMax[i]:
                        hitboxMax[i] = vert[i]

            if self.fSeparateHitbox:
                hitboxTmp.append([hitboxMin[0], hitboxMin[1], hitboxMin[2],
                                  hitboxMax[0], hitboxMax[1], hitboxMax[2]])

        if not self.fSeparateHitbox:
            hitboxTmp.append([hitboxMin[0], hitboxMin[1], hitboxMin[2],
                              hitboxMax[0], hitboxMax[1], hitboxMax[2]])

        self.hitbox.append(hitboxTmp)


def calculateVNornIndex_fn(self):
    '''find the closest normal for every vertex on all frames
        TODO speed this up somehow?
        162*MD2_MAX_VERTS*MD2_MAX_FRAMES = 339mil
    '''
    # import numpy as np  # todo test

    # self.vNormData = [None] * self.numFrames
    self.time = timer()  # reset timmer
    # print('=====')
    prefix = "Calculate vertex normals"
    for frame in range(self.numFrames):
        printProgress_fn(self, frame, prefix)  # print progress
        m_tmp = []
        for tmp_mesh in self.frameData[frame]:
            vn_tmp = [0] * tmp_mesh[IDX_I_VERT]
            for i, vn in enumerate(tmp_mesh[IDX_XYZ_VN]):
                maxDot = vn[0] * MD2_VN[0][0] + vn[1] * MD2_VN[0][1] + vn[2] * MD2_VN[0][2]
                bestIdx = 0
                for iN in range(1, 162):
                    # dot = np.dot(vnorm, MD2_VN[iN])
                    # dot = sum(vnorm[j] * MD2_VN[iN][j] for j in range(3))
                    dot = vn[0] * MD2_VN[iN][0] + vn[1] * MD2_VN[iN][1] + vn[2] * MD2_VN[iN][2]

                    if dot > maxDot:
                        maxDot = dot
                        bestIdx = iN
                        if maxDot > 0.99:  # stop wasting time
                            break

                vn_tmp[i] = bestIdx  # normal index
            m_tmp.append(vn_tmp)  # object
            del vn_tmp
        self.vNormData.append(m_tmp)  # frame
    del m_tmp
    printDone_fn(self, prefix)  # Done.


def setup_data_fn(self, context):
    ''' build a valid model and export '''
    def get_numTris(self):
        triCount = 0  # self.numTris
        for tmp_mesh in self.frameData[0]:
            triCount += tmp_mesh[IDX_I_FACE]

        if triCount > MD2_MAX_TRIANGLES:
            raise RuntimeError("Object has too many (triangulated) faces (%i), at most %i are supported in md2"
                               % (triCount, MD2_MAX_TRIANGLES))
        return triCount

    def get_numVerts(self):
        vertCount = 0  # self.numVerts
        for tmp_mesh in self.frameData[0]:
            vertCount += tmp_mesh[IDX_I_VERT]

        if vertCount > MD2_MAX_VERTS:
            raise RuntimeError(
                "Object has too many (triangulated) faces (%i), at most %i are supported in md2"
                % (vertCount, MD2_MAX_VERTS))
        return vertCount

    def get_numUV(self):
        uvCount = 0
        for tmp_mesh in self.frameData[0]:
            uvCount += tmp_mesh[IDX_I_UV]
        return uvCount

    self.obj_array = []
    self.frameData = []
    self.frameDataBBox = []
    self.hitbox = []  # mdx hitbox
    self.vertCounter = []
    self.glCmdList = []
    self.vNormData = []

    self.vertices = -1
    self.faces = 0
    self.status = ('', '')
    self.numFrames = 1 if not self.fExportAnimation else (1 + self.fEndFrame - self.fStartFrame)
    if self.numFrames > MD2_MAX_FRAMES:
        raise RuntimeError(
            "There are too many frames (%i), at most %i are supported in md2/mdx"
            % (self.numFrames, MD2_MAX_FRAMES))

    getSkins_fn(self, self.objects, self.fTextureNameMethod)  # get texture names
    self.frameNames = buildFrameNames_fn(self)  # setup frame names
    setupInternalArrays_fn(self, context)  # generate mesh/objects
    calcSharedBBox_fn(self)   # get min/max dimensions
    calculateVNornIndex_fn(self)  # slow

    self.numSkins = len(self.skins)
    self.numVerts = get_numVerts(self)
    self.numTris = get_numTris(self)
    self.numGLCmds = buildGLcommands_fn(self)

    self.frameSize = struct.calcsize("<6f16s") + (struct.calcsize("<4B") * self.numVerts)
    # setup md2/mdx header
    if self.isMdx:
        self.ident = 1481655369
        self.version = 4
        calculateHitBox_fn(self)
        self.numSfxDefines = 0  # mdx
        self.numSfxEntries = 0  # mdx
        self.numSubObjects = 1 if not self.fSeparateHitbox else len(self.objects)
        # offsets
        self.ofsSkins = struct.calcsize("<23i")
        self.ofsTris = self.ofsSkins + struct.calcsize("<64s") * self.numSkins
        self.ofsFrames = self.ofsTris + struct.calcsize("<6H") * self.numTris
        self.ofsGLCmds = self.ofsFrames + self.frameSize * self.numFrames
        self.ofsVertexInfo = self.ofsGLCmds + struct.calcsize("<i") * self.numGLCmds  # mdx
        self.ofsSfxDefines = self.ofsVertexInfo + struct.calcsize("<i") * (self.numVerts)  # mdx
        self.ofsSfxEntries = self.ofsSfxDefines  # mdx
        self.ofsBBoxFrames = self.ofsSfxEntries  # mdx
        self.ofsDummyEnd = self.ofsBBoxFrames + struct.calcsize("<6i") * (self.numFrames * self.numSubObjects)  # mdx
        self.ofsEnd = self.ofsDummyEnd
    else:
        self.ident = 844121161
        self.version = 8
        self.numUV = get_numUV(self)
        # offsets
        self.ofsSkins = struct.calcsize("<17i")
        self.ofsUV = self.ofsSkins + struct.calcsize("<64s") * self.numSkins
        self.ofsTris = self.ofsUV + struct.calcsize("<2h") * self.numUV
        self.ofsFrames = self.ofsTris + struct.calcsize("<6H") * self.numTris
        self.ofsGLCmds = self.ofsFrames + self.frameSize * self.numFrames
        self.ofsEnd = self.ofsGLCmds + struct.calcsize("<i") * self.numGLCmds


def write_fn(self, filePath):
    ''' write file '''

    self.time = timer()  # reset timmer
    prefix = "Writing file"
    #
    file = open(filePath, "wb")
    try:
        # ####################
        # ### write header ###
        if self.isMdx:  # mdx
            data = struct.pack(
                "<23i", self.ident, self.version,
                self.skinWidth, self.skinHeight,
                self.frameSize,
                self.numSkins, self.numVerts, self.numTris, self.numGLCmds, self.numFrames,
                self.numSfxDefines, self.numSfxEntries, self.numSubObjects,  # mdx
                self.ofsSkins, self.ofsTris, self.ofsFrames, self.ofsGLCmds,
                self.ofsVertexInfo, self.ofsSfxDefines, self.ofsSfxEntries, self.ofsBBoxFrames,  # mdx
                self.ofsDummyEnd,  # mdx
                self.ofsEnd)
        else:  # ms2
            data = struct.pack(
                "<17i", self.ident, self.version,
                self.skinWidth, self.skinHeight,
                self.frameSize,
                self.numSkins, self.numVerts, self.numUV, self.numTris, self.numGLCmds, self.numFrames,
                self.ofsSkins, self.ofsUV, self.ofsTris, self.ofsFrames, self.ofsGLCmds,
                self.ofsEnd)
        file.write(data)

        # #############################
        # ### write skin file names ###
        for skinName in self.skins:  # enumerate(# TODO file path?
            data = struct.pack("<64s", bytes(skinName[0:(MD2_MAX_SKINNAME - 1)], encoding="utf8"))
            file.write(data)  # skin name
        del self.skins  # TODO

        # ###############################
        # ### write software uv byte ###
        if not self.isMdx:  # MD2
            for tmp_mesh in self.frameData[0]:
                # tmp_mesh[IDX_I_UV]
                for uv in tmp_mesh[IDX_XY_UV]:
                    data = struct.pack(
                        "<2h",
                        int(uv[0] * self.skinWidth),
                        int((1 - uv[1]) * self.skinHeight))  # TODO check invalid 0-1 uv space
                    file.write(data)  # uv

        # #################################
        # ### write triangle index data ###
        ofsetVertID = 0
        objIdx = 0
        for tmp_mesh in self.frameData[0]:
            face = tmp_mesh[IDX_IDC_V]
            uv = tmp_mesh[IDX_IDC_UV]
            for idx in range(tmp_mesh[IDX_I_FACE]):
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

            ofsetVertID += len(tmp_mesh[IDX_IDC_V])
            self.vertCounter.append(len(tmp_mesh[IDX_XYZ_V]))

        # ####################
        # ### write frame/s ###
        for frame in range(self.numFrames):
            printProgress_fn(self, frame, prefix)  # print progress

            # output frames to file
            write_frame_fn(self, file, frame, self.frameNames[frame])
        ###########################
        # ### write GL Commands ###
        for glCmd in self.glCmdList:
            if self.isMdx:
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
        if self.isMdx:
            # ofsVertexInfo #mdx
            for mdxObj, tmp_mesh in enumerate(self.frameData[0]):
                for vert in range(tmp_mesh[IDX_I_VERT]):
                    if self.fSeparateHitbox:
                        bits = (1 << mdxObj)
                    else:
                        bits = 1
                    data = struct.pack("<i", bits)  # fill as object #1 TODO
                    file.write(data)  # vert index

            # ofsSfxDefines #mdx
            # ofsSfxEntries #mdx
            # ofsBBoxFrames #mdx
            for mdxObj in range(self.numSubObjects):
                for i in range(self.numFrames):
                    data = struct.pack(
                        "<6f",
                        self.hitbox[i][mdxObj][0],
                        self.hitbox[i][mdxObj][1],
                        self.hitbox[i][mdxObj][2],
                        self.hitbox[i][mdxObj][3],
                        self.hitbox[i][mdxObj][4],
                        self.hitbox[i][mdxObj][5])
                    file.write(data)
    finally:
        file.close()

    printDone_fn(self, prefix)  # Done.
    print("Model exported.")
    # TODO cleanup arrays
    del self.frameNames, self.frameData, self.frameDataBBox, self.vNormData


def Export_MD2_fn(self, context, filepath):
    '''    Export model    '''
    def isSelObjs_mesh_fn(self):
        ''' make sure all selected objects are mesh '''
        for obj in self.objects:
            if not (obj.type == 'MESH'):
                return False
        return True

    self.time = timer()
    # file extension
    ext = os.path.splitext(os.path.basename(filepath))[1]
    if ext == '.mdx':
        self.isMdx = True
    elif ext == '.md2':
        filePath = bpy.path.ensure_ext(filepath, self.filename_ext)
        self.isMdx = False
    else:
        raise RuntimeError("ERROR: Incorrect file extension. Not md2 or mdx")
        return False

    if isSelObjs_mesh_fn(self):  # self.isMesh
        origFrame = bpy.context.scene.frame_current

        if self.fIsPlayerModel:
            self.fUseSharedBoundingBox = False

        try:
            setup_data_fn(self, context)
            write_fn(self, filepath)
        finally:
            # if self.fExportAnimation:
            bpy.context.scene.frame_set(origFrame, subframe=0.0)
    else:
        raise RuntimeError("Only mesh objects can be exported")
