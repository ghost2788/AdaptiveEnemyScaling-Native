"""Exercise the disabled full-catalog proof with explicit native query results."""
from pathlib import Path
import unittest

from tests.osiris_subset import StoryFixture, call, value


GOAL = Path(__file__).resolve().parents[1] / 'story/RawFiles/Goals/AESN_82_HpCatalogProof.txt'
NULL = 'NULL_00000000-0000-0000-0000-000000000000'
SAMPLES = ((0, 20), (1, 21), (111, 131), (32768, 32788), (65535, 65555))


class CatalogFixture(StoryFixture):
    def action(self, text, env):
        name, tokens = call(text) if not text.startswith('NOT ') else ('', [])
        if name in {'ApplyStatus', 'RemoveStatus', 'SetFaction', 'SetCanFight',
                    'SetCanJoinCombat', 'SetHitpointsPercentage'}:
            self.calls.append((name, tuple(value(token, env) for token in tokens)))
        else:
            super().action(text, env)


class HpCatalogProofTests(unittest.TestCase):
    def setUp(self):
        self.s = CatalogFixture([GOAL]) if GOAL.exists() else CatalogFixture([])
        self.s.add('DB_AESN_HpCatalogEnabled', 1, fire=False)
        self.s.native['GetHostCharacter'] = [('host',)]
        self.s.native['GetFaction'] = [('host', 'friends')] + [(f'npc{amount}', 'friends') for amount, _ in SAMPLES]
        self.s.native['IsInCombat'] = [('host', 0)] + [(f'npc{amount}', 0) for amount, _ in SAMPLES]
        self.s.native['IsDead'] = [('host', 0)] + [(f'npc{amount}', 0) for amount, _ in SAMPLES]
        self.s.native['GetHitpoints'] = [(f'npc{amount}', 20) for amount, _ in SAMPLES]
        self.s.native['GetMaxHitpoints'] = [(f'npc{amount}', 20) for amount, _ in SAMPLES]
        template = 'Kobolds_Melee_Drunk_45e31b7d-32ec-4f3d-8067-79061aeec77b'
        self.s.native['CreateAtObject'] = [(template, 'host' if amount == 0 else f'npc{SAMPLES[index - 1][0]}',
                                             0, 1, '', 1, f'npc{amount}')
                                            for index, (amount, _) in enumerate(SAMPLES)]

    def timer(self, who, name):
        timer = 'SPAWN' if name.startswith('SPAWN_') else name
        self.s.event('ObjectTimerFinished', who, 'AESN_HP_CATALOG_' + timer)

    def start(self):
        self.s.event('SavegameLoaded')
        self.timer('host', 'SPAWN_0')
        for index, (amount, _) in enumerate(SAMPLES[1:], start=1):
            self.timer(f'npc{SAMPLES[index - 1][0]}', f'SPAWN_{index}')
        for amount, _ in SAMPLES:
            self.timer(f'npc{amount}', 'BASELINE')

    def set_hp(self, expected):
        self.s.native['GetMaxHitpoints'] = [(f'npc{amount}', maximum) for amount, maximum in expected.items()]
        self.s.native['GetHitpoints'] = [(f'npc{amount}', maximum) for amount, maximum in expected.items()]

    def advance_initial(self):
        for amount, _ in SAMPLES:
            self.timer(f'npc{amount}', 'SETTLE')
        self.set_hp(dict(SAMPLES))
        for amount, _ in SAMPLES:
            self.timer(f'npc{amount}', 'APPLIED')

    def advance_reload_cleanup(self):
        self.s.event('SavegameLoaded')
        self.set_hp(dict(SAMPLES))
        for amount, _ in SAMPLES:
            self.timer(f'npc{amount}', 'RELOADED')
        for amount, _ in SAMPLES:
            self.timer(f'npc{amount}', 'REMOVED')
        self.set_hp({amount: 20 for amount, _ in SAMPLES})
        for amount, _ in SAMPLES:
            self.timer(f'npc{amount}', 'CLEANED')

    def statuses(self, action='ApplyStatus'):
        return [args for name, args in self.s.calls if name == action]

    def test_boundary_samples_apply_exactly_one_catalog_status_except_zero(self):
        self.start()
        self.assertEqual([(f'npc{amount}', f'AESN_HP_TOTAL_{amount}', -1.0, 1, NULL)
                          for amount, _ in SAMPLES if amount], self.statuses())
        self.assertNotIn('host', [args[0] for args in self.statuses()])
        self.advance_initial()
        self.assertEqual([], self.s.rows('DB_AESN_HpCatalogFailure'))
        self.assertEqual([(f'npc{amount}', amount, 20, 'Inspect') for amount, _ in SAMPLES],
                         self.s.rows('DB_AESN_HpCatalogState'))

    def test_reload_retention_never_reapplies_or_writes_hp_and_exact_removal_returns_baseline(self):
        self.start()
        self.advance_initial()
        self.s.calls.clear()
        self.s.event('SavegameLoaded')
        self.assertFalse([name for name, _ in self.s.calls
                          if name in {'ApplyStatus', 'SetHitpointsPercentage'}])
        self.set_hp(dict(SAMPLES))
        for amount, _ in SAMPLES:
            self.timer(f'npc{amount}', 'RELOADED')
        self.assertEqual([(f'npc{amount}', f'AESN_HP_TOTAL_{amount}', NULL)
                          for amount, _ in SAMPLES if amount], self.statuses('RemoveStatus'))
        self.set_hp({amount: 20 for amount, _ in SAMPLES})
        for amount, _ in SAMPLES:
            self.timer(f'npc{amount}', 'REMOVED')
        for amount, _ in SAMPLES:
            self.timer(f'npc{amount}', 'CLEANED')
        self.assertEqual([(f'npc{amount}', amount, 20, 'Complete') for amount, _ in SAMPLES],
                         self.s.rows('DB_AESN_HpCatalogState'))

    def test_missing_bonus_after_reload_records_failure_without_repair(self):
        self.start()
        self.advance_initial()
        self.s.calls.clear()
        self.s.event('SavegameLoaded')
        self.set_hp({amount: 20 for amount, _ in SAMPLES})
        for amount, _ in SAMPLES:
            self.timer(f'npc{amount}', 'RELOADED')
        self.assertIn(('npc111', 111, 'Reloading'), self.s.rows('DB_AESN_HpCatalogFailure'))
        self.assertEqual([], self.statuses())

    def test_disabled_duplicate_dead_and_unsupported_paths_cannot_boost_or_complete(self):
        self.s.facts['DB_AESN_HpCatalogEnabled'].clear()
        self.s.event('SavegameLoaded')
        self.assertEqual([], self.s.calls)
        self.s.add('DB_AESN_HpCatalogEnabled', 1, fire=False)
        self.s.native['IsDead'] = [('host', 0), ('npc0', 1)] + [(f'npc{amount}', 0) for amount, _ in SAMPLES[1:]]
        self.start()
        self.timer('npc0', 'BASELINE')
        self.assertIn(('npc0', 0, 'Baseline'), self.s.rows('DB_AESN_HpCatalogFailure'))
        applied = len(self.statuses())
        self.s.event('SavegameLoaded')
        self.timer('host', 'SPAWN_0')
        self.assertEqual(applied, len(self.statuses()))
        self.s.proc('PROC_AESN_HpCatalogApply', 'npc0', 999)
        self.assertIn(('npc0', 999, 'Unsupported'), self.s.rows('DB_AESN_HpCatalogFailure'))

    def test_duplicate_spawn_and_baseline_cannot_create_or_reapply_a_fixture(self):
        self.s.event('SavegameLoaded')
        self.timer('host', 'SPAWN_0')
        self.timer('npc0', 'SPAWN_1')
        self.timer('npc0', 'SPAWN_1')
        self.assertEqual(2, len([args for name, args in self.s.calls if name == 'SetFaction']))
        self.start()
        self.advance_initial()
        self.s.event('SavegameLoaded')
        self.timer('npc111', 'BASELINE')
        self.assertEqual(1, len([args for args in self.statuses() if args[0] == 'npc111']))
        self.assertEqual([('npc111', 111, 20, 'Reloading')],
                         [row for row in self.s.rows('DB_AESN_HpCatalogState') if row[0] == 'npc111'])

    def test_dead_or_disabled_settle_records_failure_without_healing(self):
        self.start()
        self.s.native['IsDead'] = [('npc111', 1)] + [(f'npc{amount}', 0) for amount, _ in SAMPLES if amount != 111]
        self.s.native['GetHitpoints'] = [('npc111', 0)] + [(f'npc{amount}', 20) for amount, _ in SAMPLES if amount != 111]
        self.timer('npc111', 'SETTLE')
        self.assertIn(('npc111', 111, 'Settle'), self.s.rows('DB_AESN_HpCatalogFailure'))
        self.assertNotIn(('npc111', 100.0, 'Guaranteed'),
                         [args for name, args in self.s.calls if name == 'SetHitpointsPercentage'])
        self.s.facts['DB_AESN_HpCatalogEnabled'].clear()
        self.timer('npc1', 'SETTLE')
        self.assertNotIn(('npc1', 100.0, 'Guaranteed'),
                         [args for name, args in self.s.calls if name == 'SetHitpointsPercentage'])

    def test_zero_or_injured_baseline_records_failure_without_status(self):
        self.s.native['GetHitpoints'] = [('npc0', 0), ('npc1', 10), ('npc111', 20), ('npc32768', 20), ('npc65535', 20)]
        self.start()
        self.assertIn(('npc0', 0, 'Baseline'), self.s.rows('DB_AESN_HpCatalogFailure'))
        self.assertIn(('npc1', 1, 'Baseline'), self.s.rows('DB_AESN_HpCatalogFailure'))
        self.assertNotIn('npc1', [args[0] for args in self.statuses()])

    def test_delayed_spawn_and_baseline_are_inert_after_combat_or_anchor_death(self):
        self.s.event('SavegameLoaded')
        self.s.native['IsInCombat'] = [('host', 1)] + [(f'npc{amount}', 0) for amount, _ in SAMPLES]
        self.timer('host', 'SPAWN_0')
        self.assertEqual([], [args for name, args in self.s.calls if name == 'SetFaction'])
        self.setUp()
        self.s.event('SavegameLoaded')
        self.s.native['IsDead'] = [('host', 1)] + [(f'npc{amount}', 0) for amount, _ in SAMPLES]
        self.timer('host', 'SPAWN_0')
        self.assertEqual([], [args for name, args in self.s.calls if name == 'SetFaction'])
        self.setUp()
        self.s.native['IsInCombat'] = [('host', 0), ('npc111', 1)] + [(f'npc{amount}', 0) for amount, _ in SAMPLES if amount != 111]
        self.start()
        self.assertNotIn('npc111', [args[0] for args in self.statuses()])

    def test_failed_baseline_and_duplicate_settle_cannot_mutate_after_recovery_or_replay(self):
        self.s.native['GetHitpoints'] = [('npc111', 0)] + [(f'npc{amount}', 20) for amount, _ in SAMPLES if amount != 111]
        self.start()
        self.set_hp({amount: 20 for amount, _ in SAMPLES})
        self.timer('npc111', 'BASELINE')
        self.assertNotIn('npc111', [args[0] for args in self.statuses()])
        self.setUp()
        self.start()
        self.timer('npc111', 'SETTLE')
        self.timer('npc111', 'SETTLE')
        self.assertEqual(1, len([args for name, args in self.s.calls
                                 if name == 'SetHitpointsPercentage' and args[0] == 'npc111']))

    def test_invalid_phase_check_cannot_record_or_advance_state(self):
        self.start()
        self.s.proc('PROC_AESN_HpCatalogCheck', 'npc111', 'Bogus', 1)
        self.assertEqual([], [row for row in self.s.rows('DB_AESN_HpCatalogObservation')
                              if row[0] == 'npc111' and row[2] == 'Bogus'])


if __name__ == '__main__':
    unittest.main()
