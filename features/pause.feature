Feature: Pause behaviour
  While the game is paused the controller does not forward input to the model.
  These scenarios simulate that guard by explicitly checking the pause flag
  before calling handle_input, mirroring the controller's logic.

  Background:
    Given a fresh game model
    And the sequence is "left"
    And the game is in input state

  Scenario: Input is accepted when the game is not paused
    Given the game is not paused
    When the player tries to input "left" while respecting the pause state
    Then the player index should be 1

  Scenario: Input is blocked when the game is paused
    Given the game is paused
    When the player tries to input "left" while respecting the pause state
    Then the player index should be 0

  Scenario: Pausing prevents the game state from changing on correct input
    Given the game is paused
    When the player tries to input "left" while respecting the pause state
    Then the game state should be "input"

  Scenario: Pausing prevents the game state from changing on wrong input
    Given the game is paused
    When the player tries to input "right" while respecting the pause state
    Then the game state should be "input"
