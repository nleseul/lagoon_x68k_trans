import argparse
import csv
import glob
import os
import sys

import ivent_util

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

        if args.init_csv:
            init_csv(unpacked_data, 'csv/ivent/{0}.csv'.format(base_filename))


        out_data = ivent_util.pack_ivent(unpacked_data)
        if out_data is None:
            print('Packing failed')
            continue

        with open(out_filename, 'wb') as f:
            f.write(out_data)

        print('OK')