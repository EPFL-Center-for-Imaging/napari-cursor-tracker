import numpy as np

from napari_cursor_tracker import CursorTracker


# make_napari_viewer is a pytest fixture that returns a napari viewer object
# capsys is a pytest fixture that captures stdout and stderr output streams
def test_cursor_tracker(make_napari_viewer):
    # make viewer and add an image layer and a points layer using the fixture
    viewer = make_napari_viewer()
    test_image_1_name = "Test image 1"
    viewer.add_image(np.random.random((100, 50, 100)), name=test_image_1_name)
    test_points_1_name = "Test points 1"
    viewer.add_points(np.random.random((100, 3)), name=test_points_1_name)

    # create the widget, passing in the viewer
    cursor_tracker_widget = CursorTracker(viewer)

    # Check that example image is in reference drop-down menue
    assert (
        cursor_tracker_widget.reference_layer_combobox.currentText()
        == test_image_1_name
    )

    # Add a second example image
    test_image_2_name = "Test image 2"
    test_image_2_shape = (70, 50, 100)
    viewer.add_image(
        np.random.random(test_image_2_shape), name=test_image_2_name
    )

    # Check that both example images are available in drop-down menu
    assert (
        cursor_tracker_widget.reference_layer_combobox.itemText(0)
        == test_image_1_name
    )
    assert (
        cursor_tracker_widget.reference_layer_combobox.itemText(1)
        == test_image_2_name
    )

    # Delete first example image and check that it is no longer present in the drop-down menu
    del viewer.layers[test_image_1_name]
    assert (
        cursor_tracker_widget.reference_layer_combobox.itemText(0)
        == test_image_2_name
    )
    assert cursor_tracker_widget.reference_layer_combobox.itemText(1) == ""

    # Change name for new layer in text field
    test_points_2_name = "Test points layer"
    cursor_tracker_widget.layer_name_textbox.setText(test_points_2_name)

    # add a new points layer using the widget method
    cursor_tracker_widget.add_new_points_layer()

    # Check that the new points layer was added correctly
    test_points_layer = viewer.layers[test_points_2_name]
    data, props, layer_type = test_points_layer.as_layer_data_tuple()
    assert layer_type == "points"
    assert np.allclose(data.shape[0], test_image_2_shape[0])

    # Check that the pre-plugin and new points layers were added to the active layers drop-down menu
    assert (
        cursor_tracker_widget.active_layer_combobox.itemText(0)
        == test_points_1_name
    )
    assert (
        cursor_tracker_widget.active_layer_combobox.itemText(1)
        == test_points_2_name
    )
