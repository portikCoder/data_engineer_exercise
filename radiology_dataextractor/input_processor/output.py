import datetime
import json
from dataclasses import dataclass
from typing import List, Any


@dataclass
class PathologyReport:
    date: datetime.datetime = None
    opinion: str = ''
    # directly non-relevant data
    accession_number: str = ''
    patient_id: str = ''

    @property
    def is_fully_empty(self) -> bool:
        elements = self.__dict__.values()
        return not any(elements)

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)


@dataclass
class DicomStudy:
    patient_id: str = ''
    accession_number: str = ''
    date_of_study: str = ''

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)


@dataclass
class RadiologistReport:
    # all the fields: pat_id, pat_sex, pat_dob, id, outcome_l, outcome_r, date
    side: Any  # what should it be?
    date: Any
    opinion: List[str]
    # directly non-relevant data
    patient_id: str  # it is connecting to the LIMS input
    id: str  # it is connecting to the PACS input
    sex: str
    birth_date: str

    @property
    def relevant_subset_for_analysis(self) -> dict:
        return dict(side=self.side,
                    date=self.date,
                    opinion=self.opinion, )

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)


@dataclass
class MlDigestibleOutput:
    patient_uid: str
    sex: str
    date_of_birth: str
    studies: List[DicomStudy]
    rad: List[RadiologistReport]
    patho: List[PathologyReport]

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)
