"""Steps for high scores feature scenarios."""
import json
import os
import tempfile
from behave import given, when, then
from unittest.mock import patch

# Imports deferred to step functions — pygame must be mocked first by environment.py


def _track_temp_file(ctx, path):
    if not hasattr(ctx, '_temp_files'):
        ctx._temp_files = []
    ctx._temp_files.append(path)


@given('an empty scores file')
def step_empty_scores(ctx):
    ctx.tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    ctx.tmp.write('[]')
    ctx.tmp.close()
    ctx.scores_file = ctx.tmp.name
    _track_temp_file(ctx, ctx.scores_file)


@given('a scores file with {n:d} entries')
def step_scores_with_n(ctx, n):
    ctx.tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    data = [{"name": f"P{i:04d}", "score": i} for i in range(n)]
    ctx.tmp.write(json.dumps(data))
    ctx.tmp.close()
    ctx.scores_file = ctx.tmp.name
    _track_temp_file(ctx, ctx.scores_file)


@given('a full scores file with lowest score {low:d}')
def step_full_scores(ctx, low):
    ctx.tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    from game.core.high_scores import MAX_SCORES
    data = [{"name": f"P{i:04d}", "score": low + i} for i in range(MAX_SCORES)]
    ctx.tmp.write(json.dumps(data))
    ctx.tmp.close()
    ctx.scores_file = ctx.tmp.name
    _track_temp_file(ctx, ctx.scores_file)


@given('a scores file with entries {scores}')
def step_scores_with_values(ctx, scores):
    ctx.tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    values = [int(s.strip()) for s in scores.split(',')]
    data = [{"name": f"P{i:04d}", "score": v} for i, v in enumerate(values)]
    ctx.tmp.write(json.dumps(data))
    ctx.tmp.close()
    ctx.scores_file = ctx.tmp.name
    _track_temp_file(ctx, ctx.scores_file)


@given('a corrupt scores file')
def step_corrupt_scores(ctx):
    ctx.tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    ctx.tmp.write('not valid json!!!')
    ctx.tmp.close()
    ctx.scores_file = ctx.tmp.name
    _track_temp_file(ctx, ctx.scores_file)


@given('a missing scores file')
def step_missing_scores(ctx):
    ctx.scores_file = os.path.join(tempfile.gettempdir(), 'nonexistent_scores.json')
    if os.path.exists(ctx.scores_file):
        os.remove(ctx.scores_file)


@then('a score of {n:d} should qualify as a high score')
def step_qualifies(ctx, n):
    with patch('game.core.high_scores.SCORES_FILE', ctx.scores_file):
        from game.core.high_scores import is_high_score
        assert is_high_score(n) is True


@then('a score of {n:d} should not qualify as a high score')
def step_not_qualifies(ctx, n):
    from game.core.high_scores import is_high_score
    with patch('game.core.high_scores.SCORES_FILE', ctx.scores_file):
        assert is_high_score(n) is False


@when('the player adds score {score:d} with name "{name}"')
def step_add_score(ctx, score, name):
    from game.core.high_scores import add_score
    with patch('game.core.high_scores.SCORES_FILE', ctx.scores_file):
        ctx.result_scores = add_score(name, score)


@when('the scores are loaded')
def step_load_scores(ctx):
    from game.core.high_scores import load_scores
    with patch('game.core.high_scores.SCORES_FILE', ctx.scores_file):
        ctx.result_scores = load_scores()


@then('the leaderboard should have {n:d} entry')
@then('the leaderboard should have {n:d} entries')
def step_leaderboard_count(ctx, n):
    assert len(ctx.result_scores) == n, (
        f'Expected {n} entries, got {len(ctx.result_scores)}'
    )


@then('the top score name should be "{name}"')
def step_top_name(ctx, name):
    assert ctx.result_scores[0]["name"] == name


@then('the top score value should be {n:d}')
def step_top_value(ctx, n):
    assert ctx.result_scores[0]["score"] == n


@then('the score at position {pos:d} should be {score:d}')
def step_score_at_pos(ctx, pos, score):
    assert ctx.result_scores[pos - 1]["score"] == score, (
        f'Expected score {score} at position {pos}, got {ctx.result_scores[pos - 1]["score"]}'
    )
