Feature: Per-difficulty leaderboards
  Each single-player mode keeps a separate top-10 leaderboard for Easy,
  Normal, and Hard so an Easy run never competes against a Hard run.
  The server validates the composite IDs, and legacy single-board files
  are migrated into the Normal bucket on first launch.

  Scenario: Each single-player mode has three difficulty buckets
    Then the server should accept "simon_easy" as a valid game type
    And the server should accept "simon_normal" as a valid game type
    And the server should accept "simon_hard" as a valid game type
    And the server should accept "bopit_easy" as a valid game type
    And the server should accept "bopit_normal" as a valid game type
    And the server should accept "bopit_hard" as a valid game type
    And the server should accept "keys_ninja_easy" as a valid game type
    And the server should accept "keys_ninja_normal" as a valid game type
    And the server should accept "keys_ninja_hard" as a valid game type

  Scenario: Multiplayer remains a single shared bucket
    Then the server should accept "multiplayer" as a valid game type
    And the server should reject "multiplayer_easy" as a game type
    And the server should reject "multiplayer_hard" as a game type

  Scenario: Legacy bare mode IDs are no longer accepted
    Then the server should reject "simon" as a game type
    And the server should reject "bopit" as a game type
    And the server should reject "keys_ninja" as a game type

  Scenario Outline: A score posted to one difficulty does not affect another
    Given an empty leaderboard for "<mode>_easy"
    And an empty leaderboard for "<mode>_hard"
    When the player posts score 50 with name "EZ" to "<mode>_easy"
    Then the leaderboard for "<mode>_easy" should have 1 entry
    And the leaderboard for "<mode>_hard" should have 0 entries

    Examples:
      | mode       |
      | simon      |
      | bopit      |
      | keys_ninja |

  Scenario: Same player name can hold a top spot on every difficulty
    Given an empty leaderboard for "simon_easy"
    And an empty leaderboard for "simon_normal"
    And an empty leaderboard for "simon_hard"
    When the player posts score 10 with name "ACE" to "simon_easy"
    And the player posts score 20 with name "ACE" to "simon_normal"
    And the player posts score 30 with name "ACE" to "simon_hard"
    Then the top score on "simon_easy" should be 10
    And the top score on "simon_normal" should be 20
    And the top score on "simon_hard" should be 30

  Scenario: Legacy single-board file is migrated into the Normal bucket
    Given a legacy "simon_scores.json" file with one entry "OLD" 99
    When the high scores module is reloaded
    Then a "simon_normal_scores.json" file should exist with one entry "OLD" 99
    And no "simon_scores.json" file should exist

  Scenario: Migration does not overwrite an existing Normal bucket
    Given a legacy "bopit_scores.json" file with one entry "OLD" 1
    And a "bopit_normal_scores.json" file with one entry "NEW" 100
    When the high scores module is reloaded
    Then the legacy "bopit_scores.json" file should still exist
    And the top score on "bopit_normal" should be 100
