"""
This module is an example of a barebones sample data provider for napari.

It implements the "sample data" specification.
see: https://napari.org/stable/plugins/guides.html?#sample-data

Replace code below according to your needs.
"""

from __future__ import annotations

import numpy


def make_sample_data():
    """Generates an image"""
    # Return list of tuples
    # [(data1, add_image_kwargs1), (data2, add_image_kwargs2)]
    # Check the documentation for more information about the
    # add_image_kwargs
    # https://napari.org/stable/api/napari.Viewer.html#napari.Viewer.add_image
    data = numpy.ones((100, 50, 100), dtype=numpy.uint8) * 128
    for i in range(100):
        x = i
        y = (
            (numpy.sin(x / data.shape[2] * 2 * numpy.pi) + 1)
            / 2
            * data.shape[1]
        )
        y = int(y)
        data[i, y : y + 5, x : x + 5] = 255
    return [(data, {"name": "Cursor tracker sample"})]
