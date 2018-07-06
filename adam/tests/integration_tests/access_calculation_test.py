from adam import Service
from adam import PropagationParams
from adam import OpmParams
from adam import BatchPropagation
from adam import BatchPropagations
from adam import ConfigManager
from adam import RunnableManager
from adam import AccessCalculation
from adam import AccessCalculations
from adam import TargetingParams

import unittest
import os
import datetime


class AccessCalculationTest(unittest.TestCase):

    def setUp(self):
        config = ConfigManager(os.getcwd() + '/test_config.json').get_config('dev')
        self.service = Service(config)
        self.assertTrue(self.service.setup())
        self.working_project = self.service.new_working_project()
        self.assertIsNotNone(self.working_project)

    def tearDown(self):
        self.service.teardown()
    
    def new_propagation_1703_cartesian(self):
        start = '2016-12-13T12:50:42.216000Z'
        end =   '2028-12-13T12:50:42.216000Z'
        propagation_params = PropagationParams({
            'start_time': start,
            'end_time': end,
            'project_uuid': self.working_project.get_uuid(),
            'description': 'Created by test at ' + start
        })

        state_vec = [-1.3943495012181433e+8,
                     -5.9480309866722717e+7,
                     -3.6067000411359879e+7,
                     9.7858235790064864,
                     -2.8095312358013358e+01,
                     -1.8625826758658073e+01]
        opm_params = OpmParams({
            'epoch': start,
            'state_vector': state_vec,
        })

        return BatchPropagation(propagation_params, opm_params)
    
    def new_access_calculation_1703_with_ephem(self, single_prop_uuid, access_start, access_end, table):
        return AccessCalculation(None, None, single_prop_uuid, 
                                 access_start, access_end, table)

    def new_access_calculation_1703_propagated(self, access_start, access_end, table):
        start = '2016-12-13T12:50:42.216000Z'
        end = '2028-12-13T12:50:42.216000Z'
        propagation_params = PropagationParams({
            'start_time': start,
            'end_time': end,
            'project_uuid': self.working_project.get_uuid(),
            'description': 'Created by test at ' + start
        })

        state_vec = [-1.3943495012181433e+8,
                     -5.9480309866722717e+7,
                     -3.6067000411359879e+7,
                     9.7858235790064864,
                     -2.8095312358013358e+01,
                     -1.8625826758658073e+01]
        opm_params = OpmParams({
            'epoch': start,
            'state_vector': state_vec,
        })

        return AccessCalculation(propagation_params, opm_params, None,
                                 access_start, access_end, table)
    
    def test_access_calculation_1703_10yr_propagate_separately(self):
        # NOTE accesss calculations do not work with back propagated ephems
        propagation_1703 = self.new_propagation_1703_cartesian()
        batch_propagations = BatchPropagations(self.service.rest)

        RunnableManager(batch_propagations, [propagation_1703],
                        self.working_project.get_uuid()).run(get_child_results=True)

        single_prop_uuid = propagation_1703.get_children()[0].get_uuid()
        print('Using single prop ' + single_prop_uuid + ' for access calculations.')
        print('OPM:\n' + propagation_1703.get_opm_params().generate_opm())
        print('Results:\n' + propagation_1703.get_children()[0].get_ephemeris()[:600]
            + '\n...\n' + propagation_1703.get_children()[0].get_ephemeris()[-200:])

        access_start_time = '2022-02-03T00:00:00Z'
        access_end_time = '2022-02-12T00:00:00Z'
        access_calculation = self.new_access_calculation_1703_with_ephem(
            single_prop_uuid, access_start_time, access_end_time, 'Lsst10yrPointings')
        access_calculations = AccessCalculations(self.service.rest)

        RunnableManager(access_calculations, [access_calculation],
                        self.working_project.get_uuid()).run(get_child_results=False)

        # Spot-check computed accesses.
        self.assertEqual(14, len(access_calculation.get_accesses()))
        self.assertEqual([2459618.8358333334,
                          2459618.8361805556,
                          datetime.datetime(2022, 2, 8, 8, 3, 36, 8),
                          datetime.datetime(2022, 2, 8, 8, 4, 6, 6)],
                         access_calculation.get_accesses()[1])

        access_calculations.delete(access_calculation.get_uuid())
        batch_propagations.delete(propagation_1703.get_uuid())
    
    def test_access_calculation_1703_10yr(self):
        access_start_time = '2022-02-03T00:00:00Z'
        access_end_time = '2022-02-12T00:00:00Z'
        access_calculation = self.new_access_calculation_1703_propagated(
            access_start_time, access_end_time, 'Lsst10yrPointings')
        access_calculations = AccessCalculations(self.service.rest)

        RunnableManager(access_calculations, [access_calculation],
                        self.working_project.get_uuid()).run()

        print('Child propagation: ')
        self.assertEqual(1, len(access_calculation.get_children()))
        child_prop = access_calculation.get_children()[0]
        print(child_prop.get_ephemeris()[:600] + '\n...\n' + child_prop.get_ephemeris()[-200:])

        # Spot-check computed accesses.
        self.assertEqual(14, len(access_calculation.get_accesses()))
        self.assertEqual([2459618.8358333334,
                          2459618.8361805556,
                          datetime.datetime(2022, 2, 8, 8, 3, 36, 8),
                          datetime.datetime(2022, 2, 8, 8, 4, 6, 6)],
                         access_calculation.get_accesses()[1])

        access_calculations.delete(access_calculation.get_uuid())
    
    # Rename, removing leading no_ to run. CAREFUL because this will kick off
    # a very large computation.
    def no_test_access_calculation_1703_10yr_load(self):
        access_start_time = '2017-01-01T00:00:00Z'
        access_end_time = '2027-01-01T00:00:00Z'
        access_calculation_list = [self.new_access_calculation_1703_propagated(
            access_start_time, access_end_time, 'Lsst10yrPointings') for i in range(50)]

        access_calculations = AccessCalculations(self.service.rest)

        RunnableManager(access_calculations, access_calculation_list,
                        self.working_project.get_uuid()).run(get_child_results=False)

        print('Computed accesses: ')
        for a in access_calculation_list[0].get_accesses():
            print(a)
            
        for access_calculation in access_calculation_list:
            access_calculations.delete(access_calculation.get_uuid())


if __name__ == '__main__':
    unittest.main()
