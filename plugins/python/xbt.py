from inc_noesis import *

def registerNoesisTypes():
	handle = noesis.register("Time Splitters XBT", ".xbt")
	noesis.setHandlerTypeCheck(handle, TSCheckType)
	noesis.setHandlerLoadRGBA(handle, TSLoadRGBA)
	return 1

def TSCheckType(data):
	bs = NoeBitStream(data)
	Magic = bs.readInt()
	return 1   

def TSLoadRGBA(data, texList):
	datasize = len(data) - 0x80
	bs = NoeBitStream(data)
	Magic = bs.readInt()
	stuff = bs.readInt()
	imgWidth = bs.readInt()
	imgHeight = bs.readInt()
	bs.seek(0x14, NOESEEK_ABS)
	imgFmt = bs.readInt()
	bs.seek(0x80, NOESEEK_ABS)
	#DXT1
	if imgFmt == 0:
		data = bs.readBytes(datasize)
		texFmt = noesis.NOESISTEX_DXT1
	#DXT3
	elif imgFmt == 1:
		data = bs.readBytes(datasize)
		texFmt = noesis.NOESISTEX_DXT3
	#DXT1 packed normal map
	elif imgFmt == 2:
		data = bytearray()
		for y in range(0, imgHeight):
			for x in range(0, imgWidth):
				idx = noesis.morton2D(y, x)
				if (idx*4+4) > datasize:
					idx = 0
				bs.seek(128 + idx*4, NOESEEK_ABS)
				data += bs.readBytes(4)
		data = rapi.imageDecodeRaw(data, imgWidth, imgHeight, "b8g8r8a8")
		texFmt = noesis.NOESISTEX_RGBA32
	#raw
	elif imgFmt == 3:
		texFmt = noesis.NOESISTEX_RGB24
	#unknown, not handled
	else:
		print("WARNING: Unhandled image format " + repr(imgFmt) + " - " + repr(imgWidth) + "x" + repr(imgHeight) + " - " + repr(len(data)))
		return None
	texList.append(NoeTexture(rapi.getInputName(), imgWidth, imgHeight, data, texFmt))
	return 1
