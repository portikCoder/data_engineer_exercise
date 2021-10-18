import os.path
import pathlib
from dataclasses import dataclass
from typing import Union


@dataclass
class Cli:
    pacs_imaging_input_path: Union[str, pathlib.Path]
    ris_rad_opinion_input_path: Union[str, pathlib.Path]
    lims_pathology_input_path: Union[str, pathlib.Path]

    def validate(self):
        at_least_one_input_is_given=True

        input_paths = [getattr(self, x) for x in Cli.__dataclass_fields__]

        if not all(input_paths):
            missing_fields = [x for x in Cli.__dataclass_fields__ if getattr(self,x) is None]
            raise ValueError(f'Take care, the given input path was not given for "{missing_fields}"!') # should have some more user friendly mapping for the namings (and to not to expose the internal state of course...)
        
        if any([os.path.isdir(input_path) for input_path in input_paths]):
            raise NotImplementedError(f'The functionality to handle directories is not implemented in this version!')
        
        if not all([os.path.isfile(input_path) for input_path in input_paths]):
            raise FileNotFoundError(f'Take care, one given input path does not exist: "{input_paths}"!') # should give consistently similar error msg to the others!
