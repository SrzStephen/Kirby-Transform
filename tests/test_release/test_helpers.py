from unittest import TestCase
from pathlib import Path
from kirby_transform.release.helpers import GitHelpers, VersionHelper, PIPI
from kirby_transform import __version__
from warnings import warn

class TestHelpers(TestCase):
    def test_branch(self):
        git_file = GitHelpers.get_branch_from_repo(Path(__file__).parent.parent)
        git_cmd = GitHelpers.get_current_branch()
        self.assertTrue(len(git_cmd), 0)
        self.assertIsNotNone(git_cmd)
        self.assertEqual(git_cmd, git_file)


class TestDeployReady(TestCase):
    def test_version_not_in_pipi_already(self):
        # only trigger on main branch
        if VersionHelper.kirb_transform_version_in_repo():
            version_message = f"Kirby transform version {__version__} already exists in PyPi {PIPI}"
            if GitHelpers.get_current_branch() == "main":
                raise ValueError(version_message)
            else:
                warn(version_message)
