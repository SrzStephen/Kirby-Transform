from pathlib import Path
from typing import List, Tuple, Generator
from json import load

from ..schema import CommonInput, NestedInputData
from itertools import combinations


def singleline_open(path: Path) -> dict:
    with open(path) as fp:
        return load(fp)


def get_sucessful_files(data_dir:Path) -> Generator[Tuple[Path, dict], None, None]:
    success_path = data_dir / 'success'
    if not success_path.exists():
        raise NotADirectoryError(f"Didn't find successful testing directory... this shouldn't happen, \n"
                                 f" {success_path.absolute}")

    for item in success_path.glob("*.json"):
        yield item, singleline_open(item)

def input_combinations(report: dict) -> Generator[Tuple[dict, dict], None, None]:
    def iterate_over(d: dict, keys: list) -> Generator[Tuple[dict, list], None, None]:
        for possible_length in range(0, len(keys) + 1):
            for combos in combinations(keys, possible_length):
                data = d.copy()
                for element in combos:
                    if element in data.keys():
                        data.pop(element)
                yield data, combos
        yield d, []

    def iterate_data(list_report: List[dict], keys: list) -> Generator[Tuple[List[dict], dict], None, None]:
        for possible_length in range(0, len(keys) + 1):
            for combos in combinations(keys, possible_length):
                for element in combos:
                    list_rep = list_report.copy()
                    for individual_report in list_rep:
                        if element in individual_report.keys():
                            individual_report.pop(element)
                    yield list_report, combos

    toplevel_optional = [x.name for x in CommonInput().fields.values() if x.required is False]
    datalevel_optional = [x.name for x in NestedInputData().fields.values() if x.required is False]

    for toplevel_missing_report, missing_elements_toplevel in iterate_over(report.copy(), toplevel_optional):
        for data, missing_elements_datalevel in iterate_data(toplevel_missing_report['data'], datalevel_optional):
            return_data = toplevel_missing_report.copy()
            return_data['data'] = data
            yield toplevel_missing_report, dict(missing_toplevel=missing_elements_toplevel,
                                                missing_datalevel=missing_elements_datalevel)
