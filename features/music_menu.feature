Feature: Music Menu
  The music menu keeps the built-in tracks available, appends web uploads,
  and lets players return cleanly without leaving the upload control behind.

  Scenario: Music menu starts with the built-in tracks
    Given a fresh music menu
    Then the menu should have 3 built-in tracks
    And the current track should be "TECHNO THEME"

  Scenario: Web uploads are appended after the built-in tracks
    Given a web music menu with uploaded tracks "SUNRISE,LOOP"
    When the music menu synchronizes uploaded tracks
    Then the menu should have 5 tracks
    And the track at position 4 should be "SUNRISE"
    And the track at position 5 should be "LOOP"

  Scenario: Music menu keeps the current track in range when uploads shrink
    Given a web music menu with uploaded tracks "ONE,TWO"
    And the current track index is 4
    When the uploaded tracks are replaced with "SOLO"
    And the music menu synchronizes uploaded tracks
    Then the current track index should be 3
    And the menu should have 4 tracks

  Scenario: Drawing the web music menu shows the upload control once
    Given a web music menu
    When the music menu is drawn
    Then the upload button should be visible
    And the upload helper should be called once

  Scenario: Back closes the web upload control
    Given a web music menu with uploaded tracks "MIX"
    And the upload button is visible
    When the player clicks the back button
    Then the music menu should return "Back"
    And the upload button should be hidden