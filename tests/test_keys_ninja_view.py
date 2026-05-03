import sys
from unittest.mock import Mock, MagicMock, patch

sys.modules["pygame"] = MagicMock()


def _make_rect(x, y, w, h):
    """Rect-like mock that supports the attributes _draw_key_object reads."""
    rect = Mock()
    rect.x = x
    rect.y = y
    rect.width = w
    rect.height = h
    rect.left = x
    rect.right = x + w
    rect.top = y
    rect.bottom = y + h
    rect.center = (x + w // 2, y + h // 2)
    rect.move = lambda dx, dy: _make_rect(x + dx, y + dy, w, h)
    return rect


def _build_view_and_run(model, key_obj):
    """Construct KeysNinjaView under mocked pygame and call draw(model)."""
    import game.screens.gameplay.keys_ninja_view as view_mod

    mock_pg = MagicMock()
    mock_font = Mock()
    # Character rect is queried twice (shadow + main). The body rect for the
    # key itself is created via pygame.Rect(...) (handled by side_effect below),
    # so its .bottom reflects the actual computed key body.
    mock_char_rect = _make_rect(20, 20, 40, 40)
    rendered_surf = Mock()
    rendered_surf.get_rect = Mock(return_value=mock_char_rect)
    rendered_surf.set_alpha = Mock()
    mock_font.render.return_value = rendered_surf
    mock_pg.font.SysFont.return_value = mock_font
    mock_pg.font.Font.return_value = mock_font
    mock_pg.draw = Mock()
    mock_surface = Mock()
    mock_surface.copy.return_value = mock_surface
    mock_surface.set_alpha = Mock()
    mock_pg.image.load.return_value = Mock(convert_alpha=Mock(return_value=mock_surface))
    mock_pg.transform.smoothscale.return_value = mock_surface
    mock_pg.Surface.return_value = Mock(fill=Mock(), blit=Mock(), set_alpha=Mock())
    mock_pg.transform.rotozoom.return_value = Mock(get_rect=Mock(return_value=Mock()))
    mock_pg.Rect.side_effect = _make_rect

    screen = Mock()
    screen.get_width.return_value = 800
    screen.get_height.return_value = 600

    keybind_labels = {"left": "A", "right": "D", "up": "W", "down": "S", "space": "SPACE"}

    with patch.object(view_mod, "pygame", mock_pg), \
         patch("game.screens.gameplay.view.pygame", mock_pg), \
         patch("game.screens.gameplay.view.animation_utils"):
        view = view_mod.KeysNinjaView(screen, keybind_labels)
        model.keys = [key_obj]
        view.draw(model, 1.0)

    return mock_pg, rendered_surf


def _default_model():
    model = Mock()
    model.score = 10
    model.lives = 3
    model.combo = 2
    model.max_combo = 4
    model.flash_button = None
    model.flash_state = "normal"
    model.flash_end = 0
    model.state = "playing"
    return model


def _default_key_obj(scale=1.0):
    key_obj = Mock()
    key_obj.scale = scale
    key_obj.is_bomb = False
    key_obj.char = "A"
    key_obj.alpha = 255
    key_obj.rotation = 0
    key_obj.x = 200
    key_obj.y = 200
    return key_obj


def test_keys_ninja_view_draws_without_error():
    mock_pg, _ = _build_view_and_run(_default_model(), _default_key_obj())
    assert mock_pg.draw.rect.called


def test_underline_sits_inside_key_body():
    """The bright underline must be drawn within the key's body rect, not below it."""
    mock_pg, _ = _build_view_and_run(_default_model(), _default_key_obj(scale=1.0))

    # Body rect at scale 1.0: pygame.Rect(5, 5, 60, 60) -> top=5, bottom=65.
    body_top, body_bottom = 5, 65

    underline_calls = [
        c for c in mock_pg.draw.line.call_args_list
        if len(c.args) >= 4 and c.args[1] == (255, 255, 255)
    ]
    assert underline_calls, "expected at least one bright-white underline draw"

    for call in underline_calls:
        start, end = call.args[2], call.args[3]
        # Endpoints share a y so we just check one.
        underline_y = start[1]
        assert start[1] == end[1], "underline should be horizontal"
        assert body_top < underline_y < body_bottom, (
            f"underline y={underline_y} is not inside key body "
            f"({body_top} < y < {body_bottom})"
        )


def test_underline_scales_with_key_object():
    """At a smaller scale the underline still sits inside the (smaller) key body."""
    mock_pg, _ = _build_view_and_run(_default_model(), _default_key_obj(scale=0.5))

    # scale 0.5: key_size = 35, rect = Rect(5, 5, 25, 25) -> bottom=30.
    body_top, body_bottom = 5, 30

    underline_calls = [
        c for c in mock_pg.draw.line.call_args_list
        if len(c.args) >= 4 and c.args[1] == (255, 255, 255)
    ]
    assert underline_calls

    for call in underline_calls:
        underline_y = call.args[2][1]
        assert body_top < underline_y < body_bottom, (
            f"underline y={underline_y} not inside scaled key body "
            f"({body_top} < y < {body_bottom})"
        )


def test_character_is_shifted_upward():
    """The character must render above the surface center to leave room for the underline."""
    _, rendered_surf = _build_view_and_run(_default_model(), _default_key_obj(scale=1.0))

    # surf_size = key_size + 20 = 90 at scale 1.0, so geometric center is 45.
    surf_center = 45
    centers = [
        c.kwargs.get("center")
        for c in rendered_surf.get_rect.call_args_list
        if c.kwargs.get("center") is not None
    ]
    assert centers, "expected get_rect to be called with a center kwarg"

    # Both shadow and main char are anchored above the surface center.
    main_chars = [c for c in centers if c[0] == surf_center]
    assert main_chars, f"expected a centered character render, got {centers}"
    for cx, cy in main_chars:
        assert cy < surf_center, (
            f"character center y={cy} should be shifted above surface center "
            f"{surf_center} so the underline can sit below it"
        )
