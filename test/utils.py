from qgis.core import (
    QgsProject,
    QgsVectorFileWriter,
    QgsVectorLayer,
)


# functools.cached_property in Python 3.8
class cached_property(object):
    def __call__(self, fget, doc=None):
        self.fget = fget
        self.__doc__ = doc or fget.__doc__
        self.__name__ = fget.__name__
        self.__module__ = fget.__module__
        return self

    def __get__(self, inst, owner):
        try:
            value = inst._cache[self.__name__]
        except (KeyError, AttributeError):
            value = self.fget(inst)
            try:
                cache = inst._cache
            except AttributeError:
                cache = inst._cache = {}
            cache[self.__name__] = value
        return value


def save_as_gml(layer, path):
    transform_context = QgsProject.instance().transformContext()
    save_options = QgsVectorFileWriter.SaveVectorOptions()
    save_options.driverName = QgsVectorFileWriter.driverForExtension("gml")
    save_options.fileEncoding = "UTF-8"
    QgsVectorFileWriter.writeAsVectorFormatV2(
        layer,
        path,
        transform_context,
        save_options,
    )
    output = QgsVectorLayer(path, "output", "ogr")
    assert output.isValid()
    return output
