import json
import logging
from typing import List

from radiology_dataextractor import cli
from radiology_dataextractor.input_processor.file_processor import \
    distribute_input_data_procession_and_create_data_aggregator, InputAggregator, log_start_finish
from radiology_dataextractor.input_processor.output import MlDigestibleOutput


@log_start_finish('processing input files')
def main():
    aggregator: InputAggregator = distribute_input_data_procession_and_create_data_aggregator(cli)

    output: List[MlDigestibleOutput] = aggregator.aggregate().result
    # of course can fail due to the indexing :D
    logging.debug('output first 2 element: ' + str(output[:2]))

    write_output(output)


@log_start_finish('flushing output json file')
def write_output(output):
    with open('output.ml.json', 'w') as f:
        # tweak data manually into a digestible format
        # i could use non manual ways for this, like pickle (of course, it has its downside)
        f.write(json.dumps([o.to_json() for o in output]))


if __name__ == '__main__':
    main()
    logging.info('*|' * 79)
