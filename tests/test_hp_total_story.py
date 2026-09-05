import unittest
from tests.hp_story_fixture import HpStoryFixture


class HpTotalStoryTests(unittest.TestCase):
    def make(self, **kwargs):
        f = HpStoryFixture()
        f.observe()
        f.transaction(**kwargs)
        f.run('PROC_AESN_QueueHpTotal', 'owner', 'enemy', kwargs.get('delta', 111))
        return f

    def begin(self, f):
        f.run('PROC_AESN_BeginHpTotalApply', 'owner', 'enemy')

    def ack(self, f, maximum=131, current=65):
        f.observe(maximum, current, active=('AESN_HP_TOTAL_111', 'AESN_HP_TOTAL_7'))
        f.event('StatusApplied', 'enemy', 'AESN_HP_TOTAL_111', 'cause', 1)

    def committed(self, f):
        return any(r[3] == 'HPCommitted' for r in f.rows('DB_AESN_HpTransaction'))

    def test_exact_positive_boundary_ids_and_no_zero_or_binary_fallback(self):
        for delta, want in [(0, None), (1, 'AESN_HP_TOTAL_1'), (111, 'AESN_HP_TOTAL_111'),
                            (32768, 'AESN_HP_TOTAL_32768'), (65535, 'AESN_HP_TOTAL_65535'),
                            (-1, None), (65536, None)]:
            with self.subTest(delta=delta):
                f = self.make(delta=delta)
                self.assertEqual(f.rows('DB_AESN_HpTotalDesired'),
                                 [] if want is None else [('owner', 'enemy', delta, want)])
                self.assertFalse(f.rows('DB_AESN_HpDesiredBit'))

    def test_supported_representations_are_exactly_one_and_two(self):
        f = self.make()
        f.native['QRY_AESN_HpRepresentationSupported'] = []
        for version in [0, 1, 2, 3, 99]:
            self.assertEqual(bool(list(f.solutions([f'QRY_AESN_HpRepresentationSupported({version})'], {}))),
                             version in (1, 2))

    def test_intent_precedes_apply_and_native_observations_do_not_change(self):
        f = self.make()
        self.begin(f)
        self.assertIn(('ApplyStatus', ('enemy', 'AESN_HP_TOTAL_111', -1.0, 1,
                                      'NULL_00000000-0000-0000-0000-000000000000')), f.calls)
        self.assertEqual(f.intent_at_call[0][1], [('owner', 'enemy', 'Apply', 'AESN_HP_TOTAL_111', 1)])
        self.assertEqual(f.native['GetMaxHitpoints'], [('enemy', 20)])
        self.assertFalse(self.committed(f))
        self.assertFalse(f.hp_writes())

    def test_matching_ack_and_exact_maximum_commit_once(self):
        f = self.make()
        self.begin(f)
        self.ack(f)
        self.assertTrue(self.committed(f))
        self.assertEqual(f.rows('DB_AESN_EnemyHpTotal'), [('owner', 'enemy', 111, 'AESN_HP_TOTAL_111')])
        self.assertEqual(f.hp_writes(), [('SetHitpointsPercentage', ('enemy', 50.0, 'Guaranteed'))])
        self.ack(f)
        self.assertEqual(len(f.hp_writes()), 1)

    def test_ownership_appearing_after_dispatch_blocks_ack_and_preserves_intent(self):
        for delta, status in [(7, 'AESN_HP_TOTAL_7'), (111, 'AESN_HP_TOTAL_111')]:
            with self.subTest(recorded_status=status):
                f = self.make()
                self.begin(f)
                owned = ('owner', 'enemy', delta, status)
                f.add('DB_AESN_EnemyHpTotal', *owned, fire=False)
                self.ack(f)
                self.assertFalse(f.hp_writes())
                self.assertFalse(self.committed(f))
                self.assertEqual(f.rows('DB_AESN_EnemyHpTotal'), [owned])
                self.assertEqual(f.rows('DB_AESN_HpTotalPending'),
                                 [('owner', 'enemy', 'Apply', 'AESN_HP_TOTAL_111', 1)])
                self.assertEqual(f.rows('DB_AESN_HpTotalUncertain'),
                                 [('owner', 'enemy', 'Apply', 'AESN_HP_TOTAL_111', 1,
                                   'OwnershipAppearedDuringApply')])
                self.ack(f)
                self.assertFalse(f.hp_writes())
                self.assertEqual(len(f.rows('DB_AESN_HpTotalUncertain')), 1)

    def test_ack_alone_wrong_maximum_or_death_never_commits(self):
        for maximum, current in [(130, 65), (131, 0)]:
            with self.subTest(maximum=maximum, current=current):
                f = self.make()
                self.begin(f)
                self.ack(f, maximum, current)
                self.assertFalse(self.committed(f))
                self.assertFalse(f.hp_writes())
                self.assertTrue(f.rows('DB_AESN_HpTotalUncertain'))

    def test_ack_without_live_presence_is_not_success(self):
        f = self.make()
        self.begin(f)
        f.event('StatusApplied', 'enemy', 'AESN_HP_TOTAL_111', 'cause', 1)
        self.assertFalse(self.committed(f))
        self.assertTrue(f.rows('DB_AESN_HpTotalPending'))

    def test_zero_commits_without_status_or_hp_write(self):
        f = self.make(delta=0)
        self.begin(f)
        self.assertTrue(self.committed(f))
        self.assertFalse(f.calls)

    def test_preexisting_unowned_same_total_is_conflict_not_ownership(self):
        f = self.make()
        f.observe(131, 65, active=('AESN_HP_TOTAL_111',))
        self.begin(f)
        self.assertFalse(f.calls)
        self.assertFalse(f.rows('DB_AESN_EnemyHpTotal'))
        self.assertIn(('owner', 'enemy', 'UnownedTotalConflict'), f.rows('DB_AESN_HpFailure'))

    def test_unknown_version_foreign_owner_or_wrong_desired_fail_closed(self):
        for issue in ['version', 'owner', 'desired']:
            f = self.make(version=99 if issue == 'version' else 2)
            if issue == 'owner':
                f.transaction(owner='foreign')
            if issue == 'desired':
                f.facts['DB_AESN_HpTotalDesired'] = [('owner', 'enemy', 111, 'AESN_HP_TOTAL_7')]
            self.begin(f)
            self.assertFalse(f.calls)

    def test_foreign_event_does_not_acknowledge_pending(self):
        f = self.make()
        self.begin(f)
        f.event('StatusApplied', 'other', 'AESN_HP_TOTAL_111', 'cause', 1)
        f.event('StatusApplied', 'enemy', 'AESN_HP_TOTAL_7', 'cause', 1)
        self.assertTrue(f.rows('DB_AESN_HpTotalPending'))
        self.assertFalse(self.committed(f))

    def timeout(self, f):
        timers = [args for name, args in f.calls if name == 'RealtimeObjectTimerLaunch']
        self.assertTrue(timers)
        f.event('ObjectTimerFinished', 'enemy', timers[-1][1])
        return timers[-1][1]

    def test_timeout_then_late_ack_preserves_intent_without_healing_or_retry(self):
        f = self.make()
        self.begin(f)
        self.timeout(f)
        self.assertEqual(f.rows('DB_AESN_HpTotalUncertain')[0][:5],
                         ('owner', 'enemy', 'Apply', 'AESN_HP_TOTAL_111', 1))
        self.ack(f)
        f.run('PROC_AESN_ReconcileHpTotal', 'owner', 'enemy')
        self.begin(f)
        self.assertFalse(self.committed(f))
        self.assertFalse(f.hp_writes())
        self.assertEqual(len([c for c in f.calls if c[0] == 'ApplyStatus']), 1)

    def test_failed_attempt_retains_identity(self):
        f = self.make()
        self.begin(f)
        f.event('StatusAttemptFailed', 'enemy', 'AESN_HP_TOTAL_111', 'cause', 1)
        self.assertTrue(f.rows('DB_AESN_HpTotalUncertain'))
        self.assertFalse(f.hp_writes())

    def test_removal_only_recorded_total_captures_live_external_base_and_percentage(self):
        f = self.make()
        self.begin(f)
        self.ack(f)
        f.calls.clear()
        f.observe(141, 70, 49.0, active=('AESN_HP_TOTAL_111', 'AESN_HP_TOTAL_7'))
        f.run('PROC_AESN_BeginHpTotalRemove', 'owner', 'enemy', 'Cleanup')
        self.assertIn(('RemoveStatus', ('enemy', 'AESN_HP_TOTAL_111',
                                      'NULL_00000000-0000-0000-0000-000000000000')), f.calls)
        self.assertFalse(f.hp_writes())
        f.observe(30, 15, active=('AESN_HP_TOTAL_7',))
        f.event('StatusRemoved', 'enemy', 'AESN_HP_TOTAL_111', 'cause', 1)
        self.assertEqual(f.hp_writes(), [('SetHitpointsPercentage', ('enemy', 49.0, 'Guaranteed'))])
        self.assertFalse(f.rows('DB_AESN_EnemyHpTotal'))
        self.assertFalse(f.rows('DB_AESN_HpTransaction'))

    def test_removal_unknown_mode_and_unowned_id_fail_closed(self):
        f = self.make()
        f.observe(131, 65, active=('AESN_HP_TOTAL_111',))
        f.run('PROC_AESN_BeginHpTotalRemove', 'owner', 'enemy', 'Cleanup')
        self.assertFalse(f.calls)
        self.begin(f)
        f.run('PROC_AESN_BeginHpTotalRemove', 'owner', 'enemy', 'Migration')
        self.assertFalse(f.calls)

    def test_removal_wrong_maximum_or_absent_ack_never_forgets_ownership(self):
        for acknowledge in [False, True]:
            f = self.make()
            self.begin(f)
            self.ack(f)
            f.calls.clear()
            f.run('PROC_AESN_BeginHpTotalRemove', 'owner', 'enemy', 'Cleanup')
            f.observe(19, 10)
            if acknowledge:
                f.event('StatusRemoved', 'enemy', 'AESN_HP_TOTAL_111', 'cause', 1)
            else:
                self.timeout(f)
            self.assertTrue(f.rows('DB_AESN_EnemyHpTotal'))
            self.assertTrue(f.rows('DB_AESN_HpTotalUncertain'))
            self.assertFalse(f.hp_writes())

    def test_old_timer_cannot_timeout_new_removal_epoch(self):
        f = self.make()
        self.begin(f)
        timers = [args[1] for name, args in f.calls if name == 'RealtimeObjectTimerLaunch']
        self.assertTrue(timers)
        timer = timers[0]
        self.ack(f)
        f.run('PROC_AESN_BeginHpTotalRemove', 'owner', 'enemy', 'Cleanup')
        f.event('ObjectTimerFinished', 'enemy', timer)
        self.assertFalse(f.rows('DB_AESN_HpTotalUncertain'))
        self.assertEqual(f.rows('DB_AESN_HpTotalPending')[0][4], 2)

    def test_math_fixture_primitives_bind_outputs_and_reject_wrong_values(self):
        f = self.make()
        self.assertEqual(list(f.solutions(['ConcatenateInteger("prefix", 111, _Out)'], {})),
                         [{'_Out': 'prefix111'}])
        self.assertEqual(list(f.solutions(['IntegerSubtract(141, 111, _Out)'], {})), [{'_Out': 30}])
        self.assertFalse(list(f.solutions(['IntegerSubtract(141, 111, 29)'], {})))

    def test_rollback_restores_original_percentage_not_postfailure_observation(self):
        f = self.make()
        self.begin(f)
        self.ack(f, 130, 65)
        f.observe(130, 30, 23.0, active=('AESN_HP_TOTAL_111',))
        f.run('PROC_AESN_BeginHpTotalRemove', 'owner', 'enemy', 'Rollback')
        f.observe(19, 10)
        f.event('StatusRemoved', 'enemy', 'AESN_HP_TOTAL_111', 'cause', 1)
        self.assertEqual(f.hp_writes(), [('SetHitpointsPercentage', ('enemy', 50.0, 'Guaranteed'))])
        self.assertEqual(f.rows('DB_AESN_HpTransaction')[0][3], 'Failed')

    def test_replan_retains_capture_without_intermediate_percentage_write(self):
        f = self.make()
        self.begin(f)
        self.ack(f)
        f.calls.clear()
        f.observe(141, 70, 49.0, active=('AESN_HP_TOTAL_111',))
        f.run('PROC_AESN_BeginHpTotalRemove', 'owner', 'enemy', 'Replan')
        f.observe(30, 15)
        f.event('StatusRemoved', 'enemy', 'AESN_HP_TOTAL_111', 'cause', 1)
        self.assertFalse(f.hp_writes())
        self.assertEqual(f.rows('DB_AESN_HpTransaction')[0][3], 'HpTotalRemoved')
        self.assertEqual(f.rows('DB_AESN_HpTotalRemoval'),
                         [('owner', 'enemy', 'Replan', 111, 'AESN_HP_TOTAL_111', 30, 49.0)])

    def test_dead_removal_cleans_without_resurrection(self):
        f = self.make()
        self.begin(f)
        self.ack(f)
        f.calls.clear()
        f.observe(131, 0, 0.0, active=('AESN_HP_TOTAL_111',))
        f.run('PROC_AESN_BeginHpTotalRemove', 'owner', 'enemy', 'Cleanup')
        f.observe(20, 0, 0.0)
        f.event('StatusRemoved', 'enemy', 'AESN_HP_TOTAL_111', 'cause', 1)
        self.assertFalse(f.hp_writes())
        self.assertFalse(f.rows('DB_AESN_HpTransaction'))

    def test_late_apply_can_be_cleaned_but_never_reused_as_fresh_apply(self):
        f = self.make()
        self.begin(f)
        self.timeout(f)
        self.ack(f)
        f.calls.clear()
        f.run('PROC_AESN_BeginHpTotalRemove', 'owner', 'enemy', 'Cleanup')
        self.assertEqual([c[1][1] for c in f.calls if c[0] == 'RemoveStatus'], ['AESN_HP_TOTAL_111'])
        f.observe(20, 10)
        f.event('StatusRemoved', 'enemy', 'AESN_HP_TOTAL_111', 'cause', 1)
        f.facts['DB_AESN_HpFailure'].clear()
        f.transaction()
        f.run('PROC_AESN_QueueHpTotal', 'owner', 'enemy', 111)
        self.begin(f)
        self.assertFalse([c for c in f.calls if c[0] == 'ApplyStatus'])

    def test_same_owner_conflicting_transaction_version_or_state_blocks_apply(self):
        for version, state in [(99, 'Planned'), (2, 'Failed')]:
            f = self.make()
            f.transaction(version=version, state=state)
            self.begin(f)
            self.assertFalse(f.calls)

    def test_conflicting_same_state_transaction_payload_blocks_apply(self):
        for column, other in [(4, 11), (5, 21), (6, 75.0), (7, 132), (8, 112), (9, 1)]:
            with self.subTest(column=column):
                f = self.make()
                row = list(f.rows('DB_AESN_HpTransaction')[0])
                row[column] = other
                f.add('DB_AESN_HpTransaction', *row, fire=False)
                self.begin(f)
                self.assertFalse(f.calls)

    def test_explicit_dead_flag_blocks_percentage_even_with_positive_hp(self):
        f = self.make()
        self.begin(f)
        f.observe(131, 65, active=('AESN_HP_TOTAL_111',))
        f.native['IsDead'] = [('enemy', 1)]
        f.event('StatusApplied', 'enemy', 'AESN_HP_TOTAL_111', 'cause', 1)
        self.assertFalse(f.hp_writes())
        self.assertFalse(self.committed(f))

    def test_unknown_mode_on_committed_owned_total_is_noop(self):
        f = self.make()
        self.begin(f)
        self.ack(f)
        f.calls.clear()
        f.run('PROC_AESN_BeginHpTotalRemove', 'owner', 'enemy', 'Migration')
        self.assertFalse(f.calls)
        self.assertTrue(self.committed(f))

    def test_exact_boundary_apply_payloads(self):
        for delta, status, maximum in [(1, 'AESN_HP_TOTAL_1', 21),
                                        (32768, 'AESN_HP_TOTAL_32768', 32788),
                                        (65535, 'AESN_HP_TOTAL_65535', 65555)]:
            with self.subTest(delta=delta):
                f = self.make(delta=delta)
                f.native['HasActiveStatus'].append(('enemy', status, 0))
                self.begin(f)
                self.assertEqual([c[1][1] for c in f.calls if c[0] == 'ApplyStatus'], [status])
                f.observe(maximum, 10, active=(status,))
                f.event('StatusApplied', 'enemy', status, 'cause', 1)
                self.assertTrue(self.committed(f))

    def test_removal_ack_requires_live_absence_and_duplicates_write_once(self):
        f = self.make()
        self.begin(f)
        self.ack(f)
        f.calls.clear()
        f.run('PROC_AESN_BeginHpTotalRemove', 'owner', 'enemy', 'Cleanup')
        self.assertEqual(f.intent_at_call[-1][1],
                         [('owner', 'enemy', 'Remove', 'AESN_HP_TOTAL_111', 2)])
        f.event('StatusRemoved', 'enemy', 'AESN_HP_TOTAL_111', 'cause', 1)
        self.assertFalse(f.hp_writes())
        self.assertTrue(f.rows('DB_AESN_EnemyHpTotal'))
        f.observe(20, 10)
        f.event('StatusRemoved', 'enemy', 'AESN_HP_TOTAL_111', 'cause', 1)
        f.event('StatusRemoved', 'enemy', 'AESN_HP_TOTAL_111', 'cause', 1)
        self.assertEqual(len(f.hp_writes()), 1)

    def test_duplicate_owned_records_block_removal(self):
        f = self.make(state='HPCommitted', applied=111)
        f.add('DB_AESN_EnemyHpTotal', 'owner', 'enemy', 111, 'AESN_HP_TOTAL_111')
        f.add('DB_AESN_EnemyHpTotal', 'owner', 'enemy', 7, 'AESN_HP_TOTAL_7')
        f.observe(138, 65, active=('AESN_HP_TOTAL_111', 'AESN_HP_TOTAL_7'))
        f.run('PROC_AESN_BeginHpTotalRemove', 'owner', 'enemy', 'Cleanup')
        self.assertFalse(f.calls)

    def test_mixed_legacy_owned_or_pending_state_blocks_total_operations(self):
        legacy = [('DB_AESN_EnemyHpBit', ('owner', 'enemy', 1, 'AESN_HP_BIT_00001')),
                  ('DB_AESN_HpPendingApply', ('owner', 'enemy', 0, 1, 'AESN_HP_BIT_00001')),
                  ('DB_AESN_HpPendingRemove', ('owner', 'enemy', 0, 1, 'AESN_HP_BIT_00001', 'Cleanup'))]
        for name, row in legacy:
            for operation in ['Apply', 'Remove']:
                with self.subTest(fact=name, operation=operation):
                    f = self.make()
                    if operation == 'Remove':
                        self.begin(f)
                        self.ack(f)
                    f.calls.clear()
                    f.add(name, *row, fire=False)
                    if operation == 'Remove':
                        f.run('PROC_AESN_BeginHpTotalRemove', 'owner', 'enemy', 'Cleanup')
                    else:
                        self.begin(f)
                    self.assertFalse(f.calls)
                    self.assertEqual(f.rows(name), [row])


if __name__ == '__main__':
    unittest.main()
