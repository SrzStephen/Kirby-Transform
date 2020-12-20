from pathlib import Path
from pygit2 import Repository
from kirby_transform import __version__
from johnnydep import JohnnyDist
from subprocess import CalledProcessError
from os import popen
# Definitions because I can't remember that
DEV_PIPI = 'https://test-files.pythonhosted.org'
PIPI = 'https://files.pythonhosted.org'


class GitHelpers(object):
    @staticmethod
    def get_branch_from_repo(repo_path: Path) -> str:
        if repo_path.is_file():
            raise ValueError("Expected path to a repo with .git at root")
        repo = Repository(str(repo_path))
        full_repo_name = repo.head.name
        return full_repo_name[len('refs/heads/'):]

    @staticmethod
    def get_current_branch() -> str:
        return popen('git branch --show-current').read().replace('\n', '')


class VersionHelper(object):

    @staticmethod
    def kirb_transform_version_in_repo(index_url=PIPI) -> bool:
        try:
            return __version__ in JohnnyDist(req_string=__package__, index_url=index_url)
        # Get these two errors if the dist doesn't exist
        except CalledProcessError as e:
            return False

    @staticmethod
    def is_using_latest_kirb_transform(index_url=PIPI) -> bool:
        kirb = JohnnyDist(req_string=__package__, index_url=index_url)
        return kirb.version_installed == kirb.version_latest

    @staticmethod
    def version_in_pipi(package_name: str, version: str, pipi_repo: str = PIPI) -> bool:
        return version in JohnnyDist(req_string=package_name, index_url=pipi_repo).versions_available
