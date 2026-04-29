Feature: Name Entry Screen
  After achieving a high score, the player enters a 5-character name
  by typing characters directly.

  Scenario: Default name is five A's
    Given a name entry screen with score 50
    When the player confirms immediately
    Then the returned name should be "AAAAA"

  Scenario: Typing letters fills the slots
    Given a name entry screen with score 50
    When the player types "AB12"
    And the player confirms immediately
    Then the returned name should be "AB12 "

  Scenario: Space is accepted in the name
    Given a name entry screen with score 50
    When the player types "A B"
    And the player confirms immediately
    Then the returned name should be "A B  "

  Scenario: Moving cursor right affects the next slot
    Given a name entry screen with score 50
    When the player types "A"
    And the player moves cursor right
    And the player types "B"
    And the player confirms immediately
    Then the returned name should be "AB   "

  Scenario: Cursor wraps right from the last slot
    Given a name entry screen with score 50
    When the player types "ABCDE"
    And the player moves cursor right
    And the player types "Z"
    And the player confirms immediately
    Then the returned name should be "ZBCDE"

  Scenario: Cursor wraps left from the first slot
    Given a name entry screen with score 50
    When the player moves cursor left
    And the player types "Z"
    And the player confirms immediately
    Then the returned name should be "Z    "

  Scenario: Name entry returns quit on window close
    Given a name entry screen with score 50
    When the player closes the window
    Then the name entry should return "quit"
