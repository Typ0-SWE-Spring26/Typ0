Feature: Scoring
  The game awards one point when the player successfully repeats the full
  sequence, and resets the score when a new game begins.

  Background:
    Given a fresh game model

  Scenario: Correct input after a single-button sequence scores a point
    Given the sequence is "left"
    And the game is in input state
    When the player inputs "left"
    Then the score should be 1

  Scenario: Wrong input does not award a point
    Given the sequence is "left"
    And the game is in input state
    When the player inputs "right"
    Then the score should be 0

  Scenario: Partial correct input does not score
    Given the sequence is "left,right"
    And the game is in input state
    When the player inputs "left"
    Then the score should be 0

  Scenario: Score accumulates across multiple rounds
    Given the sequence is "left"
    And the game is in input state
    And the score is 3
    When the player inputs "left"
    Then the score should be 4

  Scenario: Score resets when the model resets
    Given the score is 7
    When the model is reset
    Then the score should be 0
