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
    QCheckBox,
    QComboBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    import napari


class CursorTracker(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer

        self.reference_layer_combobox = QComboBox()
        for layer in self.viewer.layers:
            self.add_ref_layer_to_combobox(layer)
        self.reference_layer_combobox.setToolTip(
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

        self.active_layer_combobox = QComboBox()
        for layer in self.viewer.layers:
            self.add_active_layer_to_combobox(layer)
        self.active_layer_combobox.setToolTip(
            "Points layer which is modified during tracking."
        )

        self.viewer.layers.events.inserted.connect(self._on_inserted_layer)
        self.viewer.layers.events.removed.connect(self._on_removed_layer)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(QLabel("Reference image"))
        self.layout().addWidget(self.reference_layer_combobox)
        self.layout().addWidget(QLabel("Name of tracked point"))
        self.layout().addWidget(self.layer_name_textbox)
        self.layout().addWidget(self.add_btn)
        self.layout().addWidget(QLabel("Active layer"))
        self.layout().addWidget(self.active_layer_combobox)
        self.layout().addWidget(self.auto_play_checkbox)

        self.viewer.text_overlay.visible = True
        self.viewer.text_overlay.text = "Press 't' to start/stop tracking"

        self.track_cursor_active = False

        @self.viewer.bind_key("t")
        def toggle_tracking(event: napari.utils.events.Event):
            self.current = self.track_cursor_active
            self.track_cursor_active = not self.current
            if self.track_cursor_active:
                self.viewer.dims.events.current_step.connect(self.track_cursor)
                if self.auto_play_checkbox.isChecked():
                    self.viewer.window.qt_viewer.dims.play()

            else:
                self.viewer.dims.events.current_step.disconnect(
                    self.track_cursor
                )
                self.viewer.window.qt_viewer.dims.stop()

    def _on_inserted_layer(self, event):
        layer = event.value
        self.add_ref_layer_to_combobox(layer)
        self.add_active_layer_to_combobox(layer)

    def _on_removed_layer(self, event):
        layer = event.value
        self.remove_ref_layer_from_combobox(layer)
        self.remove_active_layer_from_combobox(layer)

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

    def add_ref_layer_to_combobox(self, layer):
        if self.validate_ref_layer(layer):
            self.reference_layer_combobox.addItem(layer.name)

    def remove_ref_layer_from_combobox(self, layer):
        for index in range(self.reference_layer_combobox.count()):
            if layer.name == self.reference_layer_combobox.itemText(index):
                self.reference_layer_combobox.removeItem(index)

    def validate_active_layer(self, layer):
        """
        Check if the layer with the given name is suitable to be a
        an active layer.
        """
        if layer.as_layer_data_tuple()[2] != "points":
            return False
        if layer.ndim < 3:
            return False
        return True

    def add_active_layer_to_combobox(self, layer):
        if self.validate_active_layer(layer):
            self.active_layer_combobox.addItem(layer.name)

    def remove_active_layer_from_combobox(self, layer):
        for index in range(self.active_layer_combobox.count()):
            if layer.name == self.active_layer_combobox.itemText(index):
                self.active_layer_combobox.removeItem(index)

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
        data = [[0, 0, 0]] * len(
            self.viewer.layers[
                self.reference_layer_combobox.currentText()
            ].data
        )
        self.viewer.add_points(data=data, **props)

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
