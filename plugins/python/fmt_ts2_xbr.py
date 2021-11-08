#Noesis Python model import, imports some data from Time Splitters 2(XBOX)

from inc_noesis import *
import math
import os
import xbt

import noesis

#rapi methods should only be used during handler callbacks
import rapi

#registerNoesisTypes is called by Noesis to allow the script to register formats.
#Do not implement this function in script files unless you want them to be dedicated format modules!
def registerNoesisTypes():
	handle = noesis.register("Time Splitters 2", ".xbr")
	noesis.setHandlerTypeCheck(handle, tsCheckType)
	noesis.setHandlerLoadModel(handle, tsLoadModel) #see also noepyLoadModelRPG
	#noesis.logPopup()
	return 1

#check if it's this type based on the data

def tsCheckType(data):
	bs = NoeBitStream(data)
	idMagic = bs.readInt()
	if idMagic == 0xC or idMagic == 0x20:
		return 1
	return 0      

#load the model
def tsLoadModel(data, mdlList):
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
			parent = os.path.normpath(os.path.join(rapi.getDirForFilePath(rapi.getInputName()), ".."))
			parent = os.path.normpath(os.path.join(parent, ".."))
			parent = os.path.normpath(os.path.join(parent, "textures")) + "\\"
			if (rapi.checkFileExists(parent + texName + ".xbt")):
				texData = rapi.loadIntoByteArray(parent + texName + ".xbt")
				if xbt.TSLoadRGBA(texData, texList) == 1:
					texList[len(texList)-1].name = (texName + ".tga")
					texNameList.append(texName + ".tga")
					material.setTexture(texName + ".tga")
					matList.append(material)
	meshInfo = []
	if texStart == 0xC:
		bs.seek(meshCountOffset, NOESEEK_ABS)
		modelCount = bs.readInt()
		unk000 = bs.readInt()
		unk001 = bs.readInt()
		meshTableOffset = (meshCountOffset - (0x9C * modelCount))
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
				meshInfo.append([sections, vertOffsets, faceOffsets, count000, count001])
	if texStart == 0x20:
		modelCount = (len(data) - meshCountOffset) // 0xB0
		for i in range(0, modelCount):
			bs.seek(meshCountOffset + (i * 0xB0), NOESEEK_ABS)
			meshTableOffset = (bs.readUInt() - 0x9C)
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
					meshInfo.append([sections, vertOffsets, faceOffsets, count000, count001])


	for i in range(0, len(meshInfo)):#len(meshInfo)
		if texStart == 0xC:
			objCount = (((meshInfo[i][1][4] - meshInfo[i][1][0]) - 2) // 10)
			bs.seek(meshInfo[i][1][0], NOESEEK_ABS)
		else:
			objCount = (((meshInfo[i][1][7] - meshInfo[i][1][4])) // 0x10)
			bs.seek(meshInfo[i][1][0], NOESEEK_ABS)
		meshTable = []
		for a in range(0, objCount):
			texid = bs.readUShort()
			meshId = bs.readUShort()
			vertStart = bs.readUShort()
			vertCount = bs.readUShort()
			unk003 = bs.readUShort()
			if meshId >= len(meshTable):
				meshTable.append([meshId, vertStart, vertCount, texid, meshInfo[i][1][5], meshInfo[i][1][6], meshInfo[i][1][7], meshInfo[i][1][8]])

		if meshInfo[i][0] >= 2:
			if texStart == 0xC:
				objCount = (((meshInfo[i][1][9] - meshInfo[i][1][5]) - 2) // 10)
				bs.seek(meshInfo[i][1][1], NOESEEK_ABS)
			else:
				objCount = (((meshInfo[i][1][12] - meshInfo[i][1][9])) // 0x10)
				bs.seek(meshInfo[i][1][1], NOESEEK_ABS)
				for a in range(0, objCount):
					texid = bs.readUShort()
					meshId = bs.readUShort()
					vertStart = bs.readUShort()
					vertCount = bs.readUShort()
					unk003 = bs.readUShort()
					if vertCount != 0xFFFF:
						meshTable.append([meshId, vertStart, vertCount, texid, meshInfo[i][1][10], meshInfo[i][1][11], meshInfo[i][1][12], meshInfo[i][1][13]])

		if meshInfo[i][0] >= 3:
			if texStart == 0xC:
				objCount = (((meshInfo[i][1][14] - meshInfo[i][1][10]) - 2) // 10)
				bs.seek(meshInfo[i][1][2], NOESEEK_ABS)
			else:
				objCount = (((meshInfo[i][1][17] - meshInfo[i][1][14])) // 0x10)
				bs.seek(meshInfo[i][1][2], NOESEEK_ABS)
				for a in range(0, objCount):
					texid = bs.readUShort()
					meshId = bs.readUShort()
					vertStart = bs.readUShort()
					vertCount = bs.readUShort()
					unk003 = bs.readUShort()
					if vertCount != 0xFFFF:
						meshTable.append([meshId, vertStart, vertCount, texid, meshInfo[i][1][15], meshInfo[i][1][16], meshInfo[i][1][17], meshInfo[i][1][18]])

		#faceTable = []
		#bs.seek(meshInfo[i][2][0], NOESEEK_ABS)
		#for a in range(0, len(meshTable)):
		#	faceOffset = bs.readUInt()
		#	faceCount = bs.readUInt()
		#	if faceOffset != 0:
		#		faceTable.append([faceOffset, faceCount])
		#print("here")
		#print(len(meshTable))

		for a in range(0, len(meshTable)):#len(meshTable)
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
				if (flag == 0x00):
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

			vertBuff = struct.pack('f'*len(vertData), *vertData)
			uvBuff = struct.pack('f'*len(uvData), *uvData)
			if texStart == 0xC:
				normalBuff = struct.pack('f'*len(normalData), *normalData)
			faceBuff = struct.pack('H'*len(faceData), *faceData)	
			rapi.rpgBindPositionBuffer(vertBuff, noesis.RPGEODATA_FLOAT, 12)
			if texStart == 0xC:
				rapi.rpgBindNormalBuffer(normalBuff, noesis.RPGEODATA_FLOAT, 12)
			rapi.rpgBindUV1Buffer(uvBuff, noesis.RPGEODATA_FLOAT, 8)
			rapi.rpgCommitTriangles(faceBuff, noesis.RPGEODATA_USHORT, len(faceData), noesis.RPGEO_TRIANGLE, 1)
			rapi.rpgClearBufferBinds()

	mdl = rapi.rpgConstructModel()
	mdl.setModelMaterials(NoeModelMaterials(texList, matList))
	mdlList.append(mdl)	
	return 1
