"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/stable/plugins/guides.html?#widgets

Replace code below according to your needs.
"""

from typing import TYPE_CHECKING

import napari.utils.events
import numpy as np
from qtpy.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)

if TYPE_CHECKING:
    import napari


class CursorTracker(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer

        self.setLayout(QHBoxLayout())

        self.reference_layer_combobox = QComboBox()
        self.layout().addWidget(self.reference_layer_combobox)
        self.viewer.layers.events.inserted.connect(
            self.add_ref_layer_to_combobox
        )

        self.layer_name_textbox = QLineEdit(self)
        self.layer_name_textbox.setText("Tracked points")

        self.add_btn = QPushButton("Add new layer")
        self.add_btn.clicked.connect(self.add_new_layer)

        self.layout().addWidget(self.add_btn)

        self.active_layer_combobox = QComboBox()
        self.layout().addWidget(self.active_layer_combobox)

        self.viewer.text_overlay.visible = True
        self.viewer.text_overlay.text = "Press 't' to start/stop tracking"

        self.track_cursor_active = False

        @self.viewer.bind_key("t")
        def toggle_tracking(event: napari.utils.events.Event):
            self.current = self.track_cursor_active
            self.track_cursor_active = not self.current
            if self.track_cursor_active:
                self.viewer.dims.events.current_step.connect(self.track_cursor)
            else:
                self.viewer.dims.events.current_step.disconnect(
                    self.track_cursor
                )

    def validate_ref_layer(self, layer):
        """
        Check if the layer with the given name is suitable to be a
        reference layer.
        """
        if layer.as_layer_data_tuple()[2] != "image":
            return False
        if layer.ndim < 3:
            return False
        return True

    def add_ref_layer_to_combobox(self, event):
        layer = event.value
        if self.validate_ref_layer(layer):
            self.reference_layer_combobox.addItem(layer.name)

    def add_new_layer(self):
        name = self.layer_name_textbox.text()
        props = {
            "name": name,
            "size": 3,
            "ndim": 3,
            "edge_width": 0,
            "opacity": 100,
            "face_color": "red",
        }
        data = [[0, 0, 0]] * len(
            self.viewer.layers[
                self.reference_layer_combobox.currentText()
            ].data
        )
        self.viewer.add_points(data=data, **props)
        self.active_layer_combobox.addItem(name)

    def track_cursor(self, event: napari.utils.events.Event):
        """Updates Points layer and depth data based on cursor position."""
        _, x_pos, y_pos = np.array(self.viewer.cursor.position).astype(int)

        current_time_step = self.viewer.dims.current_step[0]

        points_layer = self.viewer.layers[
            self.active_layer_combobox.currentText()
        ]
        points_layer.data[current_time_step] = [
            current_time_step,
            x_pos,
            y_pos,
        ]
        points_layer.refresh()
