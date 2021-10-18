import abc
import collections
import datetime
import functools
import json
import logging
import pathlib
import random
import re
from abc import ABC
from typing import List, IO, Any, Dict

from radiology_dataextractor import Cli
from radiology_dataextractor.input_processor.output import MlDigestibleOutput, DicomStudy, RadiologistReport, \
    PathologyReport


# this should go into a util.py
def log_start_finish(jobdone_msg=''):
    """
    log('Start <your-msg>')
    your_func()
    log('Finished <your-msg>')
    """

    def decor(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logging.info(f'Start {jobdone_msg}')
            res = func(*args, **kwargs)
            logging.info(f'Finished {jobdone_msg}')
            return res

        return wrapper

    return decor


# if we would get more inputs, definitely we have a better structure for it
class InputProcessor(ABC):
    def __init__(self, file_path: pathlib.Path, directory_path: pathlib.Path = None):
        self.file_path = file_path
        self.directory_path = directory_path # could have been used
        self.result: Dict[str, Any] = collections.defaultdict(list)

    @log_start_finish
    @abc.abstractmethod
    def process(self): ...

    # it is good that we can see both the types and manipulate if we want before giving back
    @abc.abstractmethod
    def return_result(self) -> Dict[str, Any]: ...


class RisInputProcessor(InputProcessor):
    @property
    def return_result(self) -> Dict[str, List[RadiologistReport]]:
        return self.result

    @log_start_finish('RIS input procession')
    def process(self):
        with open(self.file_path, 'r') as f:
            # while this is not at all a robust process, works in case all the inputs have the same structure
            #  (which is not a good way to think); as an alternative we could use pandas or something similar,
            #   which guarantees that in any order could be the columns -- of course if it could happen, otherwise it is
            #   just an overhead, to use pandas or any other framework yet...

            # skip the header
            next(f)
            for line in f:
                elements = line.strip().split(',')
                patient_id = elements[0]
                self.result[patient_id].append(RadiologistReport(side=None, date=elements[-1],
                                                                 opinion=[elements[-3], elements[-2]], id=elements[3],
                                                                 patient_id=patient_id, sex=elements[1],
                                                                 birth_date=elements[2]))
        return self


class PacsInputProcessor(InputProcessor):
    @property
    def return_result(self) -> Dict[str, List[DicomStudy]]:
        return self.result

    @log_start_finish('PACS input procession')
    def process(self):
        with open(self.file_path, 'r') as f:
            for line in f:
                # If time is critical (and in arbitrary amounts it is :D) I would better do a regexp parse, is far mor efficient
                pacs_line = self.process_line(line)

                ds = DicomStudy()
                # not safe, could go wrong easily because of the missing keys or if the Value is not a list as excpected
                ds.patient_id = pacs_line['00100020']['Value'][0]
                ds.accession_number = pacs_line['00080050']['Value'][0]
                ds.date_of_study = pacs_line['00080020']['Value'][0]
                self.result[ds.accession_number].append(ds)
        return self

    @staticmethod
    def process_line(line: str) -> json:
        return json.loads(line)


class LimsInputProcessor(InputProcessor):
    @property
    def return_result(self) -> Dict[str, List[PathologyReport]]:
        return self.result

    @log_start_finish('LIMS input procession')
    def process(self):
        with open(self.file_path, 'r') as f:
            self.process_content(f)
        return self

    def process_content(self, file_reader: IO):
        """Process an HL7 file with the given fpath.

        Returns: an array with all the parsed messages
        """
        pr = PathologyReport()
        for line in file_reader.readlines():
            line = line.rstrip('\n')
            line = line.strip()
            if line[:3] in ['FHS', 'BHS', 'FTS', 'BTS'] or not line:
                continue

            if line[:3] == 'MSH':
                if not pr.is_fully_empty:
                    self.result[pr.patient_id].append(pr)
                pr = PathologyReport()
            else:
                if pr.is_fully_empty and not line:
                    logging.error(
                        'Segment received before message header [%s]',
                        line)
                    continue
                if line:
                    if line[:3] == 'PID':
                        # definitely a regexp candidate ;)
                        pr.patient_id = line[9:45]
                    if line[:3] == 'OBR':
                        # definitely regexp candidates ;)
                        pr.accession_number = line[6:42]
                        # in some cases as the data could miss the `accession_number` attribute, i dont handle the extraction in a robust way
                        # if i would know its structure better, i could prepare for the 'unwanted' cases, as i can see
                        #  that the separators are not always the same quantity (perhaps is due to miss of the info)
                        pr.date = line[46:54]
                    if line[:3] == 'OBX':
                        opinon = re.search(r'(?<=RESDIAG\^Result diagnosis:\|\|).*(?=\^)', line)
                        pr.opinion = opinon.group() if opinon else ''


class InputAggregator:
    def __init__(self):
        self.radiologist_reports: Dict[str, List[RadiologistReport]] = {}
        self.dicom_studies: Dict[str, List[DicomStudy]] = {}
        self.pathology_reports: Dict[str, List[PathologyReport]] = {}
        self.result: List[MlDigestibleOutput] = []

    @log_start_finish('input aggregation')
    def aggregate(self):
        logging.debug(f'len of the dicom studies: {len(self.dicom_studies)}')
        logging.debug(f'len of the pathology_reports: {len(self.pathology_reports)}')

        for patient_id, radiologist_reports in self.radiologist_reports.items():
            mdout = self.extract_info_into_ml_digestible_format(patient_id, radiologist_reports)
            self.result.append(mdout)
        return self

    def extract_info_into_ml_digestible_format(self, patient_id, radiologist_reports) -> MlDigestibleOutput:
        pathology_reports = self.pathology_reports.get(patient_id)
        if radiologist_reports:
            dicom_studies = self.dicom_studies[radiologist_reports[0].id]

            sex = radiologist_reports[0].sex
            birth_date = radiologist_reports[0].birth_date
            formatted_bdate = (datetime.datetime.strptime(birth_date, '%Y%m%d') + datetime.timedelta(
                days=random.randint(-365, 365))).strftime('%Y.%m.%d')
            relevant_rad_reports = [radiologist_report.relevant_subset_for_analysis for radiologist_report in
                                    radiologist_reports]
            mdout = MlDigestibleOutput(patient_uid=self.de_identify_id(patient_id), sex=sex,
                                       date_of_birth=formatted_bdate, studies=dicom_studies,
                                       rad=relevant_rad_reports, patho=pathology_reports)
        else:
            mdout = MlDigestibleOutput(patient_uid=self.de_identify_id(patient_id), sex='',
                                       date_of_birth='', studies=[],
                                       rad=[], patho=pathology_reports)
        return mdout

    @staticmethod
    def de_identify_id(input_id: str) -> str:
        return ''.join(random.sample(input_id, len(input_id)))


@log_start_finish('processing up the given input and setup the data aggregator with them')
def distribute_input_data_procession_and_create_data_aggregator(cli: Cli) -> InputAggregator:
    """
    In a real-world app I'would never do such practice, where you have to list all the types, IF we know that there are more than now
    It can happen that a tool like this one must support 100X types,
     and so depending on the complexity, could be either generics/template functions, or template method design pattern

    To use up the mentioned design pattern benefits, a factory method could add the ease for the creation of the different instances.
    This can be easily achieved by using an identifier for the different input processor classes, like:
        class TypeInputProcessor(InputProcessor):
            id: str = type
        and then iterate over the input types, and associate automatically them based on this identifier (from the input
        can be extracted again - easily).

    We can also enhance the way that the inputs are processed. As long as it was not defined how they are structured, I
     went on a way, that are separated already by their type. Based on my experience this is something usual, but not a must.
    A non usual way of grouping the data is by only date, and therefore could happen that the data is not separated by
     this desired way. This can be solved by 2 easy ways:
        * write an external tool/module which separates the data for us
        * write an input process separator which can be used to explore the input that is being processed and decide on-the-fly
    It depends on the need, how the data is stored, if the input process time is critical in a way (then we should prepare the data),
     etc.

    Also, as we are talking about arbitrary amount of data, we should use separate process/instances for the procession.
     That is why tools like Spark were invented.
    """
    aggregator = InputAggregator()

    if cli.ris_rad_opinion_input_path:
        aggregator.radiologist_reports = RisInputProcessor(cli.ris_rad_opinion_input_path).process().return_result
    if cli.pacs_imaging_input_path:
        aggregator.dicom_studies = PacsInputProcessor(cli.pacs_imaging_input_path).process().return_result
    if cli.lims_pathology_input_path:
        aggregator.pathology_reports = LimsInputProcessor(cli.lims_pathology_input_path).process().return_result
    return aggregator
