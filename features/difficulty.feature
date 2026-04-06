Feature: Difficulty settings
  Players can choose Easy, Normal, or Hard before starting a game.
  Difficulty controls how fast the game moves and how much time the player has.
  Normal matches the original game behaviour; Easy is more forgiving; Hard is more demanding.

  # ── Simon mode ────────────────────────────────────────────────────────────

  Scenario: Simon Normal mode is the default difficulty
    Given a fresh Simon game model with "normal" difficulty
    Then the Simon timer limit should equal the normal preset timer limit
    And the Simon flash time should equal the normal preset flash time

  Scenario: Simon Easy gives the player more time per round than Normal
    Given a fresh Simon game model with "easy" difficulty
    And a fresh Simon game model with "normal" difficulty as "normal_model"
    Then the Simon easy timer limit should be greater than the normal timer limit

  Scenario: Simon Hard gives the player less time per round than Normal
    Given a fresh Simon game model with "hard" difficulty
    And a fresh Simon game model with "normal" difficulty as "normal_model"
    Then the Simon hard timer limit should be less than the normal timer limit

  Scenario: Simon Easy shows each button for longer than Hard
    Given a fresh Simon game model with "easy" difficulty
    And a fresh Simon game model with "hard" difficulty as "hard_model"
    Then the Simon easy flash time should be greater than the hard flash time

  Scenario: Simon Easy pauses longer between rounds than Hard
    Given a fresh Simon game model with "easy" difficulty
    And a fresh Simon game model with "hard" difficulty as "hard_model"
    Then the Simon easy post-round pause should be greater than the hard post-round pause

  Scenario Outline: Simon difficulty timings are used during sequence display
    Given a fresh Simon game model with "<difficulty>" difficulty
    And the game is in showing state
    And the sequence is "left"
    And the next action time has passed
    When the game updates
    Then the flash end time should match the "<difficulty>" flash time

    Examples:
      | difficulty |
      | easy       |
      | normal     |
      | hard       |

  Scenario Outline: Simon difficulty timings are used after a completed round
    Given a fresh Simon game model with "<difficulty>" difficulty
    And the sequence is "left"
    And the game is in input state
    When the player inputs "left"
    Then the next action time should match the "<difficulty>" post-round pause

    Examples:
      | difficulty |
      | easy       |
      | normal     |
      | hard       |

  # ── Bop-It mode ───────────────────────────────────────────────────────────

  Scenario: Bop-It Normal mode is the default difficulty
    Given a fresh Bop-It model with "normal" difficulty
    Then the Bop-It base time should equal the normal Bop-It preset base time

  Scenario: Bop-It Easy starts with more time than Hard
    Given a fresh Bop-It model with "easy" difficulty
    And a fresh Bop-It model with "hard" difficulty as "hard_bopit"
    Then the Bop-It easy base time should be greater than the hard base time

  Scenario: Bop-It Hard reaches minimum time sooner than Easy
    Given a fresh Bop-It model with "easy" difficulty
    And a fresh Bop-It model with "hard" difficulty as "hard_bopit"
    Then the Bop-It hard minimum time should be less than the easy minimum time

  Scenario Outline: Bop-It time limit decreases correctly for each difficulty
    Given a fresh Bop-It model with "<difficulty>" difficulty
    And the Bop-It score is 3
    Then the Bop-It time limit should be base minus 3 steps

    Examples:
      | difficulty |
      | easy       |
      | normal     |
      | hard       |

  Scenario: Bop-It Easy round delay is longer than Hard at the start
    Given a fresh Bop-It model with "easy" difficulty
    And a fresh Bop-It model with "hard" difficulty as "hard_bopit"
    Then the Bop-It easy round delay should be greater than the hard round delay
