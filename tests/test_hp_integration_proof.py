"""Real84 + reviewed production rules; native responses are supplied, never simulated."""
from pathlib import Path
import unittest
from tests.hp_story_fixture import GOALS, HpStoryFixture
from tests.osiris_subset import call, value

PROOF = GOALS.parents[2] / 'proofs/hp-total-integration/AESN_84_HpIntegrationProof.txt'
TEMPLATE = 'Kobolds_Melee_Drunk_45e31b7d-32ec-4f3d-8067-79061aeec77b'
BITS = {1: (1,), 111: (1, 2, 4, 8, 32, 64)}


class NativeFixture(HpStoryFixture):
    def action(self, text, env):
        name, tokens = call(text) if not text.startswith('NOT ') else ('', [])
        if name in {'SetFaction', 'SetCanFight', 'SetCanJoinCombat', 'PROC_SelfHealing_Disable'}:
            self.calls.append((name, tuple(value(t, env) for t in tokens)))
        else:
            super().action(text, env)


class HpIntegrationProofTests(unittest.TestCase):
    def make(self, enabled=True):
        paths = [GOALS / ('AESN_' + n + '.txt') for n in
                 ('40_HpTransaction', '45_HpTotal', '47_HpMigration', '50_Applications',
                  '55_Components', '60_Merge', '65_Reconciliation', '66_WorldHardenedRuntime')]
        f = NativeFixture(paths + ([PROOF] if PROOF.exists() else []))
        if enabled:
            f.add('DB_AESN_HpIntegrationEnabled', 1, fire=False)
        f.add('DB_AESN_WorldContext', 'owner', fire=False)
        f.add('DB_AESN_CombatSnapshotV2', 'owner', 2, 4, 4, 20, 5, 1, 210, 1, 0, 2, 'Supported', fire=False)
        f.native['GetHostCharacter'] = [('host',)]
        f.native['GetFaction'] = [('host', 'friends'), ('npc1', 'friends'), ('npc111', 'friends')]
        for n in ('IsDead', 'IsInCombat'):
            f.native[n] = [(a, 0) for a in ('host', 'npc1', 'npc111')]
        for n in ('CanFight', 'CanJoinCombat'):
            f.native[n] = [('npc1', 0), ('npc111', 0)]
        f.native['QRY_SelfHealing_IsEnabled'] = [('npc111',)]
        f.native['CreateAtObject'] = [(TEMPLATE, 'host', 0, 1, '', 1, 'npc1'),
                                      (TEMPLATE, 'npc1', 0, 1, '', 1, 'npc111')]
        for amount in BITS:
            self.observe(f, amount, 20, 20, legacy=False, reference=False)
        return f

    def observe(self, f, amount, current, maximum, legacy=True, reference=True, bits=None):
        npc = f'npc{amount}'
        for name, number in (('GetHitpoints', current), ('GetMaxHitpoints', maximum),
                             ('GetHitpointsPercentage', current * 100.0 / maximum)):
            f.native[name] = [r for r in f.native[name] if r[0] != npc] + [(npc, number)]
        active = {'AESN_HP_TOTAL_7'} if reference else set()
        if legacy:
            active.add('AESN_HARDENED_FOE_01')
            active.update(f'AESN_HP_BIT_{b:05}' for b in (BITS[amount] if bits is None else bits))
        known = {f'AESN_HP_BIT_{2**i:05}' for i in range(16)} | {
            'AESN_HP_TOTAL_7', 'AESN_HP_TOTAL_1', 'AESN_HP_TOTAL_111', 'AESN_HARDENED_FOE_01'}
        f.native['HasActiveStatus'] = [r for r in f.native['HasActiveStatus'] if r[0] != npc] + [
            (npc, s, int(s in active)) for s in known]

    def timer(self, f, npc, phase):
        f.event('ObjectTimerFinished', npc, 'AESN_HpIntegration_' + phase)

    def start(self, f):
        f.run('PROC_AESN_HpIntegrationLoad')
        self.timer(f, 'host', 'Spawn')
        self.timer(f, 'npc1', 'Spawn')

    def inspect(self, f, normal_current=69):
        self.start(f)
        for amount in BITS:
            npc = f'npc{amount}'
            self.timer(f, npc, 'Baseline')
            self.observe(f, amount, 20 + 7 + amount, 20 + 7 + amount)
            for s in ['AESN_HP_TOTAL_7', 'AESN_HARDENED_FOE_01', *[f'AESN_HP_BIT_{b:05}' for b in BITS[amount]]]:
                f.event('StatusApplied', npc, s, 'cause', 10)
            self.timer(f, npc, 'Legacy')
            self.observe(f, amount, 13 if amount == 1 else normal_current, 27 + amount)
            f.event('HitpointsChanged', npc, 50.0)
            self.timer(f, npc, 'Wound')

    def migrate(self, f):
        f.run('PROC_AESN_HpIntegrationLoad')
        for amount in BITS:
            self.timer(f, f'npc{amount}', 'Migrate')

    def test_disabled_is_inert(self):
        f = self.make(False)
        self.start(f)
        self.assertFalse(f.calls)
        self.assertFalse(f.rows('DB_AESN_HpIntegrationFixture'))

    def test_unique_spawn_and_no_host_or_unrecorded_mutation(self):
        f = self.make()
        self.start(f)
        self.assertEqual(2, len(f.rows('DB_AESN_HpIntegrationFixture')))
        before = list(f.calls)
        for npc in ('host', 'other'):
            f.run('PROC_AESN_HpIntegrationSetup', npc, 1, 'friends')
        self.timer(f, 'host', 'Spawn')
        self.timer(f, 'npc1', 'Spawn')
        self.assertEqual(before, f.calls)
        self.assertFalse([a for n, a in f.calls if n.startswith('Set') and a[0] == 'host'])

    def test_partial_setup_reload_never_commits_or_respawns(self):
        f = self.make()
        self.start(f)
        f.run('PROC_AESN_HpIntegrationLoad')
        before = list(f.calls)
        for a in BITS:
            self.timer(f, f'npc{a}', 'Baseline')
        self.assertEqual(before, f.calls)
        self.assertTrue(f.rows('DB_AESN_HpIntegrationFailure'))
        self.assertFalse(f.rows('DB_AESN_HpTransaction'))

    def test_inspect_is_fixture_only_and_normal_healing_is_not_disabled(self):
        f = self.make()
        self.inspect(f, normal_current=138)
        self.assertEqual(2, len([r for r in f.rows('DB_AESN_HpIntegrationState') if r[-1] == 'Inspect']))
        self.assertFalse(f.rows('DB_AESN_HpTransaction'))
        self.assertFalse(f.rows('DB_AESN_WorldTracked'))
        self.assertEqual([('PROC_SelfHealing_Disable', ('npc1',))], [c for c in f.calls if c[0] == 'PROC_SelfHealing_Disable'])
        self.assertEqual(2, len(f.hp_writes()))
        self.assertIn(('npc111', 'Inspect', 138, 138), f.rows('DB_AESN_HpIntegrationObservation'))

    def test_actual_guarded_entry_first_request_only_and_global_flags_off(self):
        f = self.make()
        policy = list(f.rows('DB_AESN_CombatSnapshotV2'))
        self.inspect(f)
        self.migrate(f)
        self.assertEqual(2, len(f.rows('DB_AESN_HpMigration')))
        self.assertEqual(['AESN_HP_BIT_00001', 'AESN_HP_BIT_00064'], [a[1] for n, a in f.calls if n == 'RemoveStatus'])
        self.assertEqual(2, len(f.rows('DB_AESN_HpMigrationPause')))
        self.assertFalse(f.rows('DB_AESN_HpMigrationEnabled'))
        self.assertFalse(f.rows('DB_AESN_HpTotalIntegrationEnabled'))
        self.assertEqual(policy, f.rows('DB_AESN_CombatSnapshotV2'))
        before = list(f.calls)
        self.observe(f, 111, 69, 74, bits=(1, 2, 4, 8, 32))
        f.event('StatusRemoved', 'npc111', 'AESN_HP_BIT_00064', 'cause', 99)
        self.assertEqual(2, len([c for c in f.calls if c[0] == 'RemoveStatus']))
        self.assertEqual(2, len(f.hp_writes()))
        self.assertFalse([c for c in f.calls[len(before):] if c[0] == 'ApplyStatus'])

    def test_missing_ack_or_bad_maximum_never_commits(self):
        for defect in ('ack', 'maximum'):
            f = self.make()
            self.inspect(f)
            if defect == 'ack':
                f.facts['DB_AESN_HpIntegrationAck'].clear()
            else:
                self.observe(f, 1, 13, 29)
            self.migrate(f)
            self.assertFalse([r for r in f.rows('DB_AESN_HpTransaction') if r[1] == 'npc1'])
            self.assertTrue(f.rows('DB_AESN_HpIntegrationFailure'))

    def test_conflict_trace_late_callbacks_and_reloads_never_reissue(self):
        f = self.make()
        self.inspect(f)
        self.migrate(f)
        f.event('HitpointsChanged', 'npc1', 40.0)
        pending = list(f.rows('DB_AESN_HpTotalPending'))
        f.event('StatusRemoved', 'npc1', 'AESN_HP_BIT_00001', 'cause', 123)
        f.event('StatusApplied', 'npc1', 'REGAINHP_PEACE_NPC', 'cause', 124)
        f.run('PROC_AESN_HpIntegrationLoad')
        self.timer(f, 'npc1', 'Migrate')
        self.assertEqual(pending, f.rows('DB_AESN_HpTotalPending'))
        self.assertTrue(f.rows('DB_AESN_HpMigrationConflict'))
        trace = f.rows('DB_AESN_HpMigrationTrace')
        self.assertTrue([r for r in trace if r[3] == 'StatusRemoved' and r[-1] == 123])
        self.assertTrue([r for r in f.rows('DB_AESN_HpIntegrationTrace') if r[2] == 'StatusApplied' and r[3] == 'REGAINHP_PEACE_NPC'])
        self.assertEqual(2, len([c for c in f.calls if c[0] == 'RemoveStatus']))
        self.assertEqual(2, len(f.hp_writes()))

    def test_setup_native_configuration_acknowledgements_are_required(self):
        for query in ('CanFight', 'CanJoinCombat', 'QRY_SelfHealing_IsEnabled'):
            with self.subTest(query=query):
                f = self.make()
                self.start(f)
                if query == 'QRY_SelfHealing_IsEnabled':
                    f.native[query] = [('npc1',), ('npc111',)]
                else:
                    f.native[query] = [('npc1', 1), ('npc111', 0)]
                self.timer(f, 'npc1', 'Baseline')
                self.assertFalse([c for c in f.calls if c[0] == 'ApplyStatus' and c[1][0] == 'npc1'])
                self.assertTrue(f.rows('DB_AESN_HpIntegrationFailure'))

    def test_returned_host_existing_owner_and_duplicate_native_actor_are_rejected(self):
        for defect in ('host', 'owner', 'duplicate'):
            with self.subTest(defect=defect):
                f = self.make()
                if defect == 'host':
                    f.native['CreateAtObject'][0] = (TEMPLATE, 'host', 0, 1, '', 1, 'host')
                elif defect == 'owner':
                    f.add('DB_AESN_EnemyComponent', 'other', 'npc1', 'Stat', 'FOREIGN', fire=False)
                else:
                    f.native['CreateAtObject'][1] = (TEMPLATE, 'npc1', 0, 1, '', 1, 'npc1')
                self.start(f)
                self.assertLess(len(f.rows('DB_AESN_HpIntegrationFixture')), 2)
                self.assertTrue(f.rows('DB_AESN_HpIntegrationFailure'))

    def test_replayed_setup_helpers_cannot_mutate_after_inspection(self):
        f = self.make()
        self.inspect(f)
        before = list(f.calls)
        f.run('PROC_AESN_HpIntegrationAdvance', 'npc1', 'Baseline')
        f.run('PROC_AESN_HpIntegrationAdvance', 'npc1', 'Legacy')
        self.assertEqual(before, f.calls)

    def test_actual_savegame_loaded_order_has_no_inspect_transaction_to_reconcile(self):
        f = self.make()
        world = 'AESN_WorldHardenedOwner_da8f9f22-2125-45f1-ac0f-a8c264596f04'
        for name in ('DB_AESN_WorldContext', 'DB_AESN_CombatSnapshotV2'):
            f.facts[name] = [(world, *r[1:]) for r in f.rows(name)]
        self.inspect(f)
        self.assertFalse(f.rows('DB_AESN_HpApplicationHold'))
        f.event('SavegameLoaded')
        self.assertFalse(f.rows('DB_AESN_ReconcileEnemyPending'))
        self.assertFalse(f.rows('DB_AESN_HpApplicationHold'))
        for amount in BITS:
            self.timer(f, f'npc{amount}', 'Migrate')
        self.assertEqual(2, len(f.rows('DB_AESN_HpMigration')))
        self.assertFalse(f.rows('DB_AESN_HpApplicationHold'))
        self.assertFalse(f.rows('DB_AESN_HpIntegrationSeeding'))

    def test_missing_first_native_spawn_return_reload_is_diagnostic_and_no_retry(self):
        f = self.make()
        f.native['CreateAtObject'] = []
        self.start(f)
        f.run('PROC_AESN_HpIntegrationLoad')
        self.assertTrue(f.rows('DB_AESN_HpIntegrationFailure'))
        self.assertFalse(f.rows('DB_AESN_HpIntegrationFixture'))

    def test_preexisting_queue_or_quarantine_is_not_adopted(self):
        for name, args in (('DB_AESN_HpPlanQueued', ('other', 'npc1')),
                           ('DB_AESN_EnemyEligible', ('other', 'npc1')),
                           ('DB_AESN_HpTotalRetired', ('npc1', 'AESN_HP_TOTAL_1'))):
            f = self.make()
            f.add(name, *args, fire=False)
            self.start(f)
            self.assertFalse(f.rows('DB_AESN_HpIntegrationFixture'), name)
            self.assertEqual([args], f.rows(name))

    def test_interrupted_short_seeding_only_releases_its_own_setup_hold(self):
        f = self.make()
        self.start(f)
        f.add('DB_AESN_HpIntegrationSeeding', 'npc1', 'owner', fire=False)
        f.add('DB_AESN_HpApplicationHold', 'owner', 'npc1', fire=False)
        f.add('DB_AESN_HpApplicationHold', 'foreign', 'npc111', fire=False)
        f.run('PROC_AESN_HpIntegrationLoad')
        self.assertEqual([('foreign', 'npc111')], f.rows('DB_AESN_HpApplicationHold'))
        self.assertTrue(f.rows('DB_AESN_HpIntegrationFailure'))

    def test_status_failure_and_known_heal_spell_remain_visible_after_conflict(self):
        f = self.make()
        self.inspect(f)
        self.migrate(f)
        f.event('HitpointsChanged', 'npc1', 40.0)
        f.event('CastedSpell', 'npc1', 'Shout_RegainHP_Peace_NPC', 'Shout', 'None', 404)
        rows = f.rows('DB_AESN_HpIntegrationTrace')
        self.assertTrue([r for r in rows if r[2] == 'JournalConflict'])
        self.assertTrue([r for r in rows if r[2] == 'CastedSpell' and r[-1] == 404])

    def diagnostic_ready(self):
        f = self.make()
        self.inspect(f)
        f.run('PROC_AESN_HpIntegrationLoad')
        f.calls.clear()
        return f

    def diagnostic_failed(self, f):
        before = len(f.mutations)
        self.timer(f, 'npc1', 'Migrate')
        self.assertIn(('npc1', 'Migrate'), f.rows('DB_AESN_HpIntegrationFailure'))
        self.assertFalse(f.calls, 'diagnostics/failure must issue no native operations')
        self.assertFalse(f.rows('DB_AESN_HpTransaction'))
        self.assertFalse(f.rows('DB_AESN_HpMigration'))
        self.assertIn(('npc1', 'Migrate'), f.rows('DB_AESN_HpIntegrationDiagnosticCaptured'))
        changes = f.mutations[before:]
        failure = next(i for i, row in enumerate(changes)
                       if row[1] == 'DB_AESN_HpIntegrationFailure')
        reasons = [i for i, row in enumerate(changes)
                   if row[1] == 'DB_AESN_HpIntegrationPrerequisite']
        self.assertTrue(reasons)
        self.assertLess(max(reasons), failure, 'capture before Failure poisons Safe')
        self.assertNotIn(('npc1', 'Failure', '', 'Present'),
                         f.rows('DB_AESN_HpIntegrationPrerequisite'))

    def test_reload_diagnostics_native_mismatch_and_unavailable_are_distinct(self):
        for query in ('CanFight', 'CanJoinCombat', 'IsDead', 'IsInCombat', 'GetFaction',
                      'GetHitpoints', 'GetMaxHitpoints', 'GetHostCharacter'):
            for mode in ('Mismatch', 'Unavailable'):
                with self.subTest(query=query, mode=mode):
                    f = self.diagnostic_ready()
                    if query == 'GetHostCharacter':
                        f.native[query] = [('npc1',)] if mode == 'Mismatch' else []
                    else:
                        bad = {'GetFaction': 'different', 'GetHitpoints': 0,
                               'GetMaxHitpoints': 29}.get(query, 1)
                        f.native[query] = [r for r in f.native[query] if r[0] != 'npc1']
                        if mode == 'Mismatch':
                            f.native[query].append(('npc1', bad))
                    self.diagnostic_failed(f)
                    self.assertIn(('npc1', query, '', mode),
                                  f.rows('DB_AESN_HpIntegrationPrerequisite'))
                    self.assertNotIn(('npc1', query, '', 'Unavailable' if mode == 'Mismatch' else 'Mismatch'),
                                     f.rows('DB_AESN_HpIntegrationPrerequisite'))

    def test_reload_diagnostics_status_missing_ack_and_query_unavailable(self):
        for mode in ('Mismatch', 'Unavailable', 'AckMissing', 'UnexpectedBit'):
            with self.subTest(mode=mode):
                f = self.diagnostic_ready()
                status = 'AESN_HP_BIT_00001'
                if mode == 'AckMissing':
                    f.facts['DB_AESN_HpIntegrationAck'].remove(('npc1', status))
                elif mode == 'UnexpectedBit':
                    status = 'AESN_HP_BIT_00002'
                    f.native['HasActiveStatus'] = [r for r in f.native['HasActiveStatus'] if r[:2] != ('npc1', status)] + [('npc1', status, 1)]
                else:
                    f.native['HasActiveStatus'] = [r for r in f.native['HasActiveStatus'] if r[:2] != ('npc1', status)]
                    if mode == 'Mismatch':
                        f.native['HasActiveStatus'].append(('npc1', status, 0))
                self.diagnostic_failed(f)
                check = 'StatusAck' if mode == 'AckMissing' else 'UnexpectedBit' if mode == 'UnexpectedBit' else 'HasActiveStatus'
                result = 'Missing' if mode == 'AckMissing' else 'Present' if mode == 'UnexpectedBit' else mode
                self.assertIn(('npc1', check, status, result), f.rows('DB_AESN_HpIntegrationPrerequisite'))

    def test_reload_diagnostics_multiple_failures_values_and_no_postfailure_recapture(self):
        f = self.diagnostic_ready()
        f.native['CanFight'] = [('npc1', 1), ('npc111', 0)]
        f.native['GetFaction'] = [('npc1', 'changed'), ('npc111', 'friends'), ('host', 'friends')]
        f.native['QRY_SelfHealing_IsEnabled'].append(('npc1',))
        self.diagnostic_failed(f)
        reasons = f.rows('DB_AESN_HpIntegrationPrerequisite')
        for check in ('CanFight', 'GetFaction'):
            self.assertIn(('npc1', check, '', 'Mismatch'), reasons)
        self.assertIn(('npc1', 'HealingGood', '', 'Failed'), reasons)
        self.assertIn(('npc1', 'CanFight', 1), f.rows('DB_AESN_HpIntegrationDiagnosticValue'))
        self.assertIn(('npc1', 'SelfHealingPredicate', 1), f.rows('DB_AESN_HpIntegrationDiagnosticValue'))
        self.assertIn(('npc1', 'FactionActual', 'changed'), f.rows('DB_AESN_HpIntegrationDiagnosticGuid'))
        self.assertIn(('npc1', 'FactionExpected', 'friends'), f.rows('DB_AESN_HpIntegrationDiagnosticGuid'))
        before = list(f.mutations)
        f.run('PROC_AESN_HpIntegrationCapturePrerequisites', 'npc1', 'Migrate')
        self.assertEqual(before, f.mutations)

    def test_reload_diagnostics_ownership_context_and_ledger_prerequisites(self):
        cases = (
            ('DB_AESN_HpApplicationHold', ('foreign', 'npc1'), 'Unowned', 'DB_AESN_HpApplicationHold', 'Present'),
            ('DB_AESN_HpPlanQueued', ('foreign', 'npc1'), 'Unowned', 'DB_AESN_HpPlanQueued', 'Present'),
            ('DB_AESN_MergeInProgress', ('owner', 'other'), 'MergeOutgoing', '', 'Present'),
            ('DB_AESN_MergeInProgress', ('other', 'owner'), 'MergeIncoming', '', 'Present'),
            ('DB_AESN_CombatCleanupRequested', ('owner',), 'OwnerCleanup', '', 'Present'),
            ('DB_AESN_HpMigrationEnabled', (1,), 'AutomaticMigrationGate', '', 'Enabled'),
            ('DB_AESN_HpTotalIntegrationEnabled', (1,), 'TotalIntegrationGate', '', 'Enabled'),
            ('DB_AESN_WorldContext', ('other',), 'OtherWorld', '', 'Present'),
        )
        for name, args, check, detail, result in cases:
            with self.subTest(check=check, detail=detail):
                f = self.diagnostic_ready()
                f.add(name, *args, fire=False)
                self.diagnostic_failed(f)
                self.assertIn(('npc1', check, detail, result), f.rows('DB_AESN_HpIntegrationPrerequisite'))
        for name, check in (
                ('DB_AESN_HpIntegrationOwner', 'Owner'), ('DB_AESN_WorldContext', 'WorldContext'),
                ('DB_AESN_CombatSnapshotV2', 'SupportedPolicy'), ('DB_AESN_HpIntegrationBaseline', 'Baseline'),
                ('DB_AESN_HpIntegrationWoundSeen', 'WoundSeen'), ('DB_AESN_HpIntegrationSetterCount', 'SetterCountOne')):
            with self.subTest(missing=name):
                f = self.diagnostic_ready()
                f.facts[name].clear()
                self.diagnostic_failed(f)
                self.assertIn(('npc1', check, '', 'Missing'), f.rows('DB_AESN_HpIntegrationPrerequisite'))


if __name__ == '__main__':
    unittest.main()
