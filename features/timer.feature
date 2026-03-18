Feature: Input timer
  Players must respond before the countdown expires.
  When time runs out the game transitions to gameover with a specific reason.

  Background:
    Given a fresh game model

  Scenario: Timer expiry during input phase triggers game over
    Given the game is in input state
    When the timer expires
    Then the game state should be "gameover"

  Scenario: Timer expiry sets the correct gameover reason
    Given the game is in input state
    When the timer expires
    Then the gameover reason should be "Time's up!"

  Scenario: Timer expiry outside of input phase has no effect
    Given the game is in showing state
    And the sequence is "left"
    When the timer expires
    Then the game state should be "showing"

  Scenario: Game state returns to adding after a correct sequence and new game
    Given the sequence is "left"
    And the game is in input state
    When the player inputs "left"
    Then the game state should be "adding"
    And the gameover reason should be "Wrong input!"
