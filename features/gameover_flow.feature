Feature: Game Over Flow
  After a miss, the game over screen shows for up to 10 seconds before
  auto-switching to the high scores screen. Players can retry or view
  credits from the game over screen.

  Scenario: Game over screen returns retry on R key
    Given a game over screen with score 10
    When the player presses R
    Then the game over screen should return "retry"

  Scenario: Game over screen returns credits on C key
    Given a game over screen with score 10
    When the player presses C
    Then the game over screen should return "credits"

  Scenario: Game over screen returns quit on Q key
    Given a game over screen with score 10
    When the player presses Q
    Then the game over screen should return "quit"

  Scenario: Game over screen returns quit on ESC key
    Given a game over screen with score 10
    When the player presses ESC
    Then the game over screen should return "quit"

  Scenario: Game over auto-switches to high scores after 10 seconds
    Given a game over screen with score 10
    When 10 seconds elapse with no input
    Then the game over screen should return "high_scores"

  Scenario: Auto-switch timeout is 10 seconds
    Then the auto-switch constant should be 10000 milliseconds

  Scenario: High scores screen returns retry on R key
    Given a high scores screen
    When the player presses R
    Then the high scores screen should return "retry"

  Scenario: High scores screen returns quit on ESC key
    Given a high scores screen
    When the player presses ESC
    Then the high scores screen should return "quit"
