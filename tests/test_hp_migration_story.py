"""Task3A source checks, not qualification of native causality or ordering.

Native effects are never simulated. UI03 endpoint observations are literal;
per-bit intermediates below are explicitly synthetic adversarial inputs.
"""
import copy
import unittest

from tests.hp_story_fixture import GOALS, HpStoryFixture


class HpMigrationTests(unittest.TestCase):
    def make(self, delta=1, enabled=True, full_merge=False):
        names = ('40_HpTransaction', '45_HpTotal', '47_HpMigration',
                 '50_Applications', '55_Components', '60_Merge',
                 '65_Reconciliation', '66_WorldHardenedRuntime')
        if full_merge:
            names += ('20_Policy', '56_Relentless')
        f = HpStoryFixture([GOALS / ('AESN_' + n + '.txt') for n in names
                            if (GOALS / ('AESN_' + n + '.txt')).exists()])
        if enabled:
            f.add('DB_AESN_HpMigrationEnabled', 1, fire=False)
        f.add('DB_AESN_WorldContext', 'owner', fire=False)
        f.add('DB_AESN_WorldTracked', 'enemy', fire=False)
        f.add('DB_AESN_CombatSnapshotV2', 'owner', 2, 4, 4, 20, 5, 1,
              210, 1, 0, 2, 'Supported', fire=False)
        f.add('DB_AESN_ComponentApplication', 'owner', 'enemy', 1, 'FullyCommitted', fire=False)
        f.add('DB_AESN_EnemyComponent', 'owner', 'enemy', 'Stat', 'AESN_HARDENED_FOE_01', fire=False)
        f.add('DB_AESN_RelentlessLedger', 'owner', 2, 2, 1, 1, 1, 1, 1, fire=False)
        f.add('DB_AESN_HpTransaction', 'owner', 'enemy', 1, 'HPCommitted',
              20, 27, 100.0, 27 + delta, delta, delta, fire=False)
        bits = {0: (), 1: (1,), 111: (64, 32, 8, 4, 2, 1)}[delta]
        for b in bits:
            f.add('DB_AESN_EnemyHpBit', 'owner', 'enemy', b, f'AESN_HP_BIT_{b:05}', fire=False)
        self.observe(f, 13 if delta != 111 else 69, 27 + delta, bits)
        return f

    def observe(self, f, current, maximum, bits=(), total=None):
        active = {'AESN_HARDENED_FOE_01', 'AESN_HP_TOTAL_7', 'FOREIGN'}
        active.update(f'AESN_HP_BIT_{b:05}' for b in bits)
        if total:
            active.add(f'AESN_HP_TOTAL_{total}')
        f.observe(maximum, current, 50.0, active)
        known = active | {f'AESN_HP_BIT_{2**i:05}' for i in range(16)} | {'AESN_HP_TOTAL_1', 'AESN_HP_TOTAL_111'}
        f.native['HasActiveStatus'] = [('enemy', s, int(s in active)) for s in known]

    def start(self, f):
        f.run('PROC_AESN_TryHpMigration', 'owner', 'enemy')

    def journal(self, f):
        self.assertEqual(len(f.rows('DB_AESN_HpMigration')), 1)
        return f.rows('DB_AESN_HpMigration')[0]

    def assert_no_writes(self, f):
        self.assertFalse(f.hp_writes())

    def seed_journal(self, f, phase='Captured', current=13, maximum=28):
        f.facts['DB_AESN_HpTransaction'][0] = ('owner', 'enemy', 1, 'Migrating', 20, 27, 100.0, 28, 1, 1)
        f.add('DB_AESN_HpMigrationHold', 'enemy', 'owner', fire=False)
        f.add('DB_AESN_HpMigration', 'owner', 'enemy', phase, current, maximum, 27, 1, 'AESN_HP_TOTAL_1', 0, fire=False)
        f.add('DB_AESN_HpMigrationCheckpoint', 'owner', 'enemy', 'Captured', current, maximum, fire=False)
        f.add('DB_AESN_HpMigrationBit', 'owner', 'enemy', 1, 'AESN_HP_BIT_00001', 'Owned', fire=False)
        f.run('PROC_AESN_FreezeHpMigrationContext', 'owner', 'enemy')

    def test_default_off_never_mutates_or_acquires_hold(self):
        f = self.make(enabled=False)
        self.start(f)
        self.assertFalse(f.calls)
        self.assertFalse(f.rows('DB_AESN_HpMigrationHold'))
        self.assertEqual(f.rows('DB_AESN_HpTransaction')[0][2:4], (1, 'HPCommitted'))

    def test_capture_live_not_entry_and_record_intent_before_native_remove(self):
        f = self.make()
        before = {n: copy.deepcopy(f.rows(n)) for n in ('DB_AESN_CombatSnapshotV2', 'DB_AESN_EnemyComponent', 'DB_AESN_RelentlessLedger')}
        self.start(f)
        self.assertEqual(self.journal(f)[3:8], (13, 28, 27, 1, 'AESN_HP_TOTAL_1'))
        self.assertEqual(f.rows('DB_AESN_HpTransaction')[0][3], 'Migrating')
        self.assertEqual(f.rows('DB_AESN_HpMigrationBit')[0][-1], 'PendingRemove')
        self.assertEqual(f.rows('DB_AESN_HpMigrationHold'), [('enemy', 'owner')])
        self.assertEqual([c[1][1] for c in f.calls if c[0] == 'RemoveStatus'], ['AESN_HP_BIT_00001'])
        self.assertEqual(f.intent_at_call[0][1][0][2:4], ('MigrationRemoveLegacy', 'AESN_HP_BIT_00001'))
        self.assertEqual({n: f.rows(n) for n in before}, before)
        self.assert_no_writes(f)

    def test_literal_ui03_endpoints_stop_at_total_present_without_stale_restore(self):
        for delta, initial, removed, applied in ((1, (13, 28), (13, 27), (14, 28)), (111, (69, 138), (27, 27), (138, 138))):
            f = self.make(delta)
            self.start(f)
            bits = [64, 32, 8, 4, 2, 1] if delta == 111 else [1]
            maximum = initial[1]
            for bit in list(bits):
                bits.remove(bit)
                maximum -= bit
                # Synthetic per-bit checkpoints; final pair is captured UI03.
                self.observe(f, removed[0], maximum, bits)
                f.event('StatusRemoved', 'enemy', f'AESN_HP_BIT_{bit:05}', 'cause', 1)
            self.assertEqual(self.journal(f)[2], 'ApplyingTotal')
            self.observe(f, *applied, total=delta)
            f.event('StatusApplied', 'enemy', f'AESN_HP_TOTAL_{delta}', 'cause', 2)
            self.assertEqual(f.rows('DB_AESN_HpMigration')[0][2], 'TotalPresent')
            self.assertIn(('owner', 'enemy', 'NativeCausalityUnqualified'), f.rows('DB_AESN_HpMigrationConflict'))
            self.assertEqual(f.rows('DB_AESN_HpTransaction')[0][2:4], (1, 'Migrating'))
            self.assertTrue(f.rows('DB_AESN_HpMigrationHold'))
            self.assert_no_writes(f)

    def test_invalid_owned_set_or_live_state_never_starts(self):
        for kind in ('missing', 'wrong_id', 'wrong_value', 'sum', 'duplicate', 'max', 'dead', 'component'):
            f = self.make()
            if kind == 'missing':
                self.observe(f, 13, 28)
            elif kind == 'wrong_id':
                f.facts['DB_AESN_EnemyHpBit'] = [('owner', 'enemy', 1, 'FOREIGN')]
            elif kind == 'wrong_value':
                f.facts['DB_AESN_EnemyHpBit'] = [('owner', 'enemy', 2, 'AESN_HP_BIT_00001')]
            elif kind == 'sum':
                f.facts['DB_AESN_EnemyHpBit'].clear()
            elif kind == 'duplicate':
                f.add('DB_AESN_HpTransaction', 'other', 'enemy', 1, 'HPCommitted', 20, 27, 100.0, 28, 1, 1, fire=False)
            elif kind == 'max':
                self.observe(f, 13, 29, (1,))
            elif kind == 'dead':
                self.observe(f, 0, 28, (1,))
            elif kind == 'component':
                f.facts['DB_AESN_ComponentApplication'] = [('owner', 'enemy', 1, 'Applying')]
            self.start(f)
            self.assertFalse(f.rows('DB_AESN_HpMigration'), kind)
            self.assertFalse([c for c in f.calls if c[0] in ('ApplyStatus', 'RemoveStatus')], kind)

    def test_zero_is_metadata_only_and_rejects_owned_bits(self):
        f = self.make(0)
        self.start(f)
        self.assertEqual(f.rows('DB_AESN_HpTransaction')[0][2:4], (2, 'HPCommitted'))
        self.assertFalse(f.rows('DB_AESN_HpMigrationHold'))
        self.assertFalse(f.calls)

    def test_every_unclassified_intervention_freezes_original_pending(self):
        events = [('EnteredCombat', ('enemy', 'combat')), ('Dying', ('enemy',)),
                  ('Died', ('enemy',)), ('AttackedBy', ('enemy', 'owner', 'attacker', 'Fire', 1, 'cause', 10)),
                  ('HitpointsChanged', ('enemy', 50.0))]
        for event, args in events:
            f = self.make()
            self.start(f)
            pending = copy.deepcopy(f.rows('DB_AESN_HpTotalPending'))
            f.event(event, *args)
            self.observe(f, 13, 27)
            f.event('StatusRemoved', 'enemy', 'AESN_HP_BIT_00001', 'cause', 1)
            self.assertTrue(f.rows('DB_AESN_HpMigrationConflict'), event)
            self.assertEqual(f.rows('DB_AESN_HpTotalPending'), pending, event)
            self.assert_no_writes(f)

    def test_timeout_late_and_duplicate_events_do_not_reissue(self):
        f = self.make()
        self.start(f)
        self.assertTrue(f.rows('DB_AESN_HpTotalTimer'))
        timer = f.rows('DB_AESN_HpTotalTimer')[0][1]
        f.event('ObjectTimerFinished', 'enemy', timer)
        pending = copy.deepcopy(f.rows('DB_AESN_HpTotalPending'))
        self.observe(f, 13, 27)
        for _ in range(2):
            f.event('StatusRemoved', 'enemy', 'AESN_HP_BIT_00001', 'cause', 1)
        self.assertEqual(f.rows('DB_AESN_HpTotalPending'), pending)
        self.assertTrue(f.rows('DB_AESN_HpMigrationConflict'))
        self.assertFalse([c for c in f.calls if c[0] == 'ApplyStatus'])

    def test_captured_recovery_retains_untouched_legacy_without_native_actions(self):
        f = self.make()
        self.seed_journal(f)
        f.run('PROC_AESN_RecoverHpMigration', 'owner', 'enemy')
        self.assertFalse(f.rows('DB_AESN_HpMigration'))
        self.assertFalse(f.rows('DB_AESN_HpMigrationHold'))
        self.assertEqual(f.rows('DB_AESN_HpTransaction')[0][2:4], (1, 'HPCommitted'))
        self.assertFalse(f.calls)

    def test_reload_every_unverified_phase_is_held_and_cannot_cleanup_components(self):
        for phase in ('RemovingLegacy', 'LegacyRemoved', 'ApplyingTotal', 'TotalPresent', 'RestoringCurrent', 'UnknownFuturePhase'):
            f = self.make()
            self.seed_journal(f, phase)
            f.run('PROC_AESN_RecoverHpMigration', 'owner', 'enemy')
            f.run('PROC_AESN_CleanupEnemy', 'enemy', 'owner')
            f.run('PROC_AESN_DeleteHpRecords', 'owner', 'enemy')
            f.run('PROC_AESN_ReplanEnemy', 'owner', 'enemy')
            self.assertTrue(f.rows('DB_AESN_HpMigrationHold'), phase)
            self.assertTrue(f.rows('DB_AESN_HpMigrationConflict'), phase)
            self.assertTrue(f.rows('DB_AESN_EnemyComponent'), phase)
            self.assertFalse([c for c in f.calls if c[0] in ('ApplyStatus', 'RemoveStatus')], phase)
            self.assert_no_writes(f)

    def test_deferred_left_combat_rechecks_live_and_inactive_owner_is_not_converted(self):
        f = self.make()
        f.add('DB_Is_InCombat', 'enemy', 'combat', fire=False)
        self.start(f)
        self.assertEqual(f.rows('DB_AESN_HpMigrationDeferred'), [('owner', 'enemy')])
        f.facts['DB_Is_InCombat'].clear()
        self.observe(f, 12, 28, (1,))
        f.event('LeftCombat', 'enemy', 'combat')
        self.assertEqual(self.journal(f)[3], 12)
        g = self.make()
        g.facts['DB_AESN_WorldContext'].clear()
        g.native['CombatIsActive'] = [('owner', 0)]
        self.start(g)
        self.assertFalse(g.rows('DB_AESN_HpMigration'))

    def test_save_load_excludes_journal_from_generic_world_hold_and_cleanup(self):
        f = self.make()
        self.seed_journal(f, 'ApplyingTotal')
        f.event('SavegameLoaded')
        self.assertFalse(f.rows('DB_AESN_HpApplicationHold'))
        f.run('PROC_AESN_OpenCombatReconciliation', 'owner')
        self.assertFalse(f.rows('DB_AESN_ReconcileEnemyPending'))
        self.assertTrue(f.rows('DB_AESN_HpMigrationConflict'))
        self.assertFalse([c for c in f.calls if c[0] in ('ApplyStatus', 'RemoveStatus')])

    def test_transfer_moves_journal_and_deferred_only_under_existing_barrier(self):
        f = self.make()
        self.seed_journal(f, 'ApplyingTotal')
        f.add('DB_AESN_HpMigrationDeferred', 'owner', 'enemy', fire=False)
        names = ('DB_AESN_HpMigration', 'DB_AESN_HpMigrationBit', 'DB_AESN_HpMigrationCheckpoint',
                 'DB_AESN_HpMigrationPolicy', 'DB_AESN_HpMigrationComponent', 'DB_AESN_HpMigrationDeferred')
        f.run('PROC_AESN_TransferHpTotalFacts', 'owner', 'new', 'enemy')
        self.assertEqual(self.journal(f)[0], 'owner')
        f.add('DB_AESN_MergeInProgress', 'owner', 'new', fire=False)
        f.run('PROC_AESN_TransferHpTotalFacts', 'owner', 'new', 'enemy')
        for name in names:
            self.assertTrue(f.rows(name), name)
            self.assertEqual({row[0] for row in f.rows(name)}, {'new'}, name)
        self.assertEqual(f.rows('DB_AESN_HpMigrationHold'), [('enemy', 'new')])
        self.assertFalse(f.calls)

    def test_tracked_maintenance_retries_without_discovery_and_other_enemy_progresses(self):
        f = self.make()
        f.add('DB_AESN_HpMigrationDeferred', 'owner', 'enemy', fire=False)
        f.run('PROC_AESN_RetryTrackedHpMigrations', 'owner')
        self.assertTrue(f.rows('DB_AESN_HpMigrationHold'))
        f.add('DB_AESN_HpTransaction', 'owner', 'other', 1, 'HPCommitted', 10, 20, 50.0, 20, 0, 0, fire=False)
        f.add('DB_AESN_ComponentApplication', 'owner', 'other', 1, 'FullyCommitted')
        self.assertIn(('other',), f.rows('DB_AESN_WorldHardenedReady'))

    def test_pause_and_changed_maximum_do_not_allow_next_request(self):
        f = self.make()
        f.add('DB_AESN_HpMigrationPause', 'enemy', fire=False)
        self.start(f)
        self.assertEqual(self.journal(f)[2], 'Captured')
        self.assertFalse(f.calls)
        f.facts['DB_AESN_HpMigrationPause'].clear()
        self.observe(f, 13, 29, (1,))
        f.run('PROC_AESN_AdvanceHpMigration', 'owner', 'enemy')
        self.assertTrue(f.rows('DB_AESN_HpMigrationConflict'))
        self.assertFalse([c for c in f.calls if c[0] == 'RemoveStatus'])

    def test_verified_recovery_exact_metadata_commit_never_calls_setter(self):
        f = self.make()
        self.seed_journal(f, 'Verified')
        f.facts['DB_AESN_EnemyHpBit'].clear()
        f.facts['DB_AESN_HpMigrationBit'] = [('owner', 'enemy', 1, 'AESN_HP_BIT_00001', 'Removed')]
        f.add('DB_AESN_HpMigrationCheckpoint', 'owner', 'enemy', 'Verified', 13, 28, fire=False)
        f.add('DB_AESN_HpMigrationCheckpoint', 'owner', 'enemy', 'TotalPresent', 14, 28, fire=False)
        self.observe(f, 13, 28, total=1)
        f.run('PROC_AESN_RecoverHpMigration', 'owner', 'enemy')
        self.assertEqual(f.rows('DB_AESN_HpTransaction')[0][2:4], (2, 'HPCommitted'))
        self.assertEqual(f.rows('DB_AESN_EnemyHpTotal'), [('owner', 'enemy', 1, 'AESN_HP_TOTAL_1')])
        self.assertFalse(f.rows('DB_AESN_HpMigrationHold'))
        self.assertFalse(f.calls)

    def test_removal_ack_rejects_changed_maximum_and_keeps_exact_intent(self):
        f = self.make()
        self.start(f)
        pending = copy.deepcopy(f.rows('DB_AESN_HpTotalPending'))
        self.observe(f, 13, 26)
        f.event('StatusRemoved', 'enemy', 'AESN_HP_BIT_00001', 'cause', 1)
        self.assertEqual(f.rows('DB_AESN_HpTotalPending'), pending)
        self.assertTrue(f.rows('DB_AESN_EnemyHpBit'))
        self.assertTrue(f.rows('DB_AESN_HpMigrationConflict'))
        self.assertFalse([c for c in f.calls if c[0] == 'ApplyStatus'])

    def test_missing_owned_bit_duplicate_owner_or_changed_policy_blocks_advance(self):
        for defect in ('bit', 'owner', 'policy', 'component', 'current', 'unowned_total'):
            f = self.make()
            f.add('DB_AESN_HpMigrationPause', 'enemy', fire=False)
            self.start(f)
            f.facts['DB_AESN_HpMigrationPause'].clear()
            if defect == 'bit':
                f.facts['DB_AESN_EnemyHpBit'].clear()
            elif defect == 'owner':
                f.add('DB_AESN_HpTransaction', 'other', 'enemy', 1, 'HPCommitted', 20, 27, 100.0, 28, 1, 1, fire=False)
            elif defect == 'policy':
                f.facts['DB_AESN_CombatSnapshotV2'].clear()
            elif defect == 'component':
                f.facts['DB_AESN_EnemyComponent'].clear()
            elif defect == 'current':
                self.observe(f, 12, 28, (1,))
            else:
                self.observe(f, 13, 28, (1,), total=1)
            f.run('PROC_AESN_AdvanceHpMigration', 'owner', 'enemy')
            self.assertTrue(f.rows('DB_AESN_HpMigrationConflict'), defect)
            self.assertFalse([c for c in f.calls if c[0] in ('ApplyStatus', 'RemoveStatus')], defect)

    def test_malformed_captured_or_verified_snapshots_never_retire_hold(self):
        for phase in ('Captured', 'Verified'):
            for defect in ('sum', 'status', 'transaction', 'checkpoint', 'current', 'pending', 'extra_bit'):
                f = self.make()
                self.seed_journal(f, phase)
                if phase == 'Verified':
                    f.facts['DB_AESN_EnemyHpBit'].clear()
                    f.facts['DB_AESN_HpMigrationBit'] = [('owner', 'enemy', 1, 'AESN_HP_BIT_00001', 'Removed')]
                    f.add('DB_AESN_HpMigrationCheckpoint', 'owner', 'enemy', 'Verified', 13, 28, fire=False)
                    f.add('DB_AESN_HpMigrationCheckpoint', 'owner', 'enemy', 'TotalPresent', 14, 28, fire=False)
                    self.observe(f, 13, 28, total=1)
                if defect == 'sum':
                    f.facts['DB_AESN_HpMigrationBit'].clear()
                    f.facts['DB_AESN_EnemyHpBit'].clear()
                elif defect == 'status':
                    row = f.rows('DB_AESN_HpMigration')[0]
                    f.facts['DB_AESN_HpMigration'] = [row[:7] + ('FOREIGN',) + row[8:]]
                elif defect == 'transaction':
                    f.facts['DB_AESN_HpTransaction'].clear()
                elif defect == 'checkpoint':
                    f.facts['DB_AESN_HpMigrationCheckpoint'].clear()
                elif defect == 'current':
                    self.observe(f, 12, 28, (1,) if phase == 'Captured' else (), total=1 if phase == 'Verified' else None)
                elif defect == 'pending':
                    f.add('DB_AESN_HpTotalPending', 'owner', 'enemy', 'MigrationApplyTotal', 'AESN_HP_TOTAL_1', 4, fire=False)
                else:
                    f.add('DB_AESN_HpMigrationBit', 'owner', 'enemy', 2, 'AESN_HP_BIT_00002', 'Owned', fire=False)
                f.run('PROC_AESN_RecoverHpMigration', 'owner', 'enemy')
                self.assertTrue(f.rows('DB_AESN_HpMigrationHold'), (phase, defect))
                self.assertTrue(f.rows('DB_AESN_HpMigrationConflict'), (phase, defect))
                self.assert_no_writes(f)

    def test_trace_preserves_native_action_phase_and_pending_identity(self):
        f = self.make()
        self.start(f)
        self.observe(f, 13, 27)
        f.event('StatusRemoved', 'enemy', 'AESN_HP_BIT_00001', 'cause', 42)
        self.assertTrue(f.rows('DB_AESN_HpMigrationTrace'))
        matching = [row for row in f.rows('DB_AESN_HpMigrationTrace') if row[3] == 'StatusRemoved']
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0][4:], ('AESN_HP_BIT_00001', 13, 27, 'RemovingLegacy',
                                         'MigrationRemoveLegacy', 'AESN_HP_BIT_00001', 1, 42))

    def test_epoch_exhaustion_or_failed_apply_keeps_original_journal_held(self):
        f = self.make()
        f.add('DB_AESN_HpTotalEpoch', 'enemy', 2147483647, fire=False)
        self.start(f)
        self.assertFalse([c for c in f.calls if c[0] in ('RemoveStatus', 'ApplyStatus')])
        self.assertTrue(f.rows('DB_AESN_HpMigrationConflict'))
        g = self.make()
        self.start(g)
        self.observe(g, 13, 27)
        g.event('StatusRemoved', 'enemy', 'AESN_HP_BIT_00001', 'cause', 1)
        pending = copy.deepcopy(g.rows('DB_AESN_HpTotalPending'))
        g.event('StatusAttemptFailed', 'enemy', 'AESN_HP_TOTAL_1', 'cause', 2)
        self.assertEqual(g.rows('DB_AESN_HpTotalPending'), pending)
        self.assertTrue(g.rows('DB_AESN_HpMigrationConflict'))

    def test_duplicate_journal_or_unexpected_total_blocks_capture_recovery(self):
        for defect in ('journal', 'total', 'component_state'):
            f = self.make()
            self.seed_journal(f)
            if defect == 'journal':
                f.add('DB_AESN_HpMigration', 'owner', 'enemy', 'Captured', 12, 28, 27, 1, 'AESN_HP_TOTAL_1', 0, fire=False)
            elif defect == 'total':
                f.add('DB_AESN_EnemyHpTotal', 'owner', 'enemy', 7, 'AESN_HP_TOTAL_7', fire=False)
            else:
                f.add('DB_AESN_ComponentApplication', 'owner', 'enemy', 1, 'Applying', fire=False)
            f.run('PROC_AESN_RecoverHpMigration', 'owner', 'enemy')
            self.assertTrue(f.rows('DB_AESN_HpMigrationHold'), defect)
            self.assertTrue(f.rows('DB_AESN_HpMigrationConflict'), defect)
            self.assertEqual(f.rows('DB_AESN_HpTransaction')[0][3], 'Migrating', defect)

    def test_manual_target_entry_does_not_enable_global_scheduler(self):
        f = self.make(enabled=False)
        f.run('PROC_AESN_ValidateHpMigration', 'owner', 'enemy')
        self.assertTrue(f.rows('DB_AESN_HpMigrationHold'))
        self.assertFalse(f.rows('DB_AESN_HpMigrationEnabled'))
        self.assertEqual(self.journal(f)[2], 'RemovingLegacy')

    def test_duplicate_ack_and_post_conflict_callbacks_are_observations_only(self):
        f = self.make()
        self.start(f)
        self.observe(f, 13, 27)
        f.event('StatusRemoved', 'enemy', 'AESN_HP_BIT_00001', 'cause', 42)
        pending = copy.deepcopy(f.rows('DB_AESN_HpTotalPending'))
        f.event('StatusRemoved', 'enemy', 'AESN_HP_BIT_00001', 'cause', 42)
        self.assertEqual(f.rows('DB_AESN_HpTotalPending'), pending)
        f.event('HitpointsChanged', 'enemy', 50.0)
        self.observe(f, 14, 28, total=1)
        f.event('StatusApplied', 'enemy', 'AESN_HP_TOTAL_1', 'cause', 43)
        self.assertEqual(f.rows('DB_AESN_HpTotalPending'), pending)
        self.assertTrue(any(row[3] == 'StatusApplied' and row[-1] == 43 for row in f.rows('DB_AESN_HpMigrationTrace')))
        f.run('PROC_AESN_DumpHpMigrationTrace', 'owner', 'enemy')
        self.assertTrue(any(c[0] == 'DebugLog' and 'sequence=' in c[1][0] for c in f.calls))
        self.assert_no_writes(f)

    def test_all_transient_save_snapshots_keep_pending_and_recover_without_writes(self):
        for phase in ('Captured', 'RemovingLegacy', 'LegacyRemoved', 'ApplyingTotal', 'TotalPresent'):
            f = self.make()
            self.seed_journal(f, phase)
            if phase != 'Captured':
                f.add('DB_AESN_HpTotalPending', 'owner', 'enemy', 'MigrationRemoveLegacy', 'AESN_HP_BIT_00001', 4, fire=False)
            pending = copy.deepcopy(f.rows('DB_AESN_HpTotalPending'))
            f.event('SavegameLoaded')
            self.assertEqual(f.rows('DB_AESN_HpTotalPending'), pending, phase)
            self.assert_no_writes(f)
            self.assertFalse([c for c in f.calls if c[0] in ('RemoveStatus', 'ApplyStatus')], phase)

    def test_quiescent_damage_or_healing_without_callback_blocks_next_dispatch(self):
        for phase, changed in (('RemovingLegacy', 68), ('RemovingLegacy', 70),
                               ('LegacyRemoved', 12), ('LegacyRemoved', 14)):
            with self.subTest(phase=phase, changed=changed):
                f = self.make(111 if phase == 'RemovingLegacy' else 1)
                self.start(f)
                f.add('DB_AESN_HpMigrationPause', 'enemy', fire=False)
                if phase == 'RemovingLegacy':
                    self.observe(f, 69, 74, (32, 8, 4, 2, 1))
                    f.event('StatusRemoved', 'enemy', 'AESN_HP_BIT_00064', 'cause', 1)
                else:
                    self.observe(f, 13, 27)
                    f.event('StatusRemoved', 'enemy', 'AESN_HP_BIT_00001', 'cause', 1)
                    # Reach the phase-only checkpoint without issuing the total.
                    f.run('PROC_AESN_RemoveNextMigrationBit', 'owner', 'enemy', -1)
                self.assertEqual(self.journal(f)[2], phase)
                self.assertFalse(f.rows('DB_AESN_HpTotalPending'))
                before = copy.deepcopy(f.rows('DB_AESN_HpMigrationCheckpoint'))
                f.facts['DB_AESN_HpMigrationPause'].clear()
                self.observe(f, changed, 74 if phase == 'RemovingLegacy' else 27,
                             (32, 8, 4, 2, 1) if phase == 'RemovingLegacy' else ())
                f.calls.clear()
                f.run('PROC_AESN_AdvanceHpMigration', 'owner', 'enemy')
                self.assertTrue(f.rows('DB_AESN_HpMigrationConflict'))
                self.assertEqual(f.rows('DB_AESN_HpMigrationCheckpoint'), before)
                self.assertTrue(f.rows('DB_AESN_HpMigrationHold'))
                self.assertFalse([c for c in f.calls if c[0] in ('RemoveStatus', 'ApplyStatus')])
                self.assert_no_writes(f)

    def test_recovery_rejects_valid_plus_contradictory_or_wrong_phase_checkpoints(self):
        cases = [('Captured', 'Captured', 12, 28), ('Captured', 'Captured', 13, 29),
                 ('Captured', 'Verified', 13, 28), ('Verified', 'Captured', 12, 28),
                 ('Verified', 'Verified', 12, 28), ('Verified', 'Verified', 13, 29),
                 ('Verified', 'TotalPresent', 13, 28), ('Verified', 'TotalPresent', 14, 29),
                 ('Verified', 'LegacyRemoved', 13, 28), ('Verified', 'UnknownPhase', 13, 28)]
        for phase, extra_phase, current, maximum in cases:
            with self.subTest(phase=phase, extra_phase=extra_phase, current=current, maximum=maximum):
                f = self.make()
                self.seed_journal(f, phase)
                if phase == 'Verified':
                    f.facts['DB_AESN_EnemyHpBit'].clear()
                    f.facts['DB_AESN_HpMigrationBit'] = [('owner', 'enemy', 1, 'AESN_HP_BIT_00001', 'Removed')]
                    f.add('DB_AESN_HpMigrationCheckpoint', 'owner', 'enemy', 'Verified', 13, 28, fire=False)
                    f.add('DB_AESN_HpMigrationCheckpoint', 'owner', 'enemy', 'TotalPresent', 14, 28, fire=False)
                    self.observe(f, 13, 28, total=1)
                f.add('DB_AESN_HpMigrationCheckpoint', 'owner', 'enemy', extra_phase, current, maximum, fire=False)
                before = {n: copy.deepcopy(f.rows(n)) for n in ('DB_AESN_HpMigration', 'DB_AESN_HpMigrationCheckpoint',
                           'DB_AESN_HpMigrationBit', 'DB_AESN_HpTransaction')}
                f.run('PROC_AESN_RecoverHpMigration', 'owner', 'enemy')
                self.assertTrue(f.rows('DB_AESN_HpMigrationConflict'))
                self.assertTrue(f.rows('DB_AESN_HpMigrationHold'))
                self.assertEqual({n: f.rows(n) for n in before}, before)
                self.assertFalse(f.rows('DB_AESN_EnemyHpTotal'))
                self.assertFalse(f.calls)

    def test_full_merge_journal_pending_uncertain_trace_and_destination_conflict(self):
        for conflict in (False, True):
            with self.subTest(conflict=conflict):
                f = self.make(full_merge=True)
                f.native['CombatIsActive'] = [('owner', 1), ('new', 1)]
                self.start(f)
                timer = f.rows('DB_AESN_HpTotalTimer')[0][1]
                f.event('ObjectTimerFinished', 'enemy', timer)
                self.assertTrue(f.rows('DB_AESN_HpTotalUncertain'))
                self.assertTrue(f.rows('DB_AESN_HpMigrationTrace'))
                if conflict:
                    f.add('DB_AESN_HpMigrationDeferred', 'new', 'enemy', fire=False)
                f.add('DB_AESN_MergeInProgress', 'owner', 'new', fire=False)
                names = ('DB_AESN_HpMigration', 'DB_AESN_HpMigrationBit', 'DB_AESN_HpMigrationCheckpoint',
                         'DB_AESN_HpMigrationConflict', 'DB_AESN_HpMigrationPolicy', 'DB_AESN_HpMigrationComponent',
                         'DB_AESN_HpMigrationTrace', 'DB_AESN_HpTotalPending', 'DB_AESN_HpTotalUncertain',
                         'DB_AESN_HpMigrationDeferred',
                         'DB_AESN_HpTransaction', 'DB_AESN_EnemyHpBit', 'DB_AESN_EnemyComponent', 'DB_AESN_ComponentApplication',
                         'DB_AESN_CombatSnapshotV2')
                before = {n: copy.deepcopy(f.rows(n)) for n in names}
                fixed = {n: copy.deepcopy(f.rows(n)) for n in ('DB_AESN_HpTotalEpoch', 'DB_AESN_HpTotalTimer',
                         'DB_AESN_HpMigrationTraceSequence')}
                f.calls.clear()
                f.run('PROC_AESN_MergeCombat', 'owner', 'new')
                self.assertEqual({n: f.rows(n) for n in fixed}, fixed)
                self.assertFalse([c for c in f.calls if c[0] in ('RemoveStatus', 'ApplyStatus')])
                self.assert_no_writes(f)
                if conflict:
                    self.assertEqual({n: f.rows(n) for n in before}, before)
                    self.assertEqual(f.rows('DB_AESN_HpMigrationDeferred'), [('new', 'enemy')])
                    self.assertEqual(f.rows('DB_AESN_MergeInProgress'), [('owner', 'new')])
                    self.assertEqual(f.rows('DB_AESN_HpMigrationHold'), [('enemy', 'owner')])
                    self.assertTrue(f.rows('DB_AESN_MergeHpConflict'))
                else:
                    for name in names:
                        self.assertEqual(f.rows(name), [('new',) + row[1:] for row in before[name]], name)
                    self.assertEqual(f.rows('DB_AESN_HpMigrationHold'), [('enemy', 'new')])
                    self.assertFalse(f.rows('DB_AESN_MergeInProgress'))
                    self.assertFalse(f.rows('DB_AESN_MergeHpConflict'))


if __name__ == '__main__':
    unittest.main()
