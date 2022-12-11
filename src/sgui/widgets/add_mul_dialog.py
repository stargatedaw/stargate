from sgui.sgqt import *
from .playback_widget import playback_widget


def add_mul_dialog(a_update_callback, a_save_callback):
    """ Generic dialog for doing event transforms.  The actual transforms
        are performed by the caller using the event callbacks.  The
        caller should create a list of event objects and their original
        values.
    """
    def ok_handler():
        f_dialog.close()
        f_dialog.retval = True

    def update():
        a_update_callback(f_add_slider.value(), get_mul_val())

    def save(a_val=None):
        a_save_callback()

    def add_changed(a_val):
        update()
        save()

    def get_mul_val():
        f_val = float(f_mul_slider.value())
        f_result = 1.0 + f_val
        return round(f_result, 2)

    def mul_changed(a_val):
        update()
        save()

    f_dialog = QDialog()
    f_dialog.setMinimumWidth(720)
    f_dialog.retval = False
    f_dialog.setWindowTitle("Transform Events")
    vlayout = QVBoxLayout(f_dialog)
    f_layout = QGridLayout()
    vlayout.addLayout(f_layout)

    f_layout.addWidget(QLabel("Add"), 0, 0)
    f_add_slider = QSpinBox()
    f_add_slider.setToolTip(
        'Add this number to each value'
    )
    f_add_slider.setRange(-127, 127)
    f_add_slider.setValue(0)
    f_add_slider.valueChanged.connect(add_changed)
    f_layout.addWidget(f_add_slider, 0, 1)

    f_layout.addWidget(QLabel("Multiply"), 1, 0)
    f_mul_slider = QDoubleSpinBox()
    f_mul_slider.setToolTip('Multiply the values by this number')
    f_mul_slider.setDecimals(2)
    f_mul_slider.setSingleStep(0.01)
    f_mul_slider.setRange(-1.0, 1.0)
    f_mul_slider.setValue(0.0)
    f_mul_slider.valueChanged.connect(mul_changed)
    f_layout.addWidget(f_mul_slider, 1, 1)

    f_playback_widget = playback_widget()
    # f_layout.addWidget(f_playback_widget.play_button, 0, 30, 2, 1)
    # f_layout.addWidget(f_playback_widget.stop_button, 0, 31, 2, 1)

    ok_cancel_layout = QHBoxLayout()
    vlayout.addLayout(ok_cancel_layout)
    f_ok_button = QPushButton("OK")
    ok_cancel_layout.addWidget(f_ok_button)
    f_ok_button.pressed.connect(ok_handler)
    f_cancel_button = QPushButton("Cancel")
    ok_cancel_layout.addWidget(f_cancel_button)
    f_cancel_button.pressed.connect(f_dialog.close)
    f_dialog.move(0, 0)
    f_dialog.exec(center=False)
    return f_dialog.retval

