"""Real 45/50 rules, with independently supplied native observations.

Only deterministic string/integer primitives are evaluated here. External
actions are recorded, never made to mutate HasActiveStatus or HP responses.
"""
from pathlib import Path
from tests.osiris_subset import StoryFixture, bind, call, value

GOALS = Path(__file__).resolve().parents[1] / 'story/RawFiles/Goals'


class HpStoryFixture(StoryFixture):
    def __init__(self, paths=None):
        super().__init__(paths or [p for p in [GOALS / 'AESN_45_HpTotal.txt',
                                             GOALS / 'AESN_50_Applications.txt'] if p.exists()])
        self.intent_at_call = []

    def run(self, name, *args):
        # Missing backend during RED is a no-op, yielding behavioral assertions.
        if name in self.rules:
            self.proc(name, *args)

    def solutions(self, terms, env):
        if terms and terms[0].startswith(('ConcatenateInteger(', 'IntegerSubtract(',
                                         'IntegerProduct(', 'IntegerDivide(')):
            name, tokens = call(terms[0])
            a, b = [value(t, env) for t in tokens[:2]]
            if name == 'ConcatenateInteger':
                result = a + str(b)
            elif name == 'IntegerSubtract':
                result = a - b
            elif name == 'IntegerProduct':
                result = a * b
            else:
                result = abs(a) // abs(b) * (-1 if (a < 0) != (b < 0) else 1)
            local = bind(tokens, (a, b, result), env)
            if local is not None:
                yield from self.solutions(terms[1:], local)
            return
        yield from super().solutions(terms, env)

    def action(self, text, env):
        name, tokens = call(text) if not text.startswith('NOT ') else ('', [])
        if name in {'ApplyStatus', 'RemoveStatus', 'SetHitpoints', 'SetHitpointsPercentage'}:
            self.calls.append((name, tuple(value(token, env) for token in tokens)))
            self.intent_at_call.append((name, list(self.rows('DB_AESN_HpTotalPending'))))
        else:
            super().action(text, env)

    def observe(self, maximum=20, current=10, percentage=50.0, active=()):
        self.native['GetMaxHitpoints'] = [('enemy', maximum)]
        self.native['GetHitpoints'] = [('enemy', current)]
        self.native['GetHitpointsPercentage'] = [('enemy', percentage)]
        self.native['IsDead'] = [('enemy', int(current == 0))]
        statuses = {'AESN_HP_TOTAL_111', 'AESN_HP_TOTAL_7', *active}
        self.native['HasActiveStatus'] = [('enemy', s, int(s in active)) for s in statuses]

    def transaction(self, delta=111, version=2, state='Planned', applied=0, owner='owner'):
        self.add('DB_AESN_HpTransaction', owner, 'enemy', version, state,
                 10, 20, 50.0, 20 + delta, delta, applied, fire=False)

    def hp_writes(self):
        return [c for c in self.calls if c[0] in {'SetHitpoints', 'SetHitpointsPercentage'}]
