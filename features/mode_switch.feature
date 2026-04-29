Feature: Mode switching
  The in-game menu allows switching between Simon, Bop It, and Keys Ninja.

  Scenario: Switch from Simon to Bop It
    Given a menu overlay for "simon"
    When the player chooses to switch to "bopit"
    Then the menu overlay should return switch result for "bopit"

  Scenario: Switch from Simon to Keys Ninja
    Given a menu overlay for "simon"
    When the player chooses to switch to "keys_ninja"
    Then the menu overlay should return switch result for "keys_ninja"

  Scenario: Switch from Bop It to Simon
    Given a menu overlay for "bopit"
    When the player chooses to switch to "simon"
    Then the menu overlay should return switch result for "simon"

  Scenario: Switch from Keys Ninja to Simon
    Given a menu overlay for "keys_ninja"
    When the player chooses to switch to "simon"
    Then the menu overlay should return switch result for "simon"
