'''
This is a script that generates a countdown with second granularity for a seven-segment display in Vixen Lights.
This is my second attempt and it is significantly better than the first.
A 1 hour countdown with this script is about 100 MB as opposed to 800+ MB with the original method.
A 10 minute countdown is about 14 MB.
'''
import os
import sys
import re
from uuid import uuid4

############## GLOBAL CONFIG ###################
################################################
# this is the ModuleTypeId
# I have no idea if that always corresponds to the SetLevel effect or if this is arbitrary (I copied it from a Vixen-created sequence file).
type_id = '32cff8e0-5b10-4466-a093-0d232c55aac0' 

# I have no idea of this is consistent or not. I just copied it from a Vixen-created sequence file.
header_module_instance_id = 'f7a95a48-5eaa-407b-b194-b8eb079b9977'

# I'm assuming this can just be made up every time
layer_id = uuid4()
################################################

def secs_to_min_secs_format(total_secs):
	'''
	Turn a value in seconds into a Vixen-formatted minutes/seconds string.
	
	Arguments:
	total_secs (int) - time in seconds to format
	
	Returns:
	formatted string of the corresponding minutes and seconds
	'''
	cur_min = total_secs / 60
	cur_sec = total_secs - cur_min * 60
	return 'PT{}M{}S'.format(str(cur_min), str(cur_sec))
	
def get_any_type(the_id, type_id):
	'''
	Generate and return the "anyType" block to go in a sequence file for a Vixen SetLevel effect.
	
	Arguments:
	the_id (string) - UUID to use as the ModuleInstanceId
	
	Returns:
	stringified XML block with the specified ID
	'''
	return '<d1p1:anyType xmlns:d2p1="http://schemas.datacontract.org/2004/07/VixenModules.Effect.SetLevel" i:type="d2p1:SetLevelData"><ModuleInstanceId>{}</ModuleInstanceId><ModuleTypeId>{}</ModuleTypeId><TargetPositioning xmlns="http://schemas.datacontract.org/2004/07/VixenModules.Effect.Effect">Strings</TargetPositioning><d2p1:color xmlns:d3p1="http://schemas.datacontract.org/2004/07/Common.Controls.ColorManagement.ColorModels"><d3p1:_b>1</d3p1:_b><d3p1:_g>1</d3p1:_g><d3p1:_r>1</d3p1:_r></d2p1:color><d2p1:level>1</d2p1:level></d1p1:anyType>'.format(the_id, '32cff8e0-5b10-4466-a093-0d232c55aac0')
	
def get_effect(the_id, start_time, node, time_span, type_id):
	'''
	Generate the "EffectNodeSurrogate" block to go in a sequence file.
	
	Arguments:
	the_id (string) - UUID to use as the ModuleInstanceId
	start_time (string) - formatted time indicating the start of this effect in the sequence
	node (string) - UUID of the node for which this effect applies
	time_span (string) - formatted time indicating the duration of this effect in the sequence
	type_id (string) - 
	
	Returns:
	stringified XML block with the datacontract
	'''
	return "<EffectNodeSurrogate><InstanceId>{}</InstanceId><StartTime>{}</StartTime><TargetNodes><ChannelNodeReferenceSurrogate><NodeId>{}</NodeId></ChannelNodeReferenceSurrogate></TargetNodes><TimeSpan>{}</TimeSpan><TypeId>{}</TypeId></EffectNodeSurrogate>".format(the_id, start_time, node, time_span, type_id)

def read_in_nodes():
	'''
	Parse the SystemConfig.xml file to find all the nodes labeled as part of the seven-segment display
	
	Returns:
		tuple
			node_dict (dict) - key = (segment number, pixel number), value = node UUID
			colon_node_list (list) - list of node UUIDs used for the colon between minutes and seconds on the display
	'''
	with open('C:\Users\Filippo\Documents\Vixen 3\SystemData\SystemConfig.xml') as f:
		filecontents = f.read()

	node_dict = {}
	match = re.findall(r'<Node name="7 seg([0-9]+)\-([0-9]+)" id="([a-zA-Z0-9\-]+)"', filecontents)

	if match:
		for item in match:
			key = (int(item[0]), int(item[1]))
			node_dict[key] = item[2]
			
	# read in the nodes for the colon
	match = re.findall(r'<Node name="Colon-[1-4]" id="([a-zA-Z0-9\-]+)"', filecontents)

	colon_node_list = []
	if match:
		for item in match:
			colon_node_list.append(item)
			
	return node_dict, colon_node_list

