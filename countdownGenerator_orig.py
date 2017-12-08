'''
This is my original attempt at a countdown generator for a seven-segment display in Vixen Lights.
Technically, it works, but the sequences it generates are highly inefficient because it treats each node uniquely for every second.
This makes ridiculously large sequence files for long countdowns (e.g., 800+ MB for a 1 hour countdown, which Vixen can't really handle).

I rewrote this to be much better and that is found as countdownGenerator.py.
This file is here simply for posterity and as an example of how not to do it.
'''

import os
import re
from uuid import uuid4

duration_secs = 100


def secs_to_min_secs_format(total_secs):
	cur_min = total_secs / 60
	cur_sec = total_secs - cur_min * 60
	return 'PT{}M{}S'.format(str(cur_min), str(cur_sec))
	
def get_any_type(the_id):
	return '<d1p1:anyType xmlns:d2p1="http://schemas.datacontract.org/2004/07/VixenModules.Effect.SetLevel" i:type="d2p1:SetLevelData"><ModuleInstanceId>{}</ModuleInstanceId><ModuleTypeId>{}</ModuleTypeId><TargetPositioning xmlns="http://schemas.datacontract.org/2004/07/VixenModules.Effect.Effect">Strings</TargetPositioning><d2p1:color xmlns:d3p1="http://schemas.datacontract.org/2004/07/Common.Controls.ColorManagement.ColorModels"><d3p1:_b>1</d3p1:_b><d3p1:_g>1</d3p1:_g><d3p1:_r>1</d3p1:_r></d2p1:color><d2p1:level>1</d2p1:level></d1p1:anyType>'.format(the_id, '32cff8e0-5b10-4466-a093-0d232c55aac0')
	
def get_effect(the_id, start_time, node, time_span, type_id):
	return "<EffectNodeSurrogate><InstanceId>{}</InstanceId><StartTime>{}</StartTime><TargetNodes><ChannelNodeReferenceSurrogate><NodeId>{}</NodeId></ChannelNodeReferenceSurrogate></TargetNodes><TimeSpan>{}</TimeSpan><TypeId>{}</TypeId></EffectNodeSurrogate>".format(the_id, start_time, node, time_span, type_id)
	

# read in nodes for seven segment displays
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
	
# create mapping of segments to list of nodes associated
# segment: [min_pixel, max_pixel]
segment_map = {
	1: [1, 15],
	2: [16, 28],
	3: [29, 43],
	4: [44, 56],
	5: [57, 69],
	6: [70, 84],
	7: [85, 97]
}

# create mapping of numbers to generic segments
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


effects = []
any_types = []
total_secs = 0
type_id = '32cff8e0-5b10-4466-a093-0d232c55aac0'
time_span = 'PT0M1S'

for step in range(duration_secs, -1, -1):
	minute = step / 60
	second = step - minute * 60
	
	start_time = secs_to_min_secs_format(total_secs)
	total_secs += 1
	
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

	for seg, value in segs.iteritems():
		if value is not None:
			segments = number_map[value]
			for segment in segments:
				min_pixel = segment_map[segment][0]
				max_pixel = segment_map[segment][1]
				
				for pixel in range(min_pixel, max_pixel+1):
					try:
						node = node_dict[(seg, pixel)]
					except KeyError as e:
						print node_dict
						raise e
					
					the_id = uuid4()
					any_types.append(get_any_type(the_id))
					effects.append(get_effect(the_id, start_time, node, time_span, type_id))

# add in colon
total_duration = secs_to_min_secs_format(total_secs)
for node in colon_node_list:
	the_id = uuid4()
	any_types.append(get_any_type(the_id))
	effects.append(get_effect(the_id, 'PT0S', node, total_duration, type_id))

					
