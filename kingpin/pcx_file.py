# pylint: disable=invalid-name
'''
    load kingpin pcx file format

'''


import os
import struct
import bpy


def read_pcx_file(imagepath="",
                  dirname="",
                  check_existing=True,
                  md2_name='skin.pcx',
                  store_image=False
                  ):
    ''' import pcx file. read data'''

    def find_file_path(imagepath, dirname=""):
        ''' copy from image_utils '''
        # imagepath =
        bpy.path.native_pathsep(imagepath)
        if os.path.exists(imagepath):
            return imagepath
        variants = [imagepath]
        if dirname:
            variants += [
                os.path.join(dirname, imagepath),
                os.path.join(dirname, bpy.path.basename(imagepath)),
            ]
        for filepath_test in variants:
            ncase_variants = (
                filepath_test,
                bpy.path.resolve_ncase(filepath_test),
            )
            for nfilepath in ncase_variants:
                if os.path.exists(nfilepath):
                    return nfilepath
        return None
        # end find_file_path

    ##############################
    # check for duplicate textures
    if check_existing:
        for img in bpy.data.images:
            if img.name == md2_name:
                return img

    #################
    # does file exist?
    filepath = find_file_path(imagepath, dirname)
    if filepath is None:
        return None

    # setup read data
    img_data = []
    pal_data = []
    w = 0
    h = 0

    f = open(file=filepath, mode="rb")
    try:
        # read header
        buff = f.read(struct.calcsize("<4B6H"))
        data = struct.unpack("<4B6H", buff) #4B6H50B4H54B
        identifier = data[0]
        version = data[1]
        encoding = data[2]
        bits_pp = data[3]
        x_start = data[4]
        y_start = data[5]
        x_end = data[6]
        y_end = data[7]

        # kingpin supported format
        if (not identifier == 10 or # Identifier
                not version == 5 or # Version
                not bits_pp == 8 or # Bits per Pixel
                not encoding == 1): # Encoding Format
            raise NameError("Invalid PCX file(version)") # TODO print id
        # fill header details

        w = x_end - x_start + 1
        h = y_end - y_start + 1

        # go to pallet
        f.seek(-768, 2)
        buff = f.read(struct.calcsize("<768B"))
        pal_data = struct.unpack("<768B", buff)

        #read pixel data
        f.seek(128)
        ptr = 0
        rep = 0
        size = w * h
        while ptr < size:
            ch = struct.unpack("<1B", f.read(struct.calcsize("<1B")))
            if ch[0] >= 192:
                rep = ch[0] - 192
                ch = struct.unpack("<1B", f.read(struct.calcsize("<1B")))
            else:
                rep = 1

            # repeat pixel
            while rep > 0:
                img_data.append(ch[0])
                ptr += 1
                rep -= 1
    finally:
        f.close()

    ####################
    # check invalid data
    if len(img_data) == 0 or len(pal_data) == 0 or w == 0 or h == 0:
        return None
    if len(pal_data) < 768 or len(img_data) < w*h:
        return None

    ######################
    # write new image data
    img = bpy.data.images.new(md2_name, width=w, height=h)
    rgb_image = [] # * w * h
    for y in range(h-1, -1, -1):
        for x in range(w):
            pal_idx = img_data[y * w + x] * 3
            rgb_image.append(pal_data[pal_idx + 0] / 255)
            rgb_image.append(pal_data[pal_idx + 1] / 255)
            rgb_image.append(pal_data[pal_idx + 2] / 255)
            if pal_idx == 765: # alpha (256 * 3) - 3
                rgb_image.append(0.0)
            else:
                rgb_image.append(1.0)

    img.pixels = rgb_image
    if store_image:
        img.pack()

    return img
