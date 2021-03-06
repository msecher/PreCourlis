import unittest
import logging
import configparser
from pkg_resources import resource_filename

LOGGER = logging.getLogger("QGIS")


class TestInit(unittest.TestCase):
    """Test that the plugin init is usable for QGIS.

    Based heavily on the validator class by Alessandro
    Passoti available here:

    http://github.com/qgis/qgis-django/blob/master/qgis-app/
             plugins/validator.py

    """

    def test_read_init(self):
        """Test that the plugin __init__ will validate on plugins.qgis.org."""

        # You should update this list according to the latest in
        # https://github.com/qgis/qgis-django/blob/master/qgis-app/
        #        plugins/validator.py

        required_metadata = [
            "name",
            "description",
            "version",
            "qgisMinimumVersion",
            "email",
            "author",
        ]

        file_path = resource_filename("PreCourlis", "metadata.txt")
        LOGGER.info(file_path)
        metadata = []
        parser = configparser.ConfigParser()
        parser.optionxform = str
        parser.read(file_path)
        message = 'Cannot find a section named "general" in %s' % file_path
        assert parser.has_section("general"), message
        metadata.extend(parser.items("general"))

        for expectation in required_metadata:
            message = 'Cannot find metadata "%s" in metadata source (%s).' % (
                expectation,
                file_path,
            )

            assert expectation in dict(metadata), message
