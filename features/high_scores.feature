Feature: High Scores
  The game persists a top-10 leaderboard in JSON format. Players can earn
  a spot on the board, enter a 5-letter name, and see scores ranked
  highest-first.

  Scenario: Empty leaderboard accepts any score
    Given an empty scores file
    Then a score of 0 should qualify as a high score

  Scenario: Score qualifies when list is not full
    Given a scores file with 3 entries
    Then a score of 1 should qualify as a high score

  Scenario: Score qualifies when it beats the lowest on a full board
    Given a full scores file with lowest score 10
    Then a score of 11 should qualify as a high score

  Scenario: Score does not qualify when below the lowest on a full board
    Given a full scores file with lowest score 10
    Then a score of 5 should not qualify as a high score

  Scenario: Adding a score to an empty board
    Given an empty scores file
    When the player adds score 50 with name "HELLO"
    Then the leaderboard should have 1 entry
    And the top score name should be "HELLO"
    And the top score value should be 50

  Scenario: Adding a score maintains descending order
    Given a scores file with entries 100, 20
    When the player adds score 50 with name "MID00"
    Then the leaderboard should have 3 entries
    And the score at position 2 should be 50

  Scenario: Adding to a full board bumps the lowest score
    Given a full scores file with lowest score 10
    When the player adds score 999 with name "CHAMP"
    Then the leaderboard should have 10 entries
    And the top score name should be "CHAMP"

  Scenario: Saving truncates to max 10 entries
    Given a scores file with 15 entries
    When the scores are loaded
    Then the leaderboard should have 10 entries

  Scenario: Corrupt file returns empty list
    Given a corrupt scores file
    When the scores are loaded
    Then the leaderboard should have 0 entries

  Scenario: Missing file returns empty list
    Given a missing scores file
    When the scores are loaded
    Then the leaderboard should have 0 entries
