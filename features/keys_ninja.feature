Feature: Keys Ninja Mode
  Keys Ninja spawns falling keys. Correct hits score points, bombs end the run,
  and missed keys reduce lives.

  Scenario: Correct key increases score and combo
    Given a keys ninja model
    And a normal key "A" is on screen
    When the player hits key "A"
    Then the keys ninja score should be 10
    And the keys ninja combo should be 1

  Scenario: Bomb hit ends the game
    Given a keys ninja model
    And a bomb key "B" is on screen
    When the player hits key "B"
    Then the keys ninja game should be over with reason "Hit a bomb!"

  Scenario: Missing a key reduces lives
    Given a keys ninja model with 1 life
    And a normal key "C" has fallen off screen
    When the keys ninja model updates
    Then the keys ninja game should be over with reason "Out of lives!"

  Scenario: Wrong key resets combo without ending the game
    Given a keys ninja model
    And a normal key "A" is on screen
    And the keys ninja combo is 3
    When the player hits key "Z"
    Then the keys ninja combo should be 0
    And the keys ninja state should be "playing"
