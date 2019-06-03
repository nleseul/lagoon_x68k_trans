import text_util

init_operations = {
    0x00: {'length': 0},
    0x01: {'length': 1},
    0x02: {'length': 1},
    0x03: {'length': 1},
    0x04: {'length': 1},
    0x05: {'length': 4},
    0x06: {'length': 7,     'ref_pos': [5]},    # Character info
    0x07: {'length': 16},                       # Might be exits?
    0x08: {'length': 17,    'ref_pos': [15]},   # Shop
    0x09: {'length': 5,     'ref_pos': [3]},    # Door?
    0x0a: {'length': 4},
    0x10: {'length': 2},                        # I think it's just an uncontrolled jump to a location?
    0x16: {'length': 1},                        # Initializes area number
    0x17: {'length': 1},
    0x19: {'length': 1},
    0x1b: {'length': 3},
    0x1c: {'length': 1},                        # Terminator, apparently?
    0x1d: {'length': 4,     'ref_pos': [2]},    # Looks like a map location and a reference?
    0x25: {'length': 4},
    0x26: {'length': 3},
    0x28: {'length': 2,     'ref_pos': [0]}     # Something about bosses?
}

event_operations = {
    0x04: {'length': 1},
    0x06: {'length': 7,     'ref_pos': [5]},
    0x0a: {'length': 4,     'ref_pos': [2]},    # Check event flag?
    0x0b: {'length': 4,     'ref_pos': [2]},
    0x0c: {'length': 4,     'ref_pos': [2]},    # Check for item?
    0x0e: {'length': 2},                        # Set event flag?
    0x11: {'length': 1},
    0x12: {'length': 1},
    0x13: {'length': 1},                        # Give item?
    0x14: {'length': 1},                        # Give item?
    0x15: {'length': 4,     'ref_pos': [0, 2]}, # Sets up a yes/no choice?
    0x18: {'length': 1},                        # Might be a terminator? Don't know.
    0x1a: {'length': 4,     'ref_pos': [1]},    # Sets portrait?
    0x1b: {'length': 3,     'ref_pos': [1]},    # Check for item?
    0x1c: {'length': 1},                        # Also terminator here?
    0x1e: {'length': 4,     'ref_pos': [1]},
    0x1f: {'length': 16},                       # Warp?
    0x20: {'length': 2,     'ref_pos': [0]},
    0x21: {'length': 9,     'ref_pos': [4], 'blob_ref_pos': 6}, # Gives an NPC a path to walk
    0x23: {'length': 1},
    0x27: {'length': 2},
    0x28: {'length': 2,     'ref_pos': [0]},
    0x29: {'length': 4,     'ref_pos': [0]}     # Rewrites a byte in the IVENT data
}

