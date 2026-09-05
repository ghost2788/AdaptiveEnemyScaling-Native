"""Exercise proof rules; does not emulate or certify native boost semantics."""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET
from tests.osiris_subset import StoryFixture, call, value

GOAL = Path(__file__).resolve().parents[1] / 'story/RawFiles/Goals/AESN_83_HpTooltipProof.txt'
NULL = 'NULL_00000000-0000-0000-0000-000000000000'
PRIMARY = 'AESN_HP_TOOLTIP_PROOF_111'
REFERENCE = 'AESN_HP_TOOLTIP_REFERENCE_111'
STATS = GOAL.parents[3] / 'proofs/hp-tooltip/Status_AESN_HpTooltipProof.txt'


class ProbeFixture(StoryFixture):
    def action(self, text, env):
        name, tokens = call(text) if not text.startswith('NOT ') else ('', [])
        if name in {'AddBoosts', 'RemoveBoosts', 'ApplyStatus', 'RemoveStatus', 'SetFaction', 'SetCanFight',
                    'SetCanJoinCombat', 'SetHitpointsPercentage'}:
            self.calls.append((name, tuple(value(t, env) for t in tokens)))
        else:
            super().action(text, env)


class HpTooltipProofTests(unittest.TestCase):
    def setUp(self):
        self.s = ProbeFixture([GOAL]) if GOAL.exists() else ProbeFixture([])
        self.s.add('DB_AESN_HpTooltipProofEnabled', 1, fire=False)
        self.s.native['GetHostCharacter'] = [('host',)]
        self.s.native['GetFaction'] = [('host', 'friends')]
        self.s.native['GetHitpoints'] = [('fixture', 12)]
        self.s.native['GetMaxHitpoints'] = [('fixture', 12)]
        self.s.native['IsInCombat'] = [('host', 0)]
        self.s.native['CreateAtObject'] = [(
            'Kobolds_Melee_Drunk_45e31b7d-32ec-4f3d-8067-79061aeec77b',
            'host', 0, 1, '', 1, 'fixture')]

    def timer(self, name, who='fixture'):
        self.s.event('ObjectTimerFinished', who, 'AESN_HP_TOOLTIP_' + name)

    def start(self):
        self.s.event('SavegameLoaded')
        self.timer('SPAWN', 'host')
        self.timer('BASELINE')

    def observe(self, phase, maximum):
        if phase != 'RELOADED':
            self.timer('SETTLE')
        self.s.native['GetMaxHitpoints'] = [('fixture', maximum)]
        self.s.native['GetHitpoints'] = [('fixture', maximum)]
        self.timer(phase)

    def boosts(self):
        return [args for name, args in self.s.calls if name == 'ApplyStatus']

    def test_initial_load_applies_once_to_fixture_never_host(self):
        self.start()
        self.assertEqual([('fixture', PRIMARY, -1.0, 1, NULL)], self.boosts())
        self.s.event('SavegameLoaded')
        self.timer('SPAWN', 'host')
        self.timer('BASELINE')
        self.assertEqual(1, len(self.boosts()))

    def test_disabled_proof_does_nothing(self):
        self.s.facts['DB_AESN_HpTooltipProofEnabled'].clear()
        self.s.event('SavegameLoaded')
        self.assertEqual([], self.s.calls)

    def test_full_health_write_uses_native_heal_type_argument(self):
        self.start()
        self.assertFalse([args for name, args in self.s.calls if name == 'SetHitpointsPercentage'])
        self.timer('SETTLE')
        self.assertEqual([('fixture', 100.0, 'Guaranteed')],
                         [args for name, args in self.s.calls if name == 'SetHitpointsPercentage'])

    def test_combat_load_does_not_spawn(self):
        self.s.native['IsInCombat'] = [('host', 1)]
        self.s.event('SavegameLoaded')
        self.assertEqual([], self.s.calls)

    def test_reload_checks_retention_without_reapplying_then_removes_only_own_source(self):
        self.start()
        self.observe('APPLIED', 123)
        self.assertEqual([('fixture', 12, 'Inspect')], self.s.rows('DB_AESN_HpTooltipProofState'))
        self.s.event('SavegameLoaded')
        self.observe('RELOADED', 123)
        self.assertEqual(2, len(self.boosts()))
        self.assertEqual(('fixture', REFERENCE, -1.0, 1, NULL), self.boosts()[1])
        self.observe('REFERENCE', 234)
        removals = [args for name, args in self.s.calls if name == 'RemoveStatus']
        self.assertEqual([('fixture', PRIMARY, NULL)], removals)
        self.observe('OWN_REMOVED', 123)
        self.observe('CLEANED', 12)
        self.assertEqual([('fixture', 12, 'Complete')], self.s.rows('DB_AESN_HpTooltipProofState'))
        self.assertEqual([], self.s.rows('DB_AESN_HpTooltipProofFailure'))
        self.assertEqual([('fixture', PRIMARY, NULL), ('fixture', REFERENCE, NULL)],
                         [args for name, args in self.s.calls if name == 'RemoveStatus'])

    def test_wrong_hp_stops_sequence_instead_of_claiming_pass(self):
        self.start()
        self.observe('APPLIED', 124)
        self.assertTrue(self.s.rows('DB_AESN_HpTooltipProofFailure'))
        self.s.event('SavegameLoaded')
        self.assertEqual(1, len(self.boosts()))

    def test_recorded_observation_validates_only_the_current_phase(self):
        self.start()
        self.s.add('DB_AESN_HpTooltipProofObservation', 'fixture', 'Reloading', 123, 123, 123)
        self.assertEqual([('fixture', 12, 'Applying')], self.s.rows('DB_AESN_HpTooltipProofState'))
        self.s.add('DB_AESN_HpTooltipProofObservation', 'fixture', 'Applying', 123, 123, 123)
        self.assertEqual([('fixture', 12, 'Inspect')], self.s.rows('DB_AESN_HpTooltipProofState'))

    def test_recorded_observation_cannot_advance_a_failed_proof(self):
        self.start()
        self.s.add('DB_AESN_HpTooltipProofFailure', 'fixture', 'Applying')
        self.s.add('DB_AESN_HpTooltipProofObservation', 'fixture', 'Applying', 123, 123, 123)
        self.assertEqual([('fixture', 12, 'Applying')], self.s.rows('DB_AESN_HpTooltipProofState'))

    def test_missing_boost_after_reload_is_not_silently_repaired(self):
        self.start()
        self.observe('APPLIED', 123)
        self.s.event('SavegameLoaded')
        self.observe('RELOADED', 12)
        self.assertEqual([('fixture', 'Reloading')], self.s.rows('DB_AESN_HpTooltipProofFailure'))
        self.assertEqual(1, len(self.boosts()))

    def test_legacy_direct_boost_save_cannot_resume_as_status_proof(self):
        self.s.add('DB_AESN_HpTooltipProofStarted', 1, fire=False)
        self.s.add('DB_AESN_HpTooltipProofState', 'fixture', 12, 'Inspect', fire=False)
        self.s.event('SavegameLoaded')
        self.assertEqual([('fixture', 12, 'Inspect')], self.s.rows('DB_AESN_HpTooltipProofState'))
        self.assertEqual([], self.s.calls)

    def test_reload_does_not_write_hp_or_reapply_primary(self):
        self.start()
        self.observe('APPLIED', 123)
        self.s.calls.clear()
        self.s.event('SavegameLoaded')
        self.assertFalse([name for name, _ in self.s.calls
                          if name in {'ApplyStatus', 'AddBoosts', 'SetHitpointsPercentage'}])

    def test_requested_statuses_resolve_to_separate_flat_named_contributions(self):
        # Validate the artifact referenced by actual executed ApplyStatus calls,
        # not an invented native persistence/rendering model.
        definitions = {}
        source = STATS.read_text(encoding='utf-8') if STATS.exists() else ''
        for name, body in re.findall(r'new entry "([^"]+)"(.*?)(?=new entry |\Z)', source, re.S):
            definitions[name] = dict(re.findall(r'data "([^"]+)" "([^"]*)"', body))
        self.start()
        self.observe('APPLIED', 123)
        self.s.event('SavegameLoaded')
        self.observe('RELOADED', 123)
        requested = [args[1] for args in self.boosts()]
        self.assertEqual([PRIMARY, REFERENCE], requested)
        self.assertTrue(all(name in definitions for name in requested), 'Missing proof StatusData definition')
        localization = GOAL.parents[3] / ('toolkit/Mods/AdaptiveEnemyScalingNativePOC_'
            'a4567f52-1665-df50-b84c-3992f80fdb90/Localization/English/AdaptiveEnemyScalingNativePOC.xml')
        labels = {node.attrib['contentuid']: node.text for node in ET.parse(localization).getroot()}
        for name in requested:
            entry = definitions[name]
            self.assertEqual('BOOST', entry['StatusType'])
            self.assertEqual(['IncreaseMaxHP(111)'], [b for b in entry['Boosts'].split(';') if b])
            self.assertEqual('Adaptive Enemy Scaling', labels[entry['DisplayName'].split(';')[0]])
        self.assertNotEqual(definitions[PRIMARY]['StackId'], definitions[REFERENCE]['StackId'])


if __name__ == '__main__':
    unittest.main()
