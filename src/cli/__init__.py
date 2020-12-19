from json import load
from operator import itemgetter
from pathlib import Path
from pprint import pprint

from click import argument, group, pass_context
from click_pathlib import Path as ClickPath

from kirby_transform import Processor


@group()
@argument("-f", "--file_path", type=ClickPath(exists=True, file_okay=True, dir_okay=True),
          help="Dir or file to test on")
@pass_context
def cli(ctx, path: Path) -> None:
    def return_data(file: Path) -> dict:
        with open(file) as fp:
            return load(fp)

    if path.is_dir():
        files_to_test = [dict(filename=x.name,
                              data=return_data(x)) for x in (path.glob("*.json"))]
    elif path.is_file():
        files_to_test = [dict(filename=path.name,
                              data=return_data(path))]
    else:
        raise OSError(f" {Path} wasn't a file or dir")  # shouldn't happen

    ctx.files = files_to_test


@cli.command(name="ci_check",
             help="Prints the standard processed output data, will return 1 for failure for use with CI")
@argument('-s', '--supress_output', default=False, type=bool, show_default=True,
          help="Don't print the output if succesful, just return exit code 0")
@pass_context
def stdout(ctx, supress_output: bool) -> None:
    """Return 0 (success) or 1 (failure) for use with CI"""

    for path_name, data in map(itemgetter('filename', 'data'), ctx.files):
        try:
            processed = Processor().process(data)
            if not supress_output:
                pprint(data)
            if len(processed.data) == 0:
                raise ValueError("No data returned")
        except Exception as e:
            (f"Failed on file {path_name} \n {data} \n")
            raise
    exit(0)