# assemble final file
header = '<?xml version="1.0" encoding="utf-8"?><TimedSequenceData version="4" xmlns:a="http://www.w3.org/2001/XMLSchema" xmlns:i="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://schemas.datacontract.org/2004/07/VixenModules.Sequence.Timed"><ModuleInstanceId xmlns="">{}</ModuleInstanceId><ModuleTypeId xmlns="">296bdba2-9bf3-4bff-a9f2-13efac5c8ecb</ModuleTypeId><Length xmlns="">{}</Length><SequenceLayers xmlns:d1p1="http://schemas.datacontract.org/2004/07/Vixen.Sys.LayerMixing" xmlns=""><d1p1:Layers xmlns:d2p1="http://schemas.microsoft.com/2003/10/Serialization/Arrays"><d2p1:anyType i:type="d1p1:DefaultLayer"><d1p1:Id>{}</d1p1:Id><d1p1:LayerLevel>0</d1p1:LayerLevel><d1p1:LayerName>Default</d1p1:LayerName><d1p1:Type>Default</d1p1:Type></d2p1:anyType></d1p1:Layers><d1p1:_effectLayerMap xmlns:d2p1="http://schemas.microsoft.com/2003/10/Serialization/Arrays" /></SequenceLayers><Version xmlns="">0</Version><_dataModels xmlns:d1p1="http://schemas.microsoft.com/2003/10/Serialization/Arrays" xmlns="">'.format('f7a95a48-5eaa-407b-b194-b8eb079b9977', total_duration, uuid4())

footer = '</_effectNodeSurrogates><_filterNodeSurrogates xmlns="" /><_layerMixingFilterDataModels xmlns:d1p1="http://schemas.microsoft.com/2003/10/Serialization/Arrays" xmlns="" /><_layerMixingFilterSurrogates xmlns="" /><_mediaSurrogates xmlns="" /><_selectedTimingProviderSurrogate xmlns=""><ProviderType i:nil="true" /><SourceName i:nil="true" /></_selectedTimingProviderSurrogate><DefaultPlaybackEndTime i:nil="true" /><DefaultPlaybackStartTime>PT0S</DefaultPlaybackStartTime><DefaultRowHeight>16</DefaultRowHeight><DefaultSplitterDistance>0</DefaultSplitterDistance><MarkCollections /><TimePerPixel>PT0.0210771S</TimePerPixel><VisibleTimeStart>PT0S</VisibleTimeStart></TimedSequenceData>'

# writing with 'w' first to wipe existing file
# using 'a' next to avoid out of memory errors when doing huge countdowns (1 hour caused problems)
out_file = 'countdown.tim'
with open(out_file, 'w') as f:
	f.write(header + '\n')
				
with open(out_file, 'a') as f:
	for x in any_types:
		f.write(x + '\n')
	f.write('</_dataModels><_effectNodeSurrogates xmlns="">\n')
	for x in effects:
		f.write(x + '\n')
	f.write(footer)


	
# <d1p1:anyType xmlns:d2p1="http://schemas.datacontract.org/2004/07/VixenModules.Effect.SetLevel" i:type="d2p1:SetLevelData">
  # <ModuleInstanceId>ac24c18b-b919-4757-a042-e0685cb7de56</ModuleInstanceId>
  # <ModuleTypeId>32cff8e0-5b10-4466-a093-0d232c55aac0</ModuleTypeId>
  # <TargetPositioning xmlns="http://schemas.datacontract.org/2004/07/VixenModules.Effect.Effect">Strings</TargetPositioning>
  # <d2p1:color xmlns:d3p1="http://schemas.datacontract.org/2004/07/Common.Controls.ColorManagement.ColorModels">
	# <d3p1:_b>1</d3p1:_b>
	# <d3p1:_g>1</d3p1:_g>
	# <d3p1:_r>1</d3p1:_r>
  # </d2p1:color>
  # <d2p1:level>1</d2p1:level>
# </d1p1:anyType>
				
# <EffectNodeSurrogate>
      # <InstanceId>f148a5b0-3756-4d48-88ee-9eec4824da9c</InstanceId>
      # <StartTime>PT5M1S</StartTime>
      # <TargetNodes>
        # <ChannelNodeReferenceSurrogate>
          # <NodeId>8ddc9067-cf2f-46cc-a671-017ffbc1f9a4</NodeId>
        # </ChannelNodeReferenceSurrogate>
      # </TargetNodes>
      # <TimeSpan>PT1M</TimeSpan>
      # <TypeId>32cff8e0-5b10-4466-a093-0d232c55aac0</TypeId>
    # </EffectNodeSurrogate>