def parse_node_on_list(on_list):
	'''
	Parse the list of seconds during which a node is on and turn it into a list of ranges for when the node is on.
	The input list indicates seconds when the node "starts" being on so it is necessary to add a 1 second duration to each range.
	
	Arguments:
	on_list (list) - the list of seconds during which the node starts being on
	
	Returns:
	list of tuples of the ranges of time when the node is on: [(start, stop)]
	'''
	return_list = []
	if on_list:
		start = on_list[0]
		end = on_list[0]
		for i in range(0, len(on_list)):
			try:
				if on_list[i] + 1 == on_list[i+1]:
					# in a consecutive block
					end = on_list[i+1]
				else:
					# end of a consecutive block so record it and start tracking the next one
					return_list.append((start, end+1))
					start = on_list[i+1]
					end = start
			except IndexError:
				# we walked off the end of the list
				end = end + 1
				return_list.append((start,end))
				
	return return_list

def test_node_on_list():
	'''Function to help with verifying logic in parse_node_on_list function.'''
	on_list = []	#
	print parse_node_on_list(on_list)
	on_list = [3]	#(3,4)
	print parse_node_on_list(on_list)
	on_list = [3,4]	#(3,5)
	print parse_node_on_list(on_list)
	on_list = [3,4,5]	#(3,6)
	print parse_node_on_list(on_list)
	on_list = [3,4,5,10]	#(3,6),(10,11)
	print parse_node_on_list(on_list)
	on_list = [5,6,7,8,9,24,25,30,39,40,41]	#(5,10),(24,26),(30,31),(39,42)
	print parse_node_on_list(on_list)
	
