Feature: Multiplayer game synchronisation and outcome

  Background:
    Given two players with the same seed

  Scenario: Same seed produces identical sequences
    When both players advance through 5 rounds
    Then both sequences are identical

  Scenario: Winner is decided when a player makes a mistake
    Given both players are in input state with sequence "left"
    When player one inputs "right"
    Then player one is in gameover state
    And player two is still playing

  Scenario: Correct input keeps both players in sync
    Given both players are in input state with sequence "left"
    When player one inputs "left"
    And player two inputs "left"
    Then player one score is 1
    And player two score is 1

  Scenario: Settings flag propagates inverted keys
    Given a settings flag with inverted keys enabled
    Then the decoded settings show inverted keys is true

  Scenario: Settings flag default has no inverted keys
    Given a settings flag with default settings
    Then the decoded settings show inverted keys is false
