Feature: Credits Screen
  The credits screen lists team members grouped by role and supports
  navigating back to the previous screen.

  Scenario: Credits data contains at least one role
    Given the credits data is loaded
    Then there should be at least 1 role entry

  Scenario: Every role has at least one name
    Given the credits data is loaded
    Then every role should have at least 1 name

  Scenario: Credits screen returns back on ESC
    Given a credits screen is running
    When the player presses ESC
    Then the credits screen should return "back"

  Scenario: Credits screen returns back on Q
    Given a credits screen is running
    When the player presses Q
    Then the credits screen should return "back"

  Scenario: Credits screen returns quit on window close
    Given a credits screen is running
    When the player closes the window
    Then the credits screen should return "quit"
