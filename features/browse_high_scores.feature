Feature: Browseable High Scores from Settings
  Players can open the Settings overlay's HIGH SCORES entry to browse every
  single-player leaderboard (Simon, Bop It, Keys Ninja) and switch between
  Easy/Normal/Hard tabs. Multiplayer is excluded — it has its own bucket
  with no per-difficulty split.

  # ── Settings menu entry ──────────────────────────────────────────────────

  Scenario: Settings overlay exposes a HIGH SCORES button on the start menu
    Given a Settings overlay opened from the start menu
    Then the overlay should have a high scores rect

  Scenario: Settings overlay exposes a HIGH SCORES button mid-game
    Given a Settings overlay opened during a "simon" run
    Then the overlay should have a high scores rect

  Scenario: Clicking HIGH SCORES returns the high_scores action
    Given a Settings overlay opened from the start menu
    When the player clicks the HIGH SCORES button
    Then the overlay should return "high_scores"
    And the overlay should be closed

  # ── Browse-mode tabs ─────────────────────────────────────────────────────

  Scenario: Browse mode renders mode tabs for every single-player mode
    Given a high scores screen in browse mode for "simon"
    Then the screen should expose a "simon" mode tab
    And the screen should expose a "bopit" mode tab
    And the screen should expose a "keys_ninja" mode tab
    And the screen should not expose a "multiplayer" mode tab

  Scenario: Browse mode disables the Retry shortcut
    Given a high scores screen in browse mode for "bopit"
    Then the high scores screen should be in browse mode

  Scenario: Browse mode is forced off for multiplayer
    Given a high scores screen in browse mode for "multiplayer"
    Then the high scores screen should not be in browse mode

  Scenario: Post-game flow does not show mode tabs by default
    Given a high scores screen for "simon" "normal" after a run
    Then the high scores screen should not be in browse mode

  # ── Composite leaderboard ID resolution ──────────────────────────────────

  Scenario Outline: Browse mode resolves the right composite leaderboard ID
    Given a browse-mode high scores screen starting at "<mode>" "<difficulty>"
    Then the resolved leaderboard ID should be "<expected>"

    Examples:
      | mode       | difficulty | expected         |
      | simon      | easy       | simon_easy       |
      | simon      | normal     | simon_normal     |
      | simon      | hard       | simon_hard       |
      | bopit      | easy       | bopit_easy       |
      | bopit      | normal     | bopit_normal     |
      | bopit      | hard       | bopit_hard       |
      | keys_ninja | easy       | keys_ninja_easy  |
      | keys_ninja | normal     | keys_ninja_normal |
      | keys_ninja | hard       | keys_ninja_hard  |

  Scenario: Multiplayer leaderboard ID has no difficulty suffix
    Given a high scores screen for "multiplayer" "normal" after a run
    Then the resolved leaderboard ID should be "multiplayer"
