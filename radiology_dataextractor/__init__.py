import argparse
import logging
import pathlib

from radiology_dataextractor.cli import Cli


def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s:%(levelname)s:%(message)s',
    )
    logging.info('*' * 79)
    logging.info('Logger setup is done')


def setup_cli() -> Cli:
    parser = argparse.ArgumentParser(
        description='Process PACS, RIS, LIMS files. This version can \
        handle different input-types separated only by hand.')

    parser.add_argument(
        '-p',
        '--pacs',
        type=pathlib.Path,
        help='path with the input "Picture Archiving and Communication System" file or directory'
    )
    parser.add_argument(
        '-r',
        '--ris',
        type=pathlib.Path,
        help='path with the input "Radiology Information System" file or directory'
    )
    parser.add_argument(
        '-l',
        '--lims',
        type=pathlib.Path,
        help='path with the input "Laboratory Information Management System" file or directory'
    )
    args = parser.parse_args()
    return Cli(args.pacs, args.ris, args.lims)


setup_logging()

cli = setup_cli()
cli.validate()
