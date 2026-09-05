"""Cross-goal source execution; native observations are explicit, not simulated."""
import unittest
from tests.hp_story_fixture import GOALS, HpStoryFixture
from tools.poc_model import plan_hp_target


class HpTotalIntegrationTests(unittest.TestCase):
    def make(self, total=True, owner='owner', percent=210, tier=1):
        f = HpStoryFixture([GOALS / n for n in (
            'AESN_00_Init.txt', 'AESN_20_Policy.txt', 'AESN_56_Relentless.txt',
            'AESN_40_HpTransaction.txt', 'AESN_45_HpTotal.txt',
            'AESN_50_Applications.txt', 'AESN_55_Components.txt',
            'AESN_60_Merge.txt', 'AESN_65_Reconciliation.txt',
            'AESN_66_WorldHardenedRuntime.txt')])
        f.observe(101, 50, 49.5)
        f.add('DB_AESN_SchemaVersion', 2, fire=False)
        f.native['HasActiveStatus'] += [('enemy', f'AESN_HP_BIT_{b:05}', 0)
                                       for b in (1, 2, 4, 8, 16, 32, 64, 128)]
        f.native['CombatIsActive'] = [(owner, 1)]
        if not total:
            # Legacy-focused tests deliberately model a pre-rollout save.
            f.facts['DB_AESN_HpTotalIntegrationEnabled'].clear()
        f.add('DB_AESN_CombatSnapshotV2', owner, 2, 4, 4, 20, 5,
              tier, percent, 1, 1, 1, 'Supported', fire=False)
        return f

    def test_actual_init_and_upgrade_activation_enable_v2_without_migration(self):
        # The actual INIT goal is loaded: fresh saves receive the static gate,
        # while established saves receive it from the SavegameLoaded hook.
        fresh = self.make(tier=0)
        self.assertEqual(fresh.rows('DB_AESN_HpTotalIntegrationEnabled'), [(1,)])
        self.assertFalse(fresh.rows('DB_AESN_HpMigrationEnabled'))
        self.assertFalse(fresh.rows('DB_AESN_HpMigrationHold'))
        self.plan(fresh)
        self.assertEqual(fresh.rows('DB_AESN_HpTransaction')[0][2], 2)

        established = self.make(tier=0)
        established.facts['DB_AESN_HpTotalIntegrationEnabled'].clear()
        established.facts['DB_AESN_HpTransaction'] = [
            ('owner', 'enemy', 1, 'Planned', 50, 101, 49.5, 102, 1, 0),
            ('owner', 'enemy', 1, 'HPCommitted', 50, 101, 49.5, 102, 1, 1)
        ]
        established.facts['DB_AESN_EnemyHpBit'] = [
            ('owner', 'enemy', 1, 'AESN_HP_BIT_00001')
        ]
        established.observe(102, 50, 49.5, active=('AESN_HP_BIT_00001',))
        transactions_before = list(established.rows('DB_AESN_HpTransaction'))
        ownership_before = list(established.rows('DB_AESN_EnemyHpBit'))
        established.event('SavegameLoaded')
        established.event('SavegameLoaded')
        self.assertEqual(established.rows('DB_AESN_HpTotalIntegrationEnabled'), [(1,)])
        self.assertEqual(established.rows('DB_AESN_HpTransaction'), transactions_before)
        self.assertEqual(established.rows('DB_AESN_EnemyHpBit'), ownership_before)
        self.assertEqual(established.native['GetHitpoints'], [('enemy', 50)])
        self.assertEqual(established.native['GetMaxHitpoints'], [('enemy', 102)])
        self.assertFalse(established.rows('DB_AESN_HpMigrationEnabled'))
        self.assertFalse(established.rows('DB_AESN_HpMigrationHold'))
        self.assertFalse([call for call in established.calls if call[0] in
                          ('ApplyStatus', 'RemoveStatus', 'SetHitpoints', 'SetHitpointsPercentage')])

    def plan(self, f, owner='owner'):
        f.proc('PROC_AESN_PlanEnemy', 'enemy', owner)

    def total_ack(self, f, delta=111, maximum=212):
        f.observe(maximum, 105, 49.5, active=(f'AESN_HP_TOTAL_{delta}',))
        f.event('StatusApplied', 'enemy', f'AESN_HP_TOTAL_{delta}', 'cause', 1)

    def stable(self, f, owner='owner', delta=111):
        self.plan(f, owner)
        if delta:
            self.total_ack(f, delta, 101 + delta)
        f.event('StatusApplied', 'enemy', 'AESN_HARDENED_FOE_01', 'cause', 1)
        f.observe(101 + delta, 50, 40.0,
                  active=((f'AESN_HP_TOTAL_{delta}',) if delta else ()) + ('AESN_HARDENED_FOE_01',))
        f.calls.clear()

    def test_math_fixture_truncates_without_changing_observations(self):
        f = self.make()
        self.assertTrue(list(f.solutions(['IntegerProduct(101, 210, 21210)',
                                         'IntegerDivide(21210, 100, 212)',
                                         'IntegerDivide(-5, 2, -2)'], {})))
        self.assertEqual(f.native['GetMaxHitpoints'], [('enemy', 101)])

    def test_planner_uses_exact_total_only_when_activated_and_queues_last(self):
        for total in (False, True):
            f = self.make(total)
            self.plan(f)
            row = f.rows('DB_AESN_HpTransaction')[0]
            self.assertEqual((row[2], row[7], row[8]), (2 if total else 1, 212, 111))
            self.assertEqual(f.rows('DB_AESN_HpTotalDesired'),
                             [('owner', 'enemy', 111, 'AESN_HP_TOTAL_111')] if total else [])
            self.assertEqual(bool(f.rows('DB_AESN_HpDesiredBit')), not total)
            self.assertEqual(len([c for c in f.calls if c[0] == 'ApplyStatus']), 1)
            self.assertEqual(f.native['GetMaxHitpoints'], [('enemy', 101)])

    def test_total_ack_drives_real_components_and_world_readiness(self):
        f = self.make(owner='world')
        f.add('DB_AESN_WorldContext', 'world', fire=False)
        f.add('DB_AESN_WorldTracked', 'enemy', fire=False)
        self.stable(f, 'world')
        self.assertEqual(f.rows('DB_AESN_WorldHardenedReady'), [('enemy',)])
        self.assertEqual(f.rows('DB_AESN_ComponentApplication'),
                         [('world', 'enemy', 1, 'FullyCommitted')])

    def test_zero_cleanup_retires_without_native_mutation(self):
        f = self.make(percent=100, tier=0)
        self.plan(f)
        f.proc('PROC_AESN_CleanupEnemy', 'enemy', 'owner')
        self.assertFalse(f.rows('DB_AESN_HpTransaction'))
        self.assertFalse([c for c in f.calls if c[0] in ('ApplyStatus', 'RemoveStatus')])
        self.assertFalse(f.hp_writes())

    def test_total_cleanup_preserves_owned_until_ack_and_unrelated_sources(self):
        f = self.make(tier=0)
        self.plan(f)
        self.total_ack(f)
        f.observe(232, 116, 50.0, active=('AESN_HP_TOTAL_111', 'FOREIGN'))
        f.calls.clear()
        f.proc('PROC_AESN_CleanupEnemy', 'enemy', 'owner')
        self.assertEqual([c[1][1] for c in f.calls if c[0] == 'RemoveStatus'], ['AESN_HP_TOTAL_111'])
        self.assertTrue(f.rows('DB_AESN_EnemyHpTotal'))
        f.observe(121, 60, 49.0, active=('FOREIGN',))
        f.event('StatusRemoved', 'enemy', 'AESN_HP_TOTAL_111', 'cause', 1)
        self.assertFalse(f.rows('DB_AESN_HpTransaction'))
        self.assertEqual(f.hp_writes(), [('SetHitpointsPercentage', ('enemy', 50.0, 'Guaranteed'))])

    def test_unresolved_total_cannot_be_deleted_or_finalize_combat(self):
        f = self.make(tier=0)
        self.plan(f)
        pending = list(f.rows('DB_AESN_HpTotalPending'))
        f.proc('PROC_AESN_DeleteHpRecords', 'owner', 'enemy')
        self.assertTrue(f.rows('DB_AESN_HpTransaction'))
        self.assertEqual(f.rows('DB_AESN_HpTotalPending'), pending)
        f.facts['DB_AESN_HpTransaction'].clear()  # malformed interrupted-save input
        f.add('DB_AESN_CombatCleanupRequested', 'owner')
        self.assertTrue(f.rows('DB_AESN_CombatCleanupRequested'))

    def test_reload_is_observation_only_and_preserves_relentless(self):
        for world in (False, True):
            f = self.make()
            if world:
                f.add('DB_AESN_WorldContext', 'owner', fire=False)
            self.stable(f)
            f.add('DB_AESN_RelentlessLedger', 'owner', 2, 1, 1, 1, 1, 1, 1, fire=False)
            before = list(f.rows('DB_AESN_RelentlessLedger'))
            for _ in range(2):
                f.event('SavegameLoaded')
                f.tick()
                f.event('ObjectTimerFinished', 'enemy', 'AESN_RECONCILE_ENEMY')
                self.assertFalse(f.rows('DB_AESN_HpApplicationHold'))
                self.assertIn(('owner', 'enemy', 'RETAIN', 'ValidWorldCommit' if world else 'ValidActiveCommit'),
                              f.rows('DB_AESN_ReconcileResult'))
            self.assertFalse([c for c in f.calls if c[0] in ('ApplyStatus', 'RemoveStatus')])
            self.assertFalse(f.hp_writes())
            self.assertEqual(f.rows('DB_AESN_RelentlessLedger'), before)

    def test_transfer_preserves_pending_epoch_timer_and_does_not_replay(self):
        f = self.make(tier=0)
        self.plan(f)
        timer = list(f.rows('DB_AESN_HpTotalTimer'))
        epoch = list(f.rows('DB_AESN_HpTotalEpoch'))
        f.add('DB_AESN_MergeInProgress', 'owner', 'new', fire=False)
        f.calls.clear()
        f.run('PROC_AESN_TransferHpTotalFacts', 'owner', 'new', 'enemy')
        self.assertEqual(f.rows('DB_AESN_HpTransaction')[0][0], 'new')
        self.assertEqual(f.rows('DB_AESN_HpTotalPending')[0][0], 'new')
        self.assertEqual(f.rows('DB_AESN_HpTotalDesired')[0][0], 'new')
        self.assertEqual(f.rows('DB_AESN_HpTotalTimer'), timer)
        self.assertEqual(f.rows('DB_AESN_HpTotalEpoch'), epoch)
        self.assertFalse(f.calls)

    def test_model_exposes_total_without_changing_legacy_bits_or_math(self):
        plan = plan_hp_target(50, 101, 212, alive=True)
        self.assertEqual((plan.target_maximum, plan.delta, plan.restored_current), (212, 111, 105))
        self.assertEqual(getattr(plan, 'total_status', None), 'AESN_HP_TOTAL_111')
        self.assertEqual(sum(plan.bits), 111)

    def test_conflicting_merge_keeps_policy_components_and_hp_intact(self):
        f = self.make()
        self.stable(f)
        f.transaction(owner='new', version=1)
        f.add('DB_AESN_CombatSnapshotV2', 'new', 2, 6, 6, 30, 5, 2, 230, 1, 1, 1, 'Supported', fire=False)
        names = ('DB_AESN_CombatSnapshotV2', 'DB_AESN_HpTransaction', 'DB_AESN_EnemyComponent')
        before = {n: list(f.rows(n)) for n in names}
        f.add('DB_AESN_MergeInProgress', 'owner', 'new', fire=False)
        f.run('PROC_AESN_MergeCombat', 'owner', 'new')
        self.assertEqual({n: f.rows(n) for n in names}, before)
        self.assertTrue(f.rows('DB_AESN_MergeHpConflict'))
        self.assertEqual(f.rows('DB_AESN_MergeInProgress'), [('owner', 'new')])
        self.assertFalse([c for c in f.calls if c[0] in ('ApplyStatus', 'RemoveStatus')])

    def test_eligibility_survives_transitions_without_duplicate_planning(self):
        for total in (False, True):
            f = self.make(total, tier=0)
            f.add('DB_AESN_EnemyEligible', 'owner', 'enemy')
            self.assertEqual(len(f.rows('DB_AESN_HpTransaction')), 1)
            self.assertEqual(len([c for c in f.calls if c[0] == 'ApplyStatus']), 1)

    def test_zero_to_positive_replan_and_positive_to_zero_keep_original_capture(self):
        for old_percent, new_percent in ((100, 210), (210, 100)):
            f = self.make(percent=old_percent, tier=0)
            self.plan(f)
            if old_percent == 210:
                self.total_ack(f)
            f.observe(101 if old_percent == 100 else 212, 40, 37.0,
                      active=() if old_percent == 100 else ('AESN_HP_TOTAL_111',))
            row = f.rows('DB_AESN_CombatSnapshotV2')[0]
            f.facts['DB_AESN_CombatSnapshotV2'] = [row[:7] + (new_percent,) + row[8:]]
            f.calls.clear()
            f.proc('PROC_AESN_ReplanEnemy', 'owner', 'enemy')
            if old_percent == 210:
                self.assertFalse(f.hp_writes())
                f.observe(101, 40, 20.0)
                f.event('StatusRemoved', 'enemy', 'AESN_HP_TOTAL_111', 'cause', 1)
            else:
                self.assertFalse([c for c in f.calls if c[0] == 'RemoveStatus'])
                self.total_ack(f)
            self.assertEqual(f.hp_writes(), [('SetHitpointsPercentage', ('enemy', 37.0, 'Guaranteed'))])
            self.assertEqual(f.rows('DB_AESN_HpTransaction')[0][7:9],
                             (212, 111) if new_percent == 210 else (101, 0))

    def test_source_policy_outputs_and_floor_are_identical_for_both_owners_and_versions(self):
        # Literal schema-2 policy outcomes, independently hand-calculated.
        for size, level, percent, target, delta, budgets in (
                (1, 1, 125, 126, 25, (0, 0, 0)),
                (2, 1, 145, 146, 45, (0, 0, 0)),
                (3, 1, 165, 166, 65, (0, 0, 1)),
                (4, 5, 210, 212, 111, (1, 0, 2)),
                (6, 13, 320, 323, 222, (3, 2, 4)),
                (12, 19, 520, 525, 424, (6, 6, 6))):
            for total in (False, True):
                for owner in ('owner', 'world'):
                    with self.subTest(size=size, total=total, owner=owner):
                        f = self.make(total, owner=owner)
                        f.facts['DB_AESN_CombatSnapshotV2'].clear()
                        if owner == 'world':
                            f.add('DB_AESN_WorldContext', owner, fire=False)
                        f.proc('PROC_AESN_SelectHardenedPolicy', owner, size, size, size * level, level)
                        snapshot = f.rows('DB_AESN_CombatSnapshotV2')[0]
                        self.assertEqual((snapshot[7], snapshot[8:11]), (percent, budgets))
                        self.plan(f, owner)
                        self.assertEqual(f.rows('DB_AESN_HpTransaction')[0][7:9], (target, delta))

    def test_real_legacy_bit_acknowledgements_commit_components_in_both_owner_modes(self):
        for world in (False, True):
            f = self.make(False)
            if world:
                f.add('DB_AESN_WorldContext', 'owner', fire=False)
            self.plan(f)
            active = []
            for bit, maximum in ((64, 165), (32, 197), (8, 205), (4, 209), (2, 211), (1, 212)):
                status = f'AESN_HP_BIT_{bit:05}'
                active.append(status)
                f.observe(maximum, 50, 49.5, active=active)
                f.native['HasActiveStatus'] += [('enemy', f'AESN_HP_BIT_{b:05}', 0)
                                               for b in (1, 2, 4, 8, 16, 32, 64, 128)
                                               if f'AESN_HP_BIT_{b:05}' not in active]
                f.event('StatusApplied', 'enemy', status, 'cause', 1)
            self.assertEqual(f.rows('DB_AESN_HpTransaction')[0][3], 'HPCommitted')
            f.event('StatusApplied', 'enemy', 'AESN_HARDENED_FOE_01', 'cause', 1)
            self.assertEqual(f.rows('DB_AESN_ComponentApplication')[0][2:], (1, 'FullyCommitted'))
            self.assertEqual(bool(f.rows('DB_AESN_WorldHardenedReady')), world)

    def test_mixed_representation_merge_has_one_owner_and_no_reapplication(self):
        f = self.make()
        self.stable(f)
        f.add('DB_AESN_HpTransaction', 'owner', 'legacy', 1, 'HPCommitted',
              10, 20, 50.0, 21, 1, 1, fire=False)
        f.add('DB_AESN_EnemyHpBit', 'owner', 'legacy', 1, 'AESN_HP_BIT_00001', fire=False)
        f.add('DB_AESN_ComponentApplication', 'owner', 'legacy', 1, 'FullyCommitted', fire=False)
        f.add('DB_AESN_MergeInProgress', 'owner', 'new', fire=False)
        f.calls.clear()
        f.proc('PROC_AESN_MergeCombat', 'owner', 'new')
        self.assertEqual({r[0] for r in f.rows('DB_AESN_HpTransaction')}, {'new'})
        self.assertEqual(len(f.rows('DB_AESN_HpTransaction')), 2)
        self.assertEqual(f.rows('DB_AESN_EnemyHpTotal')[0][0], 'new')
        self.assertEqual(f.rows('DB_AESN_EnemyHpBit')[0][0], 'new')
        self.assertFalse(f.rows('DB_AESN_MergeInProgress'))
        self.assertFalse([c for c in f.calls if c[0] == 'ApplyStatus'])
        self.assertFalse(f.hp_writes())

    def test_world_join_and_out_of_range_retention_do_not_reapply(self):
        f = self.make(owner='world')
        f.add('DB_AESN_WorldContext', 'world', fire=False)
        f.add('DB_AESN_WorldTracked', 'enemy', fire=False)
        self.stable(f, 'world')
        f.add('DB_AESN_EnemyEligible', 'combat', 'enemy')
        self.assertEqual(f.rows('DB_AESN_CombatHardenedReady'), [('combat', 'enemy')])
        f.add('DB_AESN_WorldScanMiss', 'enemy')
        self.assertTrue(f.rows('DB_AESN_WorldTracked'))
        self.assertEqual(len(f.rows('DB_AESN_HpTransaction')), 1)
        self.assertFalse([c for c in f.calls if c[0] in ('ApplyStatus', 'RemoveStatus')])

    def test_external_hp_change_replans_from_observed_external_base(self):
        f = self.make(owner='world')
        f.add('DB_AESN_WorldContext', 'world', fire=False)
        f.add('DB_AESN_WorldTracked', 'enemy', fire=False)
        self.stable(f, 'world')
        f.observe(232, 80, 34.0, active=('AESN_HP_TOTAL_111', 'AESN_HARDENED_FOE_01', 'FOREIGN'))
        f.add('DB_AESN_WorldScanSeen', 'enemy')
        self.assertEqual(f.rows('DB_AESN_HpReplan')[0][3:], ('RemovingComponents', 34.0))
        f.event('StatusRemoved', 'enemy', 'AESN_HARDENED_FOE_01', 'cause', 1)
        self.assertFalse(f.hp_writes())
        f.observe(121, 40, 20.0, active=('FOREIGN',))
        f.native['HasActiveStatus'].append(('enemy', 'AESN_HP_TOTAL_133', 0))
        f.event('StatusRemoved', 'enemy', 'AESN_HP_TOTAL_111', 'cause', 1)
        self.assertEqual(f.rows('DB_AESN_HpTransaction')[0][5:9], (121, 34.0, 254, 133))
        self.assertFalse(f.hp_writes())
        self.total_ack(f, 133, 254)
        self.assertEqual(f.hp_writes(), [('SetHitpointsPercentage', ('enemy', 34.0, 'Guaranteed'))])

    def test_world_orphan_uncertainty_cannot_retire_tracking_or_failure(self):
        f = self.make(owner='world')
        f.add('DB_AESN_WorldContext', 'world', fire=False)
        f.add('DB_AESN_WorldTracked', 'enemy', fire=False)
        f.add('DB_AESN_HpTotalUncertain', 'world', 'enemy', 'Apply', 'AESN_HP_TOTAL_111', 3, 'Timeout', fire=False)
        f.add('DB_AESN_WorldCleanupRequested', 'enemy')
        self.assertTrue(f.rows('DB_AESN_WorldTracked'))
        self.assertTrue(f.rows('DB_AESN_WorldCleanupRequested'))

    def test_paused_legacy_transfer_does_not_apply_during_hold_move(self):
        f = self.make(False)
        f.add('DB_AESN_HpApplicationHold', 'owner', 'enemy', fire=False)
        f.transaction(version=1, delta=1)
        f.add('DB_AESN_HpDesiredBit', 'owner', 'enemy', 1, 'AESN_HP_BIT_00001', fire=False)
        f.add('DB_AESN_HpPlanQueued', 'owner', 'enemy', fire=False)
        f.add('DB_AESN_MergeInProgress', 'owner', 'new', fire=False)
        f.proc('PROC_AESN_TransferHpTotalFacts', 'owner', 'new', 'enemy')
        self.assertFalse([c for c in f.calls if c[0] == 'ApplyStatus'])
        self.assertEqual(f.rows('DB_AESN_HpTransaction')[0][0:4], ('new', 'enemy', 1, 'Planned'))
        self.assertEqual(f.rows('DB_AESN_HpApplicationHold'), [('new', 'enemy')])

    def test_held_committed_transfer_never_starts_components_on_source_owner(self):
        for representation in (1, 2):
            with self.subTest(representation=representation):
                f = self.make(total=representation == 2)
                f.add('DB_AESN_HpApplicationHold', 'owner', 'enemy', fire=False)
                f.transaction(version=representation, state='HPCommitted', delta=1, applied=1)
                owned = 'DB_AESN_EnemyHpBit' if representation == 1 else 'DB_AESN_EnemyHpTotal'
                status = 'AESN_HP_BIT_00001' if representation == 1 else 'AESN_HP_TOTAL_1'
                f.add(owned, 'owner', 'enemy', 1, status, fire=False)
                f.observe(21, 10, 50.0, active=(status,))
                f.add('DB_AESN_MergeInProgress', 'owner', 'new', fire=False)
                f.proc('PROC_AESN_TransferHpTotalFacts', 'owner', 'new', 'enemy')
                self.assertFalse(f.calls)
                for name in ('DB_AESN_ComponentStarted', 'DB_AESN_ComponentApplication',
                             'DB_AESN_ComponentPendingApply', 'DB_AESN_EnemyComponent'):
                    self.assertFalse(f.rows(name), name)
                self.assertEqual(f.rows('DB_AESN_HpTransaction'),
                                 [('new', 'enemy', representation, 'HPCommitted',
                                   10, 20, 50.0, 21, 1, 1)])
                self.assertEqual(f.rows(owned), [('new', 'enemy', 1, status)])
                self.assertEqual(f.rows('DB_AESN_HpApplicationHold'), [('new', 'enemy')])
                self.assertEqual(f.rows('DB_AESN_MergeInProgress'), [('owner', 'new')])

    def test_replan_does_not_mutate_a_save_reconciliation_hold(self):
        f = self.make()
        self.stable(f)
        f.add('DB_AESN_HpApplicationHold', 'owner', 'enemy', fire=False)
        f.add('DB_AESN_MergeReplanRequired', 'owner', 'enemy')
        f.proc('PROC_AESN_ReplanEnemy', 'owner', 'enemy')
        self.assertFalse(f.rows('DB_AESN_HpReplan'))
        self.assertFalse([c for c in f.calls if c[0] in ('ApplyStatus', 'RemoveStatus')])

    def test_legacy_queued_transfer_is_not_an_application_dispatch(self):
        f = self.make(False)
        f.transaction(version=1, delta=1)
        f.add('DB_AESN_HpDesiredBit', 'owner', 'enemy', 1, 'AESN_HP_BIT_00001', fire=False)
        f.add('DB_AESN_HpPlanQueued', 'owner', 'enemy', fire=False)
        f.add('DB_AESN_MergeInProgress', 'owner', 'new', fire=False)
        f.proc('PROC_AESN_TransferHpTotalFacts', 'owner', 'new', 'enemy')
        self.assertFalse([c for c in f.calls if c[0] == 'ApplyStatus'])

    def test_world_policy_change_queues_total_replan_without_touching_relentless(self):
        f = self.make(owner='world')
        f.add('DB_AESN_WorldContext', 'world', fire=False)
        f.add('DB_AESN_WorldTracked', 'enemy', fire=False)
        self.stable(f, 'world')
        f.add('DB_AESN_WorldPreviousPolicy', 'world', 1, 210, fire=False)
        f.add('DB_AESN_RelentlessLedger', 'combat', 2, 1, 0, 1, 1, 0, 1, fire=False)
        ledger = list(f.rows('DB_AESN_RelentlessLedger'))
        f.proc('PROC_AESN_QueueWorldPolicyReplans', 'world', 2, 230)
        self.assertEqual(f.rows('DB_AESN_HpReplan')[0][3], 'RemovingComponents')
        self.assertFalse(f.rows('DB_AESN_WorldHardenedReady'))
        self.assertEqual(f.rows('DB_AESN_RelentlessLedger'), ledger)

    def test_uncertain_transfer_preserves_quarantine_and_late_ack_never_commits(self):
        f = self.make(tier=0)
        self.plan(f)
        timer = f.rows('DB_AESN_HpTotalTimer')[0]
        f.event('ObjectTimerFinished', 'enemy', timer[1])
        f.add('DB_AESN_MergeInProgress', 'owner', 'new', fire=False)
        f.proc('PROC_AESN_TransferHpTotalFacts', 'owner', 'new', 'enemy')
        self.assertEqual(f.rows('DB_AESN_HpTotalUncertain')[0][0], 'new')
        self.assertEqual(f.rows('DB_AESN_HpTotalTimer'), [timer])
        f.calls.clear()
        self.total_ack(f)
        self.assertEqual(f.rows('DB_AESN_HpTransaction')[0][3], 'ApplyingHP')
        self.assertFalse(f.hp_writes())

    def test_reload_never_retains_malformed_or_pending_total_identity(self):
        for issue in ('wrong_id', 'wrong_delta', 'missing_status', 'pending'):
            f = self.make()
            self.stable(f)
            if issue == 'wrong_id':
                f.facts['DB_AESN_EnemyHpTotal'] = [('owner', 'enemy', 111, 'AESN_HP_TOTAL_7')]
            elif issue == 'wrong_delta':
                f.facts['DB_AESN_EnemyHpTotal'] = [('owner', 'enemy', 7, 'AESN_HP_TOTAL_7')]
            elif issue == 'missing_status':
                f.observe(212, 50, 40.0, active=('AESN_HARDENED_FOE_01',))
            else:
                f.add('DB_AESN_HpTotalPending', 'owner', 'enemy', 'Apply', 'AESN_HP_TOTAL_111', 5, fire=False)
            f.event('SavegameLoaded')
            f.tick()
            f.event('ObjectTimerFinished', 'enemy', 'AESN_RECONCILE_ENEMY')
            self.assertFalse([r for r in f.rows('DB_AESN_ReconcileResult') if r[2] == 'RETAIN'])
            self.assertTrue(f.rows('DB_AESN_HpApplicationHold'))
            self.assertFalse(f.hp_writes())
            self.assertFalse([c for c in f.calls if c[0] == 'ApplyStatus'])

    def test_total_transfer_remaps_all_adjuncts_but_preserves_enemy_scoped_identity(self):
        f = self.make(tier=0)
        f.transaction(state='RemovingHPTotal', applied=111)
        owner_rows = {
            'DB_AESN_HpTotalDesired': ('owner', 'enemy', 111, 'AESN_HP_TOTAL_111'),
            'DB_AESN_EnemyHpTotal': ('owner', 'enemy', 111, 'AESN_HP_TOTAL_111'),
            'DB_AESN_HpTotalPending': ('owner', 'enemy', 'Remove', 'AESN_HP_TOTAL_111', 9),
            'DB_AESN_HpTotalUncertain': ('owner', 'enemy', 'Remove', 'AESN_HP_TOTAL_111', 9, 'Timeout'),
            'DB_AESN_HpTotalRemoval': ('owner', 'enemy', 'Cleanup', 111, 'AESN_HP_TOTAL_111', 101, 49.5),
        }
        enemy_rows = {
            'DB_AESN_HpTotalEpoch': ('enemy', 9),
            'DB_AESN_HpTotalTimer': ('enemy', 'AESN_HP_TOTAL_9', 9),
            'DB_AESN_HpTotalRetired': ('enemy', 'AESN_HP_TOTAL_7'),
        }
        for name, row in {**owner_rows, **enemy_rows}.items():
            f.add(name, *row, fire=False)
        f.add('DB_AESN_MergeInProgress', 'owner', 'new', fire=False)
        f.proc('PROC_AESN_TransferHpTotalFacts', 'owner', 'new', 'enemy')
        for name, row in owner_rows.items():
            self.assertEqual(f.rows(name), [('new',) + row[1:]])
        for name, row in enemy_rows.items():
            self.assertEqual(f.rows(name), [row])
        self.assertFalse(f.calls)

    def test_zero_cleanup_retires_metadata_after_external_hp_source_change(self):
        f = self.make(percent=100, tier=0)
        self.plan(f)
        f.observe(121, 60, 50.0, active=('FOREIGN',))
        f.proc('PROC_AESN_CleanupEnemy', 'enemy', 'owner')
        self.assertFalse(f.rows('DB_AESN_HpTransaction'))
        self.assertFalse(f.hp_writes())

    def test_direct_replan_respects_destination_merge_barrier(self):
        f = self.make()
        self.stable(f)
        f.add('DB_AESN_MergeInProgress', 'old', 'owner', fire=False)
        f.proc('PROC_AESN_ReplanEnemy', 'owner', 'enemy')
        self.assertFalse(f.rows('DB_AESN_HpReplan'))
        self.assertFalse([c for c in f.calls if c[0] == 'RemoveStatus'])
