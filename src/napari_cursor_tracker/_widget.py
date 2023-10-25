"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/stable/plugins/guides.html?#widgets

Replace code below according to your needs.
"""

from typing import TYPE_CHECKING

import magicgui
import napari.utils.events
import numpy as np
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    import napari


class CursorTracker(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer

        self.reference_layer = magicgui.widgets.create_widget(
            annotation=napari.layers.Image,
            label="Reference image",
        )
        self.viewer.layers.events.inserted.connect(
            self.reference_layer.reset_choices
        )
        self.viewer.layers.events.removed.connect(
            self.reference_layer.reset_choices
        )
        self.reference_layer.native.setToolTip(
            "Select the image layer on which you want to track. It is used to infer the number of time points for the points layer."
        )

        self.layer_name_textbox = QLineEdit(self)
        self.layer_name_textbox.setText("Tracked point")
        self.layer_name_textbox.setToolTip(
            "Name of the points layer that is generated for tracking."
        )

        self.add_btn = QPushButton("Add new layer")
        self.add_btn.clicked.connect(self.add_new_points_layer)
        self.add_btn.setToolTip(
            "Add points layer for tracking. The name is taken form the 'Name of tracked point' field above and the number of time points is equal to the number of time points of the layer selected in the 'Reference image' drop-down menu."
        )
        self.auto_play_checkbox = QCheckBox(
            "Auto play when tracking is started"
        )
        self.auto_play_checkbox.setToolTip(
            "Automatically start playing the images when the tracking is started."
        )
        self.auto_play_checkbox.setChecked(True)

        self.active_layer = magicgui.widgets.create_widget(
            annotation=napari.layers.Points,
            label="Active layer",
        )
        self.viewer.layers.events.inserted.connect(
            self.active_layer.reset_choices
        )
        self.viewer.layers.events.removed.connect(
            self.active_layer.reset_choices
        )
        self.active_layer.native.setToolTip(
            "Points layer which is modified during tracking."
        )

        self.playback_param_groupbox = QGroupBox("Playback parameters")
        self.playback_param_layout = QGridLayout()
        self.playback_param_groupbox.setLayout(self.playback_param_layout)

        settings = napari.settings.get_settings()
        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(0, 1000)
        self.fps_spinbox.setSingleStep(1)
        self.fps_spinbox.setValue(10)
        settings.application.playback_fps = 10
        self.fps_spinbox.valueChanged.connect(self.update_fps)

        self.loop_combobox = QComboBox()
        self.loop_combobox.addItems(["once", "loop", "back_and_forth"])
        settings.application.playback_mode = "once"
        self.loop_combobox.currentTextChanged.connect(self.update_loop_mode)

        self.direction_combobox = QComboBox()
        self.direction_combobox.addItems(["forward", "reverse"])
        self.direction_combobox.currentTextChanged.connect(
            self.update_direction
        )

        self.playback_param_layout.addWidget(QLabel("Frames per second"))
        self.playback_param_layout.addWidget(self.fps_spinbox)
        self.playback_param_layout.addWidget(QLabel("Loop mode"))
        self.playback_param_layout.addWidget(self.loop_combobox)
        self.playback_param_layout.addWidget(QLabel("Direction"))
        self.playback_param_layout.addWidget(self.direction_combobox)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(QLabel("Reference image"))
        self.layout().addWidget(self.reference_layer.native)
        self.layout().addWidget(QLabel("Name of tracked point"))
        self.layout().addWidget(self.layer_name_textbox)
        self.layout().addWidget(self.add_btn)
        self.layout().addWidget(QLabel("Active layer"))
        self.layout().addWidget(self.active_layer.native)
        self.layout().addWidget(self.auto_play_checkbox)
        self.layout().addWidget(self.playback_param_groupbox)

        self.viewer.text_overlay.visible = True
        self.viewer.text_overlay.text = "Press 't' to start/stop tracking"

        self.track_cursor_active = False
        self.previous_step = np.nan

        @self.viewer.bind_key("t")
        def toggle_tracking(event: napari.utils.events.Event):
            self.current = self.track_cursor_active
            self.track_cursor_active = not self.current
            if self.track_cursor_active:
                if self.active_layer.value is None:
                    napari.utils.notifications.show_error(
                        "No active layer has been selected. If you haven't done so yet, create one using the 'Add new layer' button. Then select it as the active layer."
                    )
                    self.track_cursor_active = False
                    return
                self.previous_step = self.viewer.dims.current_step[0]
                self.viewer.dims.events.current_step.connect(self.track_cursor)
                if self.auto_play_checkbox.isChecked():
                    settings = napari.settings.get_settings()
                    fps = settings.application.playback_fps
                    mode = settings.application.playback_mode
                    self.viewer.window.qt_viewer.dims.play(
                        fps=fps,
                        loop_mode=mode,
                    )

            else:
                self.viewer.dims.events.current_step.disconnect(
                    self.track_cursor
                )
                self.viewer.window.qt_viewer.dims.stop()

    def add_new_points_layer(self):
        name = self.layer_name_textbox.text()
        props = {
            "name": name,
            "size": 3,
            "ndim": 3,
            "edge_width": 0,
            "opacity": 100,
            "face_color": "red",
        }
        data = [[0, 0, 0]] * len(self.reference_layer.value.data)
        self.viewer.add_points(data=data, **props)

    def track_cursor(self, event: napari.utils.events.Event):
        """Updates Points layer and depth data based on cursor position."""
        _, x_pos, y_pos = np.array(self.viewer.cursor.position).astype(int)

        points_layer = self.active_layer.value

        step = self.previous_step
        size = points_layer.size[step]

        points_layer.data[step] = [
            step,
            x_pos + size / 2,
            y_pos + size / 2,
        ]
        points_layer.refresh()
        self.previous_step = self.viewer.dims.current_step[0]

    def update_fps(self, fps: float):
        settings = napari.settings.get_settings()
        sign = np.sign(settings.application.playback_fps)
        settings.application.playback_fps = fps * sign

    def update_loop_mode(self, mode: str):
        settings = napari.settings.get_settings()
        settings.application.playback_mode = mode

    def update_direction(self, direction: str):
        settings = napari.settings.get_settings()
        if direction == "reverse":
            settings.application.playback_fps = -1 * np.abs(
                settings.application.playback_fps
            )
        elif direction == "forward":
            settings.application.playback_fps = np.abs(
                settings.application.playback_fps
            )
