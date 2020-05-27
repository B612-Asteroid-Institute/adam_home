from adam import AdamProcessingService, ConfigManager, AuthenticatingRestProxy, RestRequests, PropagationParams, \
    OpmParams


class TestAdamProcessingService:

    def setup_method(self, method):
        self.setup_actual_aps()
        print("method setup")

    def setup_actual_aps(self):
        config = ConfigManager().get_config('localdev')
        rest = AuthenticatingRestProxy(RestRequests(config['url']), config['token'])
        self.workspace = config['workspace']
        self.aps=AdamProcessingService(rest)


    def test_submit_batch(self):
        keplerian_elements = {
            'semi_major_axis_km': 448793612,
            'eccentricity': 0.1,
            'inclination_deg': 90,
            'ra_of_asc_node_deg': 91,
            'arg_of_pericenter_deg': 92,
            'true_anomaly_deg': 93,
            'gm': 132712440041.9394
        }

        keplerian_sigma = {
            'semi_major_axis': 100,
            'eccentricity': 0.001,
            'inclination': 1,
            'ra_of_asc_node': 2,
            'arg_of_pericenter': 3,
            'true_anomaly': 4,
        }

        state_vec = [130347560.13690618,
                     -74407287.6018632,
                     -35247598.541470632,
                     23.935241263310683,
                     27.146279819258538,
                     10.346605942591514]
        sigma_vec = {'x': 1000,
                     'y': 1001,
                     'z': 1002,
                     'x_dot': 10,
                     'y_dot': 11,
                     'z_dot': 12}
        draws = 5
        propagation_params = PropagationParams({
            'start_time': '2017-10-04T00:00:00Z',  # propagation start time in ISO format
            'end_time': '2017-10-11T00:00:00Z',  # propagation end time in ISO format

            'project_uuid': self.workspace,
            'keplerianSigma': keplerian_sigma,
            'monteCarloDraws': draws,
            'propagationType': 'MONTE_CARLO'
        })

        opm_params = OpmParams({
            'epoch': '2017-10-04T00:00:00Z',
            'keplerian_elements': keplerian_elements,
        })
        response = self.aps.execute_batch_propagation(self.workspace, propagation_params, opm_params)
        print(response)