def main(args):
	'''Main function'''
	arg_syntax = 'python countdownGenerator.py <duration in seconds> <output file>'
	# process input arguments
	try:
		duration_secs = int(args[0])
	except (IndexError, ValueError):
		print 'Need input argument of total number of integer seconds for which to generate the countdown'
		print arg_syntax
		sys.exit(1)
		
	try:
		out_file = args[1]
	except IndexError:
		print 'Need input argument of filename for writing the output'
		print arg_syntax
		sys.exit(1)
	
	# read in nodes for seven segment displays
	node_dict, colon_node_list = read_in_nodes()
		
	# create mapping of the seven segments of a display to the list of nodes associated
	# key = segment
	# value = [min_pixel, max_pixel]
	segment_map = {
		1: [1, 15],
		2: [16, 28],
		3: [29, 43],
		4: [44, 56],
		5: [57, 69],
		6: [70, 84],
		7: [85, 97]
	}

	# create mapping of how to render a number to the generic segments
	# key = number to render
	# value = list of segments used in rendering that number
	# segment numbering is as follows
	#      3
	#  4       2
	#      1
	#  5       7
	#      6
	number_map = {
		0: [2, 3, 4, 5, 6, 7],
		1: [2, 7],
		2: [3, 2, 1, 5, 6],
		3: [3, 2, 1, 7, 6],
		4: [4, 1, 2, 7],
		5: [3, 4, 1, 7, 6],
		6: [3, 4, 5, 6, 7, 1],
		7: [3, 2, 7],
		8: [1, 2, 3, 4, 5, 6, 7],
		9: [1, 2, 3, 4, 7]
	}

	# instantiate the dictionary for tracking when each node is on or off
	node_on_secs = {}
	for node in node_dict.itervalues():
		node_on_secs[node] = []
	
	# create some variables
	effects = []
	any_types = []
	total_secs = 0

	# loop through the desired countdown duration in 1 second descending increments
	for step in range(duration_secs, -1, -1):
		# determine the current minute and second for this step
		minute = step / 60
		second = step - minute * 60
		
		# determine what character needs rendered on each of the 4 seven-segment displays
		# we elected to not display the minutes if not needed rather than displaying zeros
		segs = {}
		if minute > 9:
			segs[1] = minute / 10
			segs[2] = minute % 10
		elif minute == 0:
			segs[1] = None
			segs[2] = None
		else:
			segs[1] = None
			segs[2] = minute
			
		if second > 9:
			segs[3] = second / 10
			segs[4] = second % 10
		else:
			segs[3] = 0
			segs[4] = second

		# iterate through each seven-segment display
		for seg, value in segs.iteritems():
			if value is not None:
				# there is something to render so get the list of segments needed to render it
				segments = number_map[value]
				
				# loop through each segment that needs rendered
				for segment in segments:
					min_pixel = segment_map[segment][0]
					max_pixel = segment_map[segment][1]
					
					# loop through each pixel in that segment
					for pixel in range(min_pixel, max_pixel+1):
						try:
							# find the corresponding node for this particular pixel in this particular segment
							node = node_dict[(seg, pixel)]
						except KeyError as e:
							print node_dict
							raise e
						
						# add this specific second to the "on time" list for this node
						node_on_secs[node].append(total_secs)
		
		# increment the counter of total elapsed time
		total_secs += 1

	# iterate through the node_on_secs to create effects of correct duration for each node
	for node, on_list in node_on_secs.iteritems():
		
		# convert the list of on seconds into ranges of time
		on_sections = parse_node_on_list(on_list)
		
		# loop through list of ranges when the node is on
		for item in on_sections:
			start, end = item
			dur = end - start
			
			# generate the xml blocks and add them to the tracking lists
			the_id = uuid4()
			any_types.append(get_any_type(the_id, header_module_instance_id))
			effects.append(get_effect(the_id, secs_to_min_secs_format(start), node, secs_to_min_secs_format(dur), type_id))
	
	# add in turning on the colon for total duration of countdown
	total_duration = secs_to_min_secs_format(total_secs)
	for node in colon_node_list:
		the_id = uuid4()
		any_types.append(get_any_type(the_id, header_module_instance_id))
		effects.append(get_effect(the_id, 'PT0S', node, total_duration, type_id))

	
	# assemble final file
	header = '<?xml version="1.0" encoding="utf-8"?><TimedSequenceData version="4" xmlns:a="http://www.w3.org/2001/XMLSchema" xmlns:i="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://schemas.datacontract.org/2004/07/VixenModules.Sequence.Timed"><ModuleInstanceId xmlns="">{}</ModuleInstanceId><ModuleTypeId xmlns="">296bdba2-9bf3-4bff-a9f2-13efac5c8ecb</ModuleTypeId><Length xmlns="">{}</Length><SequenceLayers xmlns:d1p1="http://schemas.datacontract.org/2004/07/Vixen.Sys.LayerMixing" xmlns=""><d1p1:Layers xmlns:d2p1="http://schemas.microsoft.com/2003/10/Serialization/Arrays"><d2p1:anyType i:type="d1p1:DefaultLayer"><d1p1:Id>{}</d1p1:Id><d1p1:LayerLevel>0</d1p1:LayerLevel><d1p1:LayerName>Default</d1p1:LayerName><d1p1:Type>Default</d1p1:Type></d2p1:anyType></d1p1:Layers><d1p1:_effectLayerMap xmlns:d2p1="http://schemas.microsoft.com/2003/10/Serialization/Arrays" /></SequenceLayers><Version xmlns="">0</Version><_dataModels xmlns:d1p1="http://schemas.microsoft.com/2003/10/Serialization/Arrays" xmlns="">'.format(header_module_instance_id, total_duration, layer_id)

	footer = '</_effectNodeSurrogates><_filterNodeSurrogates xmlns="" /><_layerMixingFilterDataModels xmlns:d1p1="http://schemas.microsoft.com/2003/10/Serialization/Arrays" xmlns="" /><_layerMixingFilterSurrogates xmlns="" /><_mediaSurrogates xmlns="" /><_selectedTimingProviderSurrogate xmlns=""><ProviderType i:nil="true" /><SourceName i:nil="true" /></_selectedTimingProviderSurrogate><DefaultPlaybackEndTime i:nil="true" /><DefaultPlaybackStartTime>PT0S</DefaultPlaybackStartTime><DefaultRowHeight>16</DefaultRowHeight><DefaultSplitterDistance>0</DefaultSplitterDistance><MarkCollections /><TimePerPixel>PT0.0210771S</TimePerPixel><VisibleTimeStart>PT0S</VisibleTimeStart></TimedSequenceData>'

	# writing with 'w' first to wipe existing file
	# using 'a' next to avoid out of memory errors when doing huge countdowns (1 hour caused problems in original script...prob not issue now)
	with open(out_file, 'w') as f:
		f.write(header + '\n')
					
	with open(out_file, 'a') as f:
		for x in any_types:
			f.write(x + '\n')
		f.write('</_dataModels><_effectNodeSurrogates xmlns="">\n')
		for x in effects:
			f.write(x + '\n')
		f.write(footer)

				
if __name__ == '__main__':
	# test_node_on_list()
	main(sys.argv[1:])