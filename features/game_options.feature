Feature: Game options (inverted controls and difficulty)
  Before starting a game, the player configures options.
  These are wired directly into the game: inverted controls flip the key
  mapping used by the keybind manager, and difficulty is passed into the
  game model that controls all timing.

  # ── Inverted controls ─────────────────────────────────────────────────────

  Scenario: Controls are normal by default
    Given a fresh keybind manager
    Then the "left" action should be mapped to key "a"
    And the "right" action should be mapped to key "d"
    And the "up" action should be mapped to key "w"
    And the "down" action should be mapped to key "s"

  Scenario: Enabling inverted controls swaps left and right
    Given a fresh keybind manager
    When inverted controls are enabled
    Then the "left" action should be mapped to key "d"
    And the "right" action should be mapped to key "a"

  Scenario: Enabling inverted controls swaps up and down
    Given a fresh keybind manager
    When inverted controls are enabled
    Then the "up" action should be mapped to key "s"
    And the "down" action should be mapped to key "w"

  Scenario: Space is unaffected by inversion
    Given a fresh keybind manager
    When inverted controls are enabled
    Then the "space" action should be mapped to key "space"

  Scenario: Toggling inverted controls twice restores the original mapping
    Given a fresh keybind manager
    When inverted controls are toggled
    And inverted controls are toggled
    Then the "left" action should be mapped to key "a"
    And the "right" action should be mapped to key "d"

  Scenario: Disabling inverted controls restores the original mapping
    Given a fresh keybind manager
    And inverted controls are enabled
    When inverted controls are disabled
    Then the "left" action should be mapped to key "a"
    And the "right" action should be mapped to key "d"

  # ── Difficulty wired into Simon ────────────────────────────────────────────

  Scenario: Choosing Easy difficulty makes Simon sequences display more slowly
    Given a fresh Simon game model with "easy" difficulty
    Then the Simon flash time should be greater than 500

  Scenario: Choosing Hard difficulty makes Simon sequences display quickly
    Given a fresh Simon game model with "hard" difficulty
    Then the Simon flash time should be less than 500

  Scenario: Choosing Easy difficulty gives the player more input time
    Given a fresh Simon game model with "easy" difficulty
    Then the Simon timer limit should be greater than 5000

  Scenario: Choosing Hard difficulty gives the player less input time
    Given a fresh Simon game model with "hard" difficulty
    Then the Simon timer limit should be less than 5000

  # ── Difficulty wired into Bop-It ───────────────────────────────────────────

  Scenario: Choosing Easy difficulty gives Bop-It more starting time
    Given a fresh Bop-It model with "easy" difficulty
    Then the Bop-It base time should be greater than 5000

  Scenario: Choosing Hard difficulty gives Bop-It less starting time
    Given a fresh Bop-It model with "hard" difficulty
    Then the Bop-It base time should be less than 5000

  Scenario: Choosing Normal difficulty leaves Bop-It at the original base time
    Given a fresh Bop-It model with "normal" difficulty
    Then the Bop-It base time should equal 5000
