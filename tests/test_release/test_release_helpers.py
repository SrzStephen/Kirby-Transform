from unittest import TestCase
from pathlib import Path
from kirby_transform.release import GitHelpers, VersionHelper, PIPI, is_running_on_travisci
from kirby_transform import __version__
from warnings import warn
import pytest


class TestHelpers(TestCase):

    def test_branch(self):
        git_branch = GitHelpers.get_branch_from_repo(Path(__file__).parent.parent)
        git_cmd = GitHelpers.get_current_branch()
        self.assertTrue(len(git_cmd), 0)
        self.assertIsNotNone(git_cmd)
        if not is_running_on_travisci():
            self.assertEqual(git_cmd, git_branch)


class TestDeployReady(TestCase):
    def test_version_not_in_pipi_already(self):
        # only trigger on main branch
        if VersionHelper.kirb_transform_version_in_repo():
            version_message = f"Kirby transform version {__version__} already exists in PyPi {PIPI}"
            if GitHelpers.get_current_branch() == "main":
                raise ValueError(version_message)

            else:
                warn(version_message)
