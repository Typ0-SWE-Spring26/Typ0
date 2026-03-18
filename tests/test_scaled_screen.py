import importlib
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest


@pytest.fixture
def scaled_module(monkeypatch):
    class FakeSurface:
        def __init__(self, size):
            self._size = size

        def get_size(self):
            return self._size

    fake_pg = SimpleNamespace()
    fake_pg.Surface = FakeSurface
    fake_pg.transform = SimpleNamespace(smoothscale=Mock(return_value="scaled-surface"))
    fake_pg.display = SimpleNamespace(flip=Mock())
    fake_pg.event = SimpleNamespace(Event=lambda event_type, **attrs: SimpleNamespace(type=event_type, **attrs))

    monkeypatch.setitem(sys.modules, "pygame", fake_pg)

    module = importlib.import_module("game.utils.scaled_screen")
    module = importlib.reload(module)
    return module, fake_pg


def test_update_scaling_uses_min_axis_ratio(scaled_module):
    module, _ = scaled_module
    window = Mock()
    window.get_size.return_value = (1600, 900)

    screen = module.ScaledScreen(window)

    assert screen.scale == 1.5
    assert screen.scaled_size == (1200, 900)
    assert screen.offset_x == 200
    assert screen.offset_y == 0


def test_present_fills_letterbox_blits_scaled_and_flips(scaled_module):
    module, fake_pg = scaled_module
    window = Mock()
    window.get_size.return_value = (800, 600)

    screen = module.ScaledScreen(window)
    screen.present()

    window.fill.assert_called_once_with((0, 0, 0))
    fake_pg.transform.smoothscale.assert_called_once_with(screen, (800, 600))
    window.blit.assert_called_once_with("scaled-surface", (0, 0))
    fake_pg.display.flip.assert_called_once()


def test_map_mouse_accounts_for_offset_and_scale(scaled_module):
    module, _ = scaled_module
    window = Mock()
    window.get_size.return_value = (1600, 900)

    screen = module.ScaledScreen(window)
    mapped = screen.map_mouse((500, 450))

    assert mapped == (200, 300)


def test_map_mouse_clamps_when_point_is_in_letterbox(scaled_module):
    module, _ = scaled_module
    window = Mock()
    window.get_size.return_value = (1600, 900)

    screen = module.ScaledScreen(window)

    assert screen.map_mouse((0, 0)) == (0, 0)
    assert screen.map_mouse((5000, 5000)) == (module.VIRTUAL_WIDTH - 1, module.VIRTUAL_HEIGHT - 1)


def test_remap_event_converts_mouse_pos(scaled_module):
    module, _ = scaled_module
    window = Mock()
    window.get_size.return_value = (1600, 900)

    screen = module.ScaledScreen(window)
    mouse_event = SimpleNamespace(type=123, pos=(500, 450), button=1)

    remapped = screen.remap_event(mouse_event)

    assert remapped.type == 123
    assert remapped.pos == (200, 300)
    assert remapped.button == 1


def test_remap_event_returns_original_when_no_pos(scaled_module):
    module, _ = scaled_module
    window = Mock()
    window.get_size.return_value = (800, 600)

    screen = module.ScaledScreen(window)
    key_event = SimpleNamespace(type=456, key=13)

    remapped = screen.remap_event(key_event)

    assert remapped is key_event


def test_clone_event_keeps_selected_attributes_and_overrides(scaled_module):
    module, _ = scaled_module
    original = SimpleNamespace(type=999, pos=(10, 20), button=1, key=65, extra="ignore")

    cloned = module._clone_event(original, pos=(30, 40))

    assert cloned.type == 999
    assert cloned.pos == (30, 40)
    assert cloned.button == 1
    assert cloned.key == 65
    assert not hasattr(cloned, "extra")