def unpack_ivent(reader):
    init = []
    events = []
    text_table = []
    blob_table = []

    pending_offsets = []
    offset_map = {}

    while True:
        pos = reader.tell()
        op_code_bytes = reader.read(1)
        if op_code_bytes is None:
            break

        op_code = op_code_bytes[0]

        if op_code not in init_operations:
                raise Exception('Unknown init opcode {0:02x} at address {1:04x}!'.format(op_code, pos))

        length = init_operations[op_code]['length']
        content = reader.read(length)

        record = {'op': op_code, 'orig_address': pos, 'content': content.hex()}

        if 'ref_pos' in init_operations[op_code]:
            record['orig_ref_offsets'] = []
            for ref_pos in init_operations[op_code]['ref_pos']:
                record['orig_ref_offsets'].append(int.from_bytes(content[ref_pos:ref_pos+2], byteorder='big'))

        init.append(record)
        if 'orig_ref_offsets' in record:
            pending_offsets += record['orig_ref_offsets']

        if op_code == 0x1c:
            break

    while len(pending_offsets) > 0:
        current_offset = pending_offsets.pop(0)

        if current_offset in offset_map:
            continue

        reader.seek(current_offset)

        while True:
            pos = reader.tell()
            op_code_bytes = reader.read(1)
            if op_code_bytes is None or len(op_code_bytes) == 0:
                break
            op_code = op_code_bytes[0]

            if pos in offset_map:
                # I think this is okay; it just means the data used by a couple of references overlaps some.
                # We've already processed this and subsequent events, so stop.
                break
            offset_map[pos] = len(events)

            event = {'op': op_code, 'orig_address': pos}

            if op_code == 0x00:
                # Terminator; no further decoration required.
                pass
            elif op_code == 0x70:
                text = text_util.decode_japanese(reader)

                event['text_id'] = len(text_table)
                text_table.append({'id': event['text_id'], 'orig_text': text, 'new_text': "Text {0}".format(event['text_id'])})
            else:
                if op_code not in event_operations:
                    raise Exception('Unknown event opcode {0:02x} at address {1:04x}!'.format(op_code, pos))

                length = event_operations[op_code]['length']

                content = reader.read(length)
                event['content'] = content.hex()

                if 'ref_pos' in event_operations[op_code]:
                    event['orig_ref_offsets'] = []
                    for ref_pos in event_operations[op_code]['ref_pos']:
                        event['orig_ref_offsets'].append(int.from_bytes(content[ref_pos:ref_pos+2], byteorder='big'))

                if 'blob_ref_pos' in event_operations[op_code]:
                    blob_ref_pos = event_operations[op_code]['blob_ref_pos']
                    blob_offset = int.from_bytes(content[blob_ref_pos:blob_ref_pos+2], byteorder='big')
                    event['blob_id'] = len(blob_table)
                    blob_table.append({'id': event['blob_id'], 'op': op_code, 'orig_offset': blob_offset})

            events.append(event)
            if 'orig_ref_offsets' in event:
                pending_offsets += event['orig_ref_offsets']

            if op_code == 0x00 or op_code == 0x1c:
                break


    next_id = 0

    for init_event in init:
        if 'orig_ref_offsets' in init_event:
            init_event['ref_ids'] = []
            for orig_ref_offset in init_event['orig_ref_offsets']:
                ref_target_index = offset_map[orig_ref_offset]
                if 'id' not in events[ref_target_index]:
                    events[ref_target_index]['id'] = next_id
                    next_id += 1
                init_event['ref_ids'].append(events[ref_target_index]['id'])

    for event in events:
        if 'orig_ref_offsets' in event:
            event['ref_ids'] = []
            for orig_ref_offset in event['orig_ref_offsets']:
                ref_target_index = offset_map[orig_ref_offset]
                if 'id' not in events[ref_target_index]:
                    events[ref_target_index]['id'] = next_id
                    next_id += 1
                event['ref_ids'].append(events[ref_target_index]['id'])

    events.sort(key=lambda e: e['orig_address'])

    for blob in blob_table:
        if blob['op'] == 0x21:
            reader.seek(blob['orig_offset'])
            blob_data = bytearray()

            while True:
                record = reader.read(2)
                if record is None or len(record) < 2:
                    break
                blob_data += record
                if record[1] == 00:
                    break
            blob['content'] = blob_data.hex()


    return {'init': init, 'events': events, 'text': text_table, 'blobs': blob_table}

def pack_ivent(ivent_data):
    out_data = bytearray()

    text_map = {}
    for text in ivent_data['text']:
        text_map[text['id']] = text['new_text']

    ref_map = {}
    id_map = {}
    blob_id_map = {}

    for init_event in ivent_data['init']:
        pos = len(out_data)
        op_code = init_event['op']

        out_data.append(op_code)
        out_data += bytes.fromhex(init_event['content'])

        if 'ref_pos' in init_operations[op_code]:
            for index, ref_pos in enumerate(init_operations[op_code]['ref_pos']):
                ref_map[pos + 1 + ref_pos] = init_event['ref_ids'][index]

    for event in ivent_data['events']:
        pos = len(out_data)
        op_code = event['op']

        if 'id' in event:
            id_map[event['id']] = pos

        out_data.append(op_code)

        if op_code == 0x70:
            out_data += text_util.encode_english(text_map[event['text_id']])
        elif op_code == 0x00:
            # No content; do nothing.
            pass
        else:
            out_data += bytes.fromhex(event['content'])

            if 'ref_pos' in event_operations[op_code]:
                for index, ref_pos in enumerate(event_operations[op_code]['ref_pos']):
                    ref_map[pos + 1 + ref_pos] = event['ref_ids'][index]

            if 'blob_ref_pos' in event_operations[op_code]:
                blob_id_map[event['blob_id']] = pos + 1 + event_operations[op_code]['blob_ref_pos']

    for ref, id in ref_map.items():
        out_data[ref:ref+2] = id_map[id].to_bytes(2, byteorder='big')

    for blob in ivent_data['blobs']:
        offset = len(out_data)
        ref_offset = blob_id_map[blob['id']]
        out_data += bytes.fromhex(blob['content'])
        out_data[ref_offset:ref_offset + 2] = offset.to_bytes(2, byteorder='big')

    # Footer? What is this for?
    out_data += b'\x18\x00\x00'

    return out_data