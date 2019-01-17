import argparse
import csv
import glob
import os
import sys

from ips_util import Patch

import ivent_util
import text_util

def add_record_checked(patch, address, data, length):
    if len(data) > length:
        raise Exception('Data at {0:x} too long! Actual length={1}, allowed length={2}'.format(address, len(data), length))

    patch.add_record(address, data)

def create_lagoon_x_patch(orig_data):
    BYTES_NOP = b'\x4e\x71'

    patch = Patch()

    # NOP something... probably window rendering.
    patch.add_record(0x06aa, BYTES_NOP * 2)

    # NOP something else
    patch.add_record(0xa4ca, BYTES_NOP * 2)

    # I think this bit renders the glyph to the text buffer?
    patch.add_record(0xa864, BYTES_NOP)   # Increment the destination less.
    patch.add_record(0xa869, b'\x7f')     # Offset to start of next glyph.
    patch.add_record(0xa870, b'\xf7\xff') # Offset back to the top, I think?


    # The code around 0xa650 is counting the number of characters in a string
    # to center it and fit a window around it. We need to count bytes instead
    # of words to be sure we don't miss a terminator. But that also means we
    # need to halve the number of bytes, because the characters are half-width
    # now.
    # So, first, shift the block from 0x8654 to 0x867f back four bytes. That
    # eliminates a double increment, and also makes room for a shift operation.
    patch.add_record(0xa650, orig_data[0xa654:0xa680])

    # By doing that, we bork a bunch of branch instructions in that area, so
    # go back and correct those destinations.
    patch.add_record(0xa63f, b'\x3c')
    patch.add_record(0xa64f, b'\x24')
    patch.add_record(0xa65b, b'\xee')
    patch.add_record(0xa66f, b'\xda')
    patch.add_record(0xa673, b'\xd6')
    patch.add_record(0xa677, b'\xc4')
    patch.add_record(0xa67b, b'\xc0')

    # Now in the four bytes we freed up with that shift, we insert a right-shift
    # that halves the value of the counter ("ASR.W #$01,D1"), followed by a NOP.
    patch.add_record(0xa67c, b'\xe2\x41' + BYTES_NOP)

    # We hack the initialization of that counter to start at 1 instead of zero...
    # that should effectively make the right-shift round the value up instead of down.
    patch.add_record(0xa641, b'\x01')

    # And then there's one more double increment around there that needs to be NOPed.
    patch.add_record(0xa6a8, BYTES_NOP * 2)


    # Control codes!

    # 0x7371 through 0x7379 change the text color. Remapping those to 0xc9 through 0xd2.
    # 0xa6ac does comparisons with it.
    patch.add_record(0xa6ae, b'\x00\xc9')
    patch.add_record(0xa6b4, b'\x00\xd2')
    patch.add_record(0xa6ba, b'\x00\xc9')

    # Same thing when counting characters...
    patch.add_record(0xa652, b'\x00\xc9')
    patch.add_record(0xa658, b'\x00\xd2')

    # Other control codes... I believe these all change portrait animations.
    patch.add_record(0xa6c6, b'\x00\x5c') # 0x7370 is a page break. Remapping it to 0x5c (\)
    patch.add_record(0xa6d8, b'\x00\x40') # 0x2177 (full-width @) remaps to 0x40 (@)
    patch.add_record(0xa6de, b'\x00\x5b') # 0x214e (full-width [) remaps to 0x5b ([}
    patch.add_record(0xa6e6, b'\x00\x5d') # 0x214f (full-width ]) remaps to 0x5d [])
    patch.add_record(0xa6ee, b'\x00\x5e') # 0x215c (full-width +) remaps to 0x5e (^)
    patch.add_record(0xa6f4, b'\x00\x5f') # 0x215d (full-width -) remaps to 0x5f (_)

    # Some of the same when counting characters...
    patch.add_record(0xa65e, b'\x00\x5c')
    patch.add_record(0xa66c, b'\x00\x40')

    # Punctuation marks, used to trigger blink animations on portraits. Uses addresses in the
    # system font graphics for some reason? Order doesn't matter; they all go to the same place.
    patch.add_record(0xa918, b'\x00\xf3\xaa\x20') # Half-width !
    patch.add_record(0xa920, b'\x00\xf3\xaa\xf0') # Half-width .
    patch.add_record(0xa928, b'\x00\xf3\xac\x00') # Half-width ?

    # Same handling of punctuation marks in a different spot... not sure where this is used,
    # but updating it too just to be safe.
    patch.add_record(0xa882, b'\x00\xf3\xaa\x20') # Half-width !
    patch.add_record(0xa88a, b'\x00\xf3\xaa\xf0') # Half-width .
    patch.add_record(0xa892, b'\x00\xf3\xac\x00') # Half-width ?



    # Text in the executable!

    # Instruction to insert the user disk.
    patch.add_record(0x4fdc, text_util.encode_english('If you have a user disk,      \nplease exchange it for the    \nsystem disk. Otherwise, leave \nthe system disk in place.     ', 128))

    # Game over!
    patch.add_record(0x4fc7, text_util.encode_english('Game Over', 20))

    # Pause! What's it doing way down there?
    patch.add_record(0x21504, text_util.encode_english(' Pause ', 15))

    # Disk UI
    patch.add_record(0xc241, text_util.encode_english('Data Load', 19))
    patch.add_record(0xc255, text_util.encode_english('Data Save', 19))
    patch.add_record(0xc269, text_util.encode_english(' 1:', 5))
    patch.add_record(0xc26f, text_util.encode_english(' 2:', 5))
    patch.add_record(0xc275, text_util.encode_english(' 3:', 5))

    # Item received
    patch.add_record(0x7132, text_util.encode_english('was obtained!', 17))

    return patch

