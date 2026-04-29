Feature: Menu overlay controls
  The in-game menu supports closing and returning to the main menu.

  Scenario: Close the menu with the X button
    Given an open menu overlay for "simon"
    When the player clicks the menu close button
    Then the menu overlay should be closed

  Scenario: Close the menu with the Escape key
    Given an open menu overlay for "bopit"
    When the player presses Escape
    Then the menu overlay should be closed

  Scenario: Return to the main menu from in-game
    Given an open menu overlay for "keys_ninja"
    When the player chooses main menu
    Then the menu overlay should return "main_menu"
