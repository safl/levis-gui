#!/usr/bin/python
import math
import os

import Image

def main():
	
	(width, height)	= (16, 16)	# Sprite dimensions
	sprites_x		= 4			# How many sprites horizontally on the map
	
	mapping_fn		= 'mapping.txt'
	sprite_dir		= 'icons'+os.sep
	spritemap_fn	= 'sprites'	
	css				= ".gui-icon { width: 16px; height: 16px; background-image: url(static/img/%s.png); }\n" % spritemap_fn
	css_template	= ".gui-icon-%s { background-position: -%dpx -%dpx; }\n"	
	
	fof = []
	
	with open(mapping_fn) as fd:
		lines	= [line.rstrip().split(':') for line in fd.readlines()]
		mapping = [(style.strip(), fn.strip()) for (style, fn) in lines]
		mapping.sort()
		
	sprites		= len(mapping)+1
	sprites_y	= int(math.ceil(float(sprites) / float(sprites_x)))
	
	spritemap	= Image.new(
		mode='RGBA',
		size=(
			sprites_x * width,
			sprites_y * height
		),
		color=(0,0,0,0)
	)
	
	y_offset = 0
	x_offset = width # First icon is blank/transparent
	for style, sprite in ((style, Image.open(sprite_dir+fn)) for style, fn in mapping):
		
		spritemap.paste(sprite, (x_offset, y_offset))
		css += css_template % (style, x_offset, y_offset)
		
		x_offset += width
		if x_offset % (sprites_x * width)  == 0:
			y_offset += height
			x_offset = 0
	
	spritemap.save('%s.png' % spritemap_fn)	
	with open('%s.css' % spritemap_fn ,'w') as fd:
		fd.write( css )

if __name__ == "__main__":
	main()
