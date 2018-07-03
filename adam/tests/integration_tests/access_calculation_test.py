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


class AccessCalculationTest(unittest.TestCase):

    def setUp(self):
        config = ConfigManager(os.getcwd() + '/test_config.json').get_config('dev')
        self.service = Service(config)
        self.assertTrue(self.service.setup())
        self.working_project = self.service.new_working_project()
        self.assertIsNotNone(self.working_project)

    def tearDown(self):
        self.service.teardown()
    
    def new_propagation_1703_keplerian(self):
        # start = '2027-02-25T02:02:41.216Z'
        # end = '2016-02-25T02:02:41.216Z'
        start = '2016-02-25T02:02:41.216Z'
        end = '2027-02-25T02:02:41.216Z'
        propagation_params = PropagationParams({
            'start_time': start,
            'end_time': end,
            'step_size': 86400,
            'description': 'Created by test at ' + start
        })

        state_vector = [309583299.63553455,
                        149330310.63501837,
                        91399553.72240286,
                        -13.348371665766601,
                        8.096083086159309,
                        5.588584368211324]
        # state_vector = [-131900970.6, 62817207.04, 43907139.71,
        #                 -13.58678389, -27.66719022, -17.85324656]

        # keplerian_elements = {
        #     'semi_major_axis_km': 1.883096951 * 149597870.7,
        #     'eccentricity': 0.4737577730000001,
        #     'inclination_deg': 33.25638884571273,
        #     'ra_of_asc_node_deg': 1.810551601578951,
        #     'arg_of_pericenter_deg': 172.5271584249529,
        #     'true_anomaly_deg': 335.814768,
        #     'gm': 1.327124400419394E11
        # }
        opm_params = OpmParams({
            'epoch': start,
            'state_vector': state_vector,
        })

        return BatchPropagation(propagation_params, opm_params)
    
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
        propagation_1703 = self.new_propagation_1703_keplerian()
        batch_propagations = BatchPropagations(self.service.rest)

        RunnableManager(batch_propagations, [propagation_1703],
                        self.working_project.get_uuid()).run(get_child_results=True)

        single_prop_uuid = propagation_1703.get_children()[0].get_uuid()
        print('Using single prop ' + single_prop_uuid + ' for access calculations.')
        print('OPM:\n' + propagation_1703.get_opm_params().generate_opm())
        print('Results:\n' + propagation_1703.get_children()[0].get_ephemeris()[:1000]
            + '\n...\n' + propagation_1703.get_children()[0].get_ephemeris()[-500:])

        access_start_time = '2022-02-03T00:00:00Z'
        access_end_time = '2022-02-12T00:00:00Z'
        access_calculation = self.new_access_calculation_1703_with_ephem(
            single_prop_uuid, access_start_time, access_end_time, 'Lsst10yrPointings')
        access_calculations = AccessCalculations(self.service.rest)

        RunnableManager(access_calculations, [access_calculation],
                        self.working_project.get_uuid()).run(get_child_results=False)

        print('Computed accesses: ')
        for a in access_calculation.get_accesses():
            print(a)

        access_calculations.delete(access_calculation.get_uuid())
        batch_propagations.delete(propagation_1703.get_uuid())
    
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
    
    def no_test_access_calculation_1703_160yr(self):
        access_start_time = '2017-06-10T00:00:00Z'
        access_end_time = '2017-06-11T00:00:00Z'
        access_calculation = self.new_access_calculation_1703_propagated(
            access_start_time, access_end_time, 'LsstPointings')

        access_calculations = AccessCalculations(self.service.rest)

        RunnableManager(access_calculations, [access_calculation],
                        self.working_project.get_uuid()).run(get_child_results=False)

        print('Computed accesses: ')
        for a in access_calculation.get_accesses():
            print(a)
            
        access_calculations.delete(access_calculation.get_uuid())

    def no_test_access_calculation_1703_4mo(self):
        access_start_time = '2022-01-03T00:00:00Z'
        access_end_time = '2022-05-03T00:00:00Z'
        access_calculation = self.new_access_calculation_1703_propagated(
            access_start_time, access_end_time, 'Lsst4moPointings')

        access_calculations = AccessCalculations(self.service.rest)

        RunnableManager(access_calculations, [access_calculation],
                        self.working_project.get_uuid()).run(get_child_results=False)

        print('Computed accesses: ')
        for a in access_calculation.get_accesses():
            print(a)

        children = access_calculation.get_children()
        if children is None or len(children) == 0:
            print("children: " + str(children))

        access_calculations.delete(access_calculation.get_uuid())
        access_calculations.delete('e6e65f0a-8715-41b6-8cc2-dd7af349097b')

        self.assertIsNone(access_calculations.get(access_calculation.get_uuid()))


if __name__ == '__main__':
    unittest.main()
