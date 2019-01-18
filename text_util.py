

def decode_japanese(reader):
    lines = []

    str_b = bytearray()
    while True:
        b = reader.read(1)

        if b == b'\x00':
            lines.append(str_b)
            str_b = bytearray()

            if reader.peek()[:1] == b'\x70':
                reader.read(1)
            else:
                break
        else:
            str_b += b

    out = ''
    for line_bytes in lines:
        if len(out) > 0:
            out += '\n'

        if line_bytes[0] > 0x80:
            out += line_bytes.decode('shift-jis')
        else:
            out += (b'\033$B' + line_bytes).decode('iso2022_jp')


    return out

def encode_english(text, enforce_length=None):
    out_data = bytearray()

    for line in text.splitlines():
        if len(out_data) != 0:
            out_data += b'\x00\x70'
        out_data += line.encode('latin-1')
    out_data.append(0x00)

    if enforce_length is not None:
        if len(out_data) > enforce_length:
            print(out_data.hex())
            raise Exception('String \'{0}\' is too long for a space of {1} bytes!'.format(text, enforce_length))
        else:
            out_data = out_data.ljust(enforce_length, b'\x00')

    return out_data