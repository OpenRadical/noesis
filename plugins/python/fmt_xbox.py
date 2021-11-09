# coding=utf-8

"""
Noesis TimeSplitters formats
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

import os
import struct

from inc_noesis import *
import noesis
import rapi

XBT_HEADER_SIZE = 0x80

XBT_DXT1 = 0x00
XBT_DXT3 = 0x01
XBT_DXT1_PACKED_NORMAL_MAP = 0x02
XBT_RAW = 0x03


def registerNoesisTypes():
    """Register Noesis types for .xb* files."""

    handleXbt = noesis.register("TimeSplitters Texture", ".xbt")
    noesis.setHandlerTypeCheck(handleXbt, xbtCheckType)
    noesis.setHandlerLoadRGBA(handleXbt, xbtLoadRGBA)

    handleXbr = noesis.register("TimeSplitters Model", ".xbr")
    noesis.setHandlerTypeCheck(handleXbr, xbrCheckType)
    noesis.setHandlerLoadModel(handleXbr, xbrLoadModel)
    return 1


def xbtCheckType(data):
    """Check magic bit for .xbt files."""
    bs = NoeBitStream(data)
    magic = bs.readInt()
    return 1


def xbrCheckType(data):
    """Check magic bit for .xbr files."""

    bs = NoeBitStream(data)
    magic = bs.readInt()
    return magic in (0xC, 0x20)


def xbtLoadRGBA(data, texList):
    dataSize = len(data) - XBT_HEADER_SIZE
    bs = NoeBitStream(data)
    magic = bs.readInt()
    stuff = bs.readInt()
    imageWidth = bs.readInt()
    imageHeight = bs.readInt()
    bs.seek(0x14, NOESEEK_ABS)
    imageFormat = bs.readInt()
    bs.seek(XBT_HEADER_SIZE, NOESEEK_ABS)
    if imageFormat == XBT_DXT1:
        data = bs.readBytes(dataSize)
        textureFormat = noesis.NOESISTEX_DXT1
    elif imageFormat == XBT_DXT3:
        data = bs.readBytes(dataSize)
        textureFormat = noesis.NOESISTEX_DXT3
    elif imageFormat == XBT_DXT1_PACKED_NORMAL_MAP:
        data = bytearray()
        for y in range(0, imageHeight):
            for x in range(0, imageWidth):
                idx = noesis.morton2D(y, x)
                if (idx * 4 + 4) > dataSize:
                    idx = 0
                bs.seek(128 + idx * 4, NOESEEK_ABS)
                data += bs.readBytes(4)
        data = rapi.imageDecodeRaw(data, imageWidth, imageHeight, "b8g8r8a8")
        textureFormat = noesis.NOESISTEX_RGBA32
    # raw
    elif imageFormat == XBT_RAW:
        textureFormat = noesis.NOESISTEX_RGB24
    # unknown, not handled
    else:
        print(
            "WARNING: Unhandled image format {fmt} - {width}x{height} - {length:d}".format(
                fmt=imageFormat,
                width=imageWidth,
                height=imageHeight,
                length=len(data),
            )
        )
        return None
    texList.append(
        NoeTexture(rapi.getInputName(), imageWidth, imageHeight, data, textureFormat)
    )
    return 1


def xbrLoadModel(data, mdlList):
    """Load a TimeSplitters model."""
    ctx = rapi.rpgCreateContext()
    bs = NoeBitStream(data)
    texStart = bs.readInt()
    meshCountOffset = bs.readInt()
    texId = 0
    matList = []
    texList = []
    texNameList = []
    bs.seek(texStart, NOESEEK_ABS)
    while texId != 0xFFFFFFFF:
        material = NoeMaterial(str(len(texNameList)), "")
        texId = bs.readUInt()
        bs.seek(12, NOESEEK_REL)
        if texId != 0xFFFFFFFF:
            texName = str(texId).zfill(4)
            parent = os.path.normpath(
                os.path.join(rapi.getDirForFilePath(rapi.getInputName()), "..")
            )
            parent = os.path.normpath(os.path.join(parent, ".."))
            parent = os.path.normpath(os.path.join(parent, "textures")) + "\\"
            if rapi.checkFileExists(parent + texName + ".xbt"):
                texData = rapi.loadIntoByteArray(parent + texName + ".xbt")
                if xbtLoadRGBA(texData, texList) == 1:
                    texList[len(texList) - 1].name = texName + ".tga"
                    texNameList.append(texName + ".tga")
                    material.setTexture(texName + ".tga")
                    matList.append(material)
    meshInfo = []
    if texStart == 0xC:
        bs.seek(meshCountOffset, NOESEEK_ABS)
        modelCount = bs.readInt()
        unk000 = bs.readInt()
        unk001 = bs.readInt()
        meshTableOffset = meshCountOffset - (0x9C * modelCount)
        bs.seek(meshTableOffset, NOESEEK_ABS)
        for i in range(0, modelCount):
            header1 = bs.read("6B")
            bs.seek(0xE, NOESEEK_REL)
            vertOffsets = bs.read("I" * 19)
            count000 = bs.readShort()
            count001 = bs.readShort()
            bs.seek(0x28, NOESEEK_REL)
            float000 = bs.readInt()
            faceOffsets = bs.read("I" * 3)
            if faceOffsets[2] != 0:
                sections = 3
            elif faceOffsets[1] != 0:
                sections = 2
            else:
                sections = 1
            if vertOffsets[0] != 0:
                meshInfo.append(
                    [sections, vertOffsets, faceOffsets, count000, count001]
                )
    if texStart == 0x20:
        modelCount = (len(data) - meshCountOffset) // 0xB0
        for i in range(0, modelCount):
            bs.seek(meshCountOffset + (i * 0xB0), NOESEEK_ABS)
            meshTableOffset = bs.readUInt() - 0x9C
            if meshTableOffset > 0:
                bs.seek(meshTableOffset, NOESEEK_ABS)
                header1 = bs.read("6B")
                bs.seek(0xE, NOESEEK_REL)
                vertOffsets = bs.read("I" * 19)
                count000 = bs.readShort()
                count001 = bs.readShort()
                bs.seek(0x28, NOESEEK_REL)
                float000 = bs.readInt()
                faceOffsets = bs.read("I" * 3)
                if faceOffsets[2] != 0:
                    sections = 3
                elif faceOffsets[1] != 0:
                    sections = 2
                else:
                    sections = 1
                if vertOffsets[0] != 0:
                    meshInfo.append(
                        [sections, vertOffsets, faceOffsets, count000, count001]
                    )

    for i in range(0, len(meshInfo)):
        if texStart == 0xC:
            objCount = ((meshInfo[i][1][4] - meshInfo[i][1][0]) - 2) // 10
            bs.seek(meshInfo[i][1][0], NOESEEK_ABS)
        else:
            objCount = ((meshInfo[i][1][7] - meshInfo[i][1][4])) // 0x10
            bs.seek(meshInfo[i][1][0], NOESEEK_ABS)
        meshTable = []
        for a in range(0, objCount):
            texid = bs.readUShort()
            meshId = bs.readUShort()
            vertStart = bs.readUShort()
            vertCount = bs.readUShort()
            unk003 = bs.readUShort()
            if meshId >= len(meshTable):
                meshTable.append(
                    [
                        meshId,
                        vertStart,
                        vertCount,
                        texid,
                        meshInfo[i][1][5],
                        meshInfo[i][1][6],
                        meshInfo[i][1][7],
                        meshInfo[i][1][8],
                    ]
                )

        if meshInfo[i][0] >= 2:
            if texStart == 0xC:
                objCount = ((meshInfo[i][1][9] - meshInfo[i][1][5]) - 2) // 10
                bs.seek(meshInfo[i][1][1], NOESEEK_ABS)
            else:
                objCount = ((meshInfo[i][1][12] - meshInfo[i][1][9])) // 0x10
                bs.seek(meshInfo[i][1][1], NOESEEK_ABS)
                for a in range(0, objCount):
                    texid = bs.readUShort()
                    meshId = bs.readUShort()
                    vertStart = bs.readUShort()
                    vertCount = bs.readUShort()
                    unk003 = bs.readUShort()
                    if vertCount != 0xFFFF:
                        meshTable.append(
                            [
                                meshId,
                                vertStart,
                                vertCount,
                                texid,
                                meshInfo[i][1][10],
                                meshInfo[i][1][11],
                                meshInfo[i][1][12],
                                meshInfo[i][1][13],
                            ]
                        )

        if meshInfo[i][0] >= 3:
            if texStart == 0xC:
                objCount = ((meshInfo[i][1][14] - meshInfo[i][1][10]) - 2) // 10
                bs.seek(meshInfo[i][1][2], NOESEEK_ABS)
            else:
                objCount = ((meshInfo[i][1][17] - meshInfo[i][1][14])) // 0x10
                bs.seek(meshInfo[i][1][2], NOESEEK_ABS)
                for a in range(0, objCount):
                    texid = bs.readUShort()
                    meshId = bs.readUShort()
                    vertStart = bs.readUShort()
                    vertCount = bs.readUShort()
                    unk003 = bs.readUShort()
                    if vertCount != 0xFFFF:
                        meshTable.append(
                            [
                                meshId,
                                vertStart,
                                vertCount,
                                texid,
                                meshInfo[i][1][15],
                                meshInfo[i][1][16],
                                meshInfo[i][1][17],
                                meshInfo[i][1][18],
                            ]
                        )

        # faceTable = []
        # bs.seek(meshInfo[i][2][0], NOESEEK_ABS)
        # for a in range(0, len(meshTable)):
        # 	faceOffset = bs.readUInt()
        # 	faceCount = bs.readUInt()
        # 	if faceOffset != 0:
        # 		faceTable.append([faceOffset, faceCount])
        # print("here")
        # print(len(meshTable))

        for a in range(0, len(meshTable)):  # len(meshTable)
            vertData = []
            normalData = []
            uvData = []
            faceData = []
            facedir = 0

            bs.seek(meshTable[a][4] + (0x10 * meshTable[a][1]), NOESEEK_ABS)
            rapi.rpgSetName(str(meshTable[a][3]))
            rapi.rpgSetMaterial(str(meshTable[a][3]))
            for b in range(0, meshTable[a][2]):
                vx = bs.readFloat()
                vy = bs.readFloat()
                vz = bs.readFloat()
                vertData.append(vx)
                vertData.append(vy)
                vertData.append(vz)
                wind = bs.readUByte()
                flag = bs.readUByte()
                scale = bs.readUShort()
                if flag == 0x00:
                    if (facedir ^ wind) == 0:
                        faceData.append(b - 2)
                        faceData.append(b - 1)
                        faceData.append(b)
                    else:
                        faceData.append(b - 1)
                        faceData.append(b - 2)
                        faceData.append(b)
                else:
                    facedir = 1
                facedir = 1 - facedir
            bs.seek(meshTable[a][5] + (0xC * meshTable[a][1]), NOESEEK_ABS)
            for b in range(0, meshTable[a][2]):
                tu = bs.readFloat()
                tv = bs.readFloat()
                tw = bs.readFloat()
                uvData.append(tu * tw)
                uvData.append(tv * tw)

            if texStart == 0xC:
                bs.seek(meshTable[a][7] + (0x10 * meshTable[a][1]), NOESEEK_ABS)
                for b in range(0, meshTable[a][2]):
                    nx = bs.readFloat()
                    ny = bs.readFloat()
                    nz = bs.readFloat()
                    nw = bs.readFloat()
                    normalData.append(nx)
                    normalData.append(ny)
                    normalData.append(nz)

            else:
                bs.seek(meshTable[a][6] + (0x10 * meshTable[a][1]), NOESEEK_ABS)

            vertBuff = struct.pack("f" * len(vertData), *vertData)
            uvBuff = struct.pack("f" * len(uvData), *uvData)
            if texStart == 0xC:
                normalBuff = struct.pack("f" * len(normalData), *normalData)
            faceBuff = struct.pack("H" * len(faceData), *faceData)
            rapi.rpgBindPositionBuffer(vertBuff, noesis.RPGEODATA_FLOAT, 12)
            if texStart == 0xC:
                rapi.rpgBindNormalBuffer(normalBuff, noesis.RPGEODATA_FLOAT, 12)
            rapi.rpgBindUV1Buffer(uvBuff, noesis.RPGEODATA_FLOAT, 8)
            rapi.rpgCommitTriangles(
                faceBuff,
                noesis.RPGEODATA_USHORT,
                len(faceData),
                noesis.RPGEO_TRIANGLE,
                1,
            )
            rapi.rpgClearBufferBinds()

    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(texList, matList))
    mdlList.append(mdl)
    return 1
