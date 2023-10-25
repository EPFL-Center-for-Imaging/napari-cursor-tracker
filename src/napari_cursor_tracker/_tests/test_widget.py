import napari
import numpy as np
import pytest

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
        cursor_tracker_widget.reference_layer.value.name == test_image_1_name
    )

    # Add a second example image
    test_image_2_name = "Test image 2"
    test_image_2_shape = (70, 50, 100)
    viewer.add_image(
        np.random.random(test_image_2_shape), name=test_image_2_name
    )

    # Check that both example images are available in drop-down menu
    assert (
        cursor_tracker_widget.reference_layer.native.itemText(0)
        == test_image_1_name
    )
    assert (
        cursor_tracker_widget.reference_layer.native.itemText(1)
        == test_image_2_name
    )

    # Delete first example image and check that it is no longer present in the drop-down menu
    del viewer.layers[test_image_1_name]
    assert (
        cursor_tracker_widget.reference_layer.native.itemText(0)
        == test_image_2_name
    )
    assert cursor_tracker_widget.reference_layer.native.itemText(1) == ""

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
        cursor_tracker_widget.active_layer.native.itemText(0)
        == test_points_1_name
    )
    assert (
        cursor_tracker_widget.active_layer.native.itemText(1)
        == test_points_2_name
    )


@pytest.fixture(params=[1, 10, 100])
def fps(request):
    return request.param


@pytest.fixture(params=["forward", "reverse"])
def direction(request):
    return request.param


@pytest.fixture(params=["once", "loop", "back_and_forth"])
def loop_mode(request):
    return request.param


def test_playback_parameter_interface(
    make_napari_viewer, fps, loop_mode, direction
):
    viewer = make_napari_viewer()

    # create the widget, passing in the viewer
    cursor_tracker_widget = CursorTracker(viewer)

    cursor_tracker_widget.fps_spinbox.setValue(fps)
    cursor_tracker_widget.loop_combobox.setCurrentText(loop_mode)
    cursor_tracker_widget.direction_combobox.setCurrentText(direction)

    settings = napari.settings.get_settings()
    assert settings.application.playback_mode == loop_mode
    assert np.abs(settings.application.playback_fps) == fps
    if direction == "forward":
        assert np.sign(settings.application.playback_fps) == 1
    else:
        assert np.sign(settings.application.playback_fps) == -1