def init_csv(ivent_data, filename):
    with open(filename, 'w', encoding='utf8') as out_file:
        writer = csv.writer(out_file, lineterminator='\n')

        for text in ivent_data['text']:
            writer.writerow([text['orig_text'], text['new_text']])

if __name__ == '__main__':
    parser = argparse.ArgumentParser('Main patch build for Lagoon X68000')
    parser.add_argument('src_directory', help='Directory where the original system disk files are contained')
    parser.add_argument('dest_directory', help='Directory where the patched system disk files should be written')

    parser.add_argument('--init-csv', help='Whether initial CSV files containing the text for translation should be created. This will overwrite any files already present.', action='store_true')

    args = parser.parse_args()


    os.makedirs(os.path.join(args.dest_directory, 'IVENT'), exist_ok=True)
    if args.init_csv:
        os.makedirs('csv/ivent', exist_ok=True)

    for path in glob.iglob(os.path.join(args.src_directory, 'IVENT/*.BIN')):
        out_data = None

        base_filename = os.path.splitext(os.path.split(path)[1])[0]
        out_filename = os.path.join(args.dest_directory, 'IVENT/{0}.BIN'.format(base_filename))

        print('{0} ==> {1}... '.format(path, out_filename), end='')

        unpacked_data = None
        with open(path, 'rb') as f:
            unpacked_data = ivent_util.unpack_ivent(f)
        if unpacked_data is None:
            print('Unpacking failed')
            continue

        csv_path = 'csv/ivent/{0}.csv'.format(base_filename)
        if args.init_csv:
            init_csv(unpacked_data, csv_path)

        translation_map = {}
        with open(csv_path, 'r', encoding='utf8') as in_file:
            reader = csv.reader(in_file, lineterminator='\n')
            for row in reader:
                translation_map[row[0]] = row[1]

        for text in unpacked_data['text']:
            text['new_text'] = translation_map[text['orig_text']]

        out_data = ivent_util.pack_ivent(unpacked_data)
        if out_data is None:
            print('Packing failed')
            continue

        with open(out_filename, 'wb') as f:
            f.write(out_data)

        print('OK')

    print('Creating LAGOON.X... ', end='')
    lagoon_x_out_data = bytes()
    with open(os.path.join(args.src_directory, 'LAGOON.X'), 'rb') as f:
        lagoon_x_in_data = f.read()
        lagoon_x_out_data = create_lagoon_x_patch(lagoon_x_in_data).apply(lagoon_x_in_data)
    with open(os.path.join(args.dest_directory, 'LAGOON.X'), 'w+b') as f:
        f.write(lagoon_x_out_data)
    print('OK')