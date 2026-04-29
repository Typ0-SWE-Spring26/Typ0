Feature: Bop It mode
  Bop It commands require correct input; wrong input ends the game.

  Scenario: Wrong input ends the game
    Given a bopit model in input with command "left"
    When the player presses bopit input "right"
    Then the bopit game should be over

  Scenario: Correct input increases score
    Given a bopit model in input with command "left"
    When the player presses bopit input "left"
    Then the bopit score should be at least 1
