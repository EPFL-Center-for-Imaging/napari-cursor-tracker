import numpy as np

from napari_cursor_tracker import make_sample_data


def test_sample_data_generation():
    returned_value = make_sample_data()
    assert isinstance(returned_value, list)
    for layer_data_tuple in returned_value:
        # Check that it is a layer data tuple
        assert isinstance(layer_data_tuple, tuple)
        assert len(layer_data_tuple) == 2
        assert isinstance(layer_data_tuple[0], np.ndarray)
        assert isinstance(layer_data_tuple[1], dict)

        # Check that the data is 3D and has 2 unique values
        data = layer_data_tuple[0]
        assert data.ndim == 3
        assert len(np.unique(data)) == 2
