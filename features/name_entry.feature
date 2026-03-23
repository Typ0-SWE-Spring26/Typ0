Feature: Name Entry Screen
  After achieving a high score, the player enters a 5-character name
  using arcade-style letter scrolling.

  Scenario: Default name is five A's
    Given a name entry screen with score 50
    When the player confirms immediately
    Then the returned name should be "AAAAA"

  Scenario: Scrolling up changes the current letter
    Given a name entry screen with score 50
    When the player scrolls up once
    And the player confirms immediately
    Then the first letter should be "B"

  Scenario: Scrolling down from A wraps to end of alphabet
    Given a name entry screen with score 50
    When the player scrolls down once
    And the player confirms immediately
    Then the first letter should be " "

  Scenario: Moving cursor right and scrolling affects second slot
    Given a name entry screen with score 50
    When the player moves cursor right
    And the player scrolls up once
    And the player confirms immediately
    Then the first letter should be "A"
    And the second letter should be "B"

  Scenario: Cursor does not move past the last slot
    Given a name entry screen with score 50
    When the player moves cursor right 10 times
    And the player scrolls up once
    And the player confirms immediately
    Then the last letter should be "B"

  Scenario: Cursor does not move before the first slot
    Given a name entry screen with score 50
    When the player moves cursor left
    And the player scrolls up once
    And the player confirms immediately
    Then the first letter should be "B"

  Scenario: Name entry returns quit on window close
    Given a name entry screen with score 50
    When the player closes the window
    Then the name entry should return "quit"
