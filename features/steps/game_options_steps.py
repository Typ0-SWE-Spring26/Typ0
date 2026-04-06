"""Given/When/Then steps for game_options.feature."""
from behave import given, when, then


# ---------------------------------------------------------------------------
# Given — keybind manager setup
# ---------------------------------------------------------------------------

@given('a fresh keybind manager')
def step_fresh_keybinds(ctx):
    from game.core.keybinds import KeybindManager
    ctx.keybinds = KeybindManager()


# ---------------------------------------------------------------------------
# Given/When — keybind actions (registered for both so either keyword works)
# ---------------------------------------------------------------------------

def _enable_inverted(ctx):
    ctx.keybinds.inverted = True

def _disable_inverted(ctx):
    ctx.keybinds.inverted = False

given('inverted controls are enabled')(_enable_inverted)
when('inverted controls are enabled')(_enable_inverted)
given('inverted controls are disabled')(_disable_inverted)
when('inverted controls are disabled')(_disable_inverted)


def _toggle_inverted(ctx):
    ctx.keybinds.toggle_invert()

given('inverted controls are toggled')(_toggle_inverted)
when('inverted controls are toggled')(_toggle_inverted)


# ---------------------------------------------------------------------------
# Then — keybind assertions
#
# pygame is mocked in the test environment so pygame.key.name() returns a
# MagicMock, not a real string.  Instead we compare key constants directly
# against KeybindManager's own maps, which use those same (mocked) constants.
# ---------------------------------------------------------------------------

def _key_name_to_const(key_name):
    """Resolve a human-readable key name to the pygame constant used by
    KeybindManager, without calling pygame.key.name().

    We use KeybindManager's DEFAULT_MAP as the canonical source of truth:
      'a'     → DEFAULT_MAP['left']   (K_a)
      'd'     → DEFAULT_MAP['right']  (K_d)
      'w'     → DEFAULT_MAP['up']     (K_w)
      's'     → DEFAULT_MAP['down']   (K_s)
      'space' → DEFAULT_MAP['space']  (K_SPACE)
    """
    from game.core.keybinds import KeybindManager
    _name_map = {
        'a':     KeybindManager.DEFAULT_MAP['left'],
        'd':     KeybindManager.DEFAULT_MAP['right'],
        'w':     KeybindManager.DEFAULT_MAP['up'],
        's':     KeybindManager.DEFAULT_MAP['down'],
        'space': KeybindManager.DEFAULT_MAP['space'],
    }
    assert key_name in _name_map, f'Unknown key name "{key_name}" in step'
    return _name_map[key_name]


@then('the "{action}" action should be mapped to key "{key_name}"')
def step_action_mapped_to_key(ctx, action, key_name):
    mapping = ctx.keybinds.button_keys
    assert action in mapping, f'Action "{action}" not found in keybind map'
    expected_const = _key_name_to_const(key_name)
    actual_const   = mapping[action]
    assert actual_const == expected_const, (
        f'Action "{action}": expected key "{key_name}" constant, '
        f'got a different constant'
    )


# ---------------------------------------------------------------------------
# Then — Simon game option threshold assertions (used in game_options.feature)
# ---------------------------------------------------------------------------

@then('the Simon flash time should be greater than {threshold:d}')
def step_simon_flash_gt(ctx, threshold):
    assert ctx.model._flash_time > threshold, (
        f'Expected _flash_time > {threshold}, got {ctx.model._flash_time}'
    )


@then('the Simon flash time should be less than {threshold:d}')
def step_simon_flash_lt(ctx, threshold):
    assert ctx.model._flash_time < threshold, (
        f'Expected _flash_time < {threshold}, got {ctx.model._flash_time}'
    )


@then('the Simon timer limit should be greater than {threshold:d}')
def step_simon_timer_gt(ctx, threshold):
    assert ctx.model.timer_limit > threshold, (
        f'Expected timer_limit > {threshold}, got {ctx.model.timer_limit}'
    )


@then('the Simon timer limit should be less than {threshold:d}')
def step_simon_timer_lt(ctx, threshold):
    assert ctx.model.timer_limit < threshold, (
        f'Expected timer_limit < {threshold}, got {ctx.model.timer_limit}'
    )


# ---------------------------------------------------------------------------
# Then — Bop-It game option threshold assertions
# ---------------------------------------------------------------------------

@then('the Bop-It base time should be greater than {threshold:d}')
def step_bopit_base_gt(ctx, threshold):
    assert ctx.bopit_model.BASE_TIME > threshold, (
        f'Expected BASE_TIME > {threshold}, got {ctx.bopit_model.BASE_TIME}'
    )


@then('the Bop-It base time should be less than {threshold:d}')
def step_bopit_base_lt(ctx, threshold):
    assert ctx.bopit_model.BASE_TIME < threshold, (
        f'Expected BASE_TIME < {threshold}, got {ctx.bopit_model.BASE_TIME}'
    )


@then('the Bop-It base time should equal {value:d}')
def step_bopit_base_eq(ctx, value):
    assert ctx.bopit_model.BASE_TIME == value, (
        f'Expected BASE_TIME {value}, got {ctx.bopit_model.BASE_TIME}'
    )
