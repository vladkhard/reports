import pyminizip
import argparse
import os.path
import ConfigParser


def get_out_name(files):
    broker = os.path.basename(files[0].split('@')[0])
    date = os.path.basename(files[0].split('@')[1]).split('-')[:-1]
    operations = set(
        [os.path.basename(f).split('-')[-1].split('.')[0] for f in files]
    )

    out_name = '{}@{}-{}.zip'.format(
        broker, '-'.join(date), '-'.join(operations)
    )
    return out_name


def get_argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-f',
        '--files',
        dest='files',
        nargs='+',
        required=True
    )
    parser.add_argument(
        '-c',
        '--config',
        dest='config',
        required=True
    )
    parser.add_argument(
        '-p',
        '--password',
    )

    parser.add_argument(
        '-z',
        '--zipname',
    )
    return parser


def run():
    parser = get_argument_parser()
    args = parser.parse_args()
    config = ConfigParser.ConfigParser()
    config.read(args.config)
    if args.zipname:
        out_name = args.zipname
    else:
        try:
            out_name = get_out_name(args.files)
        except:
            out_name = '{}.zip'.format(os.path.basename(args.files[0]))
    pyminizip.compress_multiple(
        args.files,
        os.path.join(config.get('out', 'out_dir'), out_name),
        args.password,
        4
    )
