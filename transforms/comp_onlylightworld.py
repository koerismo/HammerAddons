''' Removes light entities flaged by the user. '''

from srctools import Vec, conv_bool
from srctools.bsp import BSP_LUMPS
from hammeraddons.bsp_transform import trans, Context
from srctools.logger import get_logger
import struct

LOGGER = get_logger(__name__)
wlight_struct = struct.Struct( '< 9f 3i 7f 3i' )

EMIT_SURFACE	= 0
EMIT_POINT		= 1
EMIT_SPOTLIGHT	= 2
EMIT_SKYLIGHT	= 3
EMIT_QUAKELIGHT	= 4
EMIT_SKYAMBIENT	= 5

class worldlight():
	def __init__( self, raw ):
		self._raw = raw

		self.origin = Vec()
		self.intensity = Vec()
		self.normal = Vec()
		
		(
		self.origin.x,    self.origin.y,    self.origin.z,		# Vec
		self.intensity.x, self.intensity.y, self.intensity.z,	# Vec
		self.normal.x,    self.normal.y,    self.normal.z,		# Vec

		self.cluster,			# int
		self.emittype,			# int
		self.style,				# int

		self.stopdot,			# float
		self.stopdot2,			# float
		self.exponent,			# float
		self.radius,			# float

		self.constant_attn,		# float
		self.linear_attn,		# float
		self.quadratic_attn,	# float

		self.flags,				# int
		self.texinfo,			# int
		self.owner				# int

		) = wlight_struct.unpack(raw)

	def pack( self ):
		return wlight_struct.pack(
		*tuple(self.origin),	# Vec
		*tuple(self.intensity),	# Vec
		*tuple(self.normal),	# Vec

		self.cluster,			# int
		self.emittype,			# int
		self.style,				# int

		self.stopdot,			# float
		self.stopdot2,			# float
		self.exponent,			# float
		self.radius,			# float

		self.constant_attn,		# float
		self.linear_attn,		# float
		self.quadratic_attn,	# float

		self.flags,				# int
		self.texinfo,			# int
		self.owner				# int
		)

@trans('Only Light World', post_vrad=True)
def only_light_world(ctx: Context):
	''' Removes lights with the Only Light World keyvalue enabled. '''
	# https://github.com/ValveSoftware/source-sdk-2013/blob/master/sp/src/public/bspfile.h#L966-L987


	# Read worldlight lump into list of objects
	wlight_hdr_lump = ctx.bsp.lumps[BSP_LUMPS.WORLDLIGHTS_HDR].data
	wlights_hdr: list[worldlight] = []
	for i in range( 0, len(wlight_hdr_lump), 88 ):
		if i+88 >= len(wlight_hdr_lump): break
		chunk = wlight_hdr_lump[i:i+88]
		wlights_hdr.append(worldlight(chunk))

	# Read entities and create worldlight blacklist
	blacklist = []
	for ent_class in {'light', 'light_spot'}: 
		for entity in ctx.vmf.by_class[ent_class]:

			onlyworld = entity.get('onlylightworld', default=None)
			if onlyworld is None: continue

			if conv_bool(onlyworld):
				blacklist.append(entity.id)
				entity.remove()

			del entity['onlylightworld']

	# Reconstruct lump
	out = b''
	for light in wlights_hdr:
		if light.owner not in blacklist: out += light._raw

	# Add a dummy worldlight to prevent the game from enabling fullbright
	if len(out) == 0 and len(blacklist) > 0:
		blanklight = worldlight( b'\x00'*88 )
		blanklight.emittype = 1
		blanklight.owner = blacklist[0]
		out = blanklight.pack()

	# Write revised lump
	ctx.bsp.lumps[BSP_LUMPS.WORLDLIGHTS_HDR].data = out
