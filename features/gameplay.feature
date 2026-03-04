Feature: Gameplay state machine
  The game cycles through four states: adding -> showing -> input -> adding.
  A wrong input at any point sends the game to gameover.

  Background:
    Given a fresh game model

  Scenario: Adding state appends a button to the sequence
    Given the game is in adding state
    And the next action time has passed
    When the game updates
    Then the sequence length should be 1
    And the game state should be "showing"

  Scenario: Showing state transitions to input once all buttons are displayed
    Given the sequence is "left"
    And the game is in showing state
    And all buttons have been shown
    When the game updates
    Then the game state should be "input"

  Scenario: Correct input advances the player position
    Given the sequence is "left,right"
    And the game is in input state
    When the player inputs "left"
    Then the player index should be 1

  Scenario: Completing the full sequence starts the next round
    Given the sequence is "left"
    And the game is in input state
    When the player inputs "left"
    Then the game state should be "adding"
    And the score should be 1

  Scenario: Wrong input triggers game over
    Given the sequence is "left"
    And the game is in input state
    When the player inputs "right"
    Then the game state should be "gameover"

  Scenario: Correct input records the pressed button for visual feedback
    Given the sequence is "left,right"
    And the game is in input state
    When the player inputs "left"
    Then the flash button should be "left"

  Scenario: Multi-step sequence requires every button in order
    Given the sequence is "left,right"
    And the game is in input state
    When the player inputs "left"
    And the player inputs "right"
    Then the score should be 1
    And the game state should be "adding"

  Scenario: Wrong button in the middle of a sequence triggers game over
    Given the sequence is "left,right"
    And the game is in input state
    When the player inputs "left"
    And the player inputs "down"
    Then the game state should be "gameover"
    And the score should be 0
