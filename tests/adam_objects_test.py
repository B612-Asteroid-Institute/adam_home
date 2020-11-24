from adam.adam_objects import AdamObject
from adam.adam_objects import AdamObjects
from adam.adam_objects import AdamObjectRunnableState
from adam.rest_proxy import _RestProxyForTest
import unittest


class AdamObjectTest(unittest.TestCase):
    """Unit tests for AdamObject object

    """

    def test_get_and_set_methods(self):
        adam_object = AdamObject()
        self.assertIsNone(adam_object.get_uuid())
        self.assertIsNone(adam_object.get_runnable_state())
        self.assertIsNone(adam_object.get_children())

        adam_object.set_uuid('uuid')
        self.assertEqual('uuid', adam_object.get_uuid())

        adam_object.set_runnable_state({'whatever': 5})
        self.assertEqual({'whatever': 5}, adam_object.get_runnable_state())

        adam_object.set_children(['what', 'ever'])
        self.assertEqual(['what', 'ever'], adam_object.get_children())


class AdamObjectRunnableStateTest(unittest.TestCase):
    """Unit tests for AdamObjectRunnableState object

    """

    def test_get_methods(self):
        running_runnable_state = AdamObjectRunnableState({
            'uuid': 'uuid1',
            'calculationState': 'RUNNING'
        })
        self.assertEqual('uuid1', running_runnable_state.get_uuid())
        self.assertEqual('RUNNING', running_runnable_state.get_calc_state())
        self.assertIsNone(running_runnable_state.get_error())

        failed_runnable_state = AdamObjectRunnableState({
            'uuid': 'uuid2',
            'calculationState': 'FAILED',
            'error': 'some error'
        })
        self.assertEqual('uuid2', failed_runnable_state.get_uuid())
        self.assertEqual('FAILED', failed_runnable_state.get_calc_state())
        self.assertEqual('some error', failed_runnable_state.get_error())


class AdamObjectsTest(unittest.TestCase):
    """Unit tests for AdamObjects module

    """

    def test_insert(self):
        rest = _RestProxyForTest()
        adam_objects = AdamObjects(rest, 'MyType')

        expected_data = {}

        def check_input(data_dict):
            self.assertEqual(expected_data, data_dict)
            return True

        expected_data = {'anyKey': 'anyVal'}
        rest.expect_post("/adam_object/single/MyType",
                         check_input, 200, {'uuid': 'uuid1'})

        uuid = adam_objects._insert({'anyKey': 'anyVal'})
        self.assertEqual('uuid1', uuid)

        rest.expect_post("/adam_object/single/MyType", check_input, 404, {})
        with self.assertRaises(RuntimeError):
            adam_objects._insert({'anyKey': 'anyVal'})

    def test_get_runnable_state(self):
        rest = _RestProxyForTest()
        adam_objects = AdamObjects(rest, 'MyType')

        rest.expect_get("/adam_object/runnable_state/single/MyType/uuid1", 200, {
            'uuid': 'uuid1',
            'calculationState': 'PENDING',
        })
        runnable_state = adam_objects.get_runnable_state('uuid1')
        self.assertEqual('uuid1', runnable_state.get_uuid())
        self.assertEqual('PENDING', runnable_state.get_calc_state())
        self.assertIsNone(runnable_state.get_error())

        rest.expect_get(
            "/adam_object/runnable_state/single/MyType/uuid1", 404, {})
        runnable_state = adam_objects.get_runnable_state('uuid1')
        self.assertEqual(runnable_state, None)

        rest.expect_get(
            "/adam_object/runnable_state/single/MyType/uuid1", 403, {})
        with self.assertRaises(RuntimeError):
            adam_objects.get_runnable_state('uuid1')

    def test_get_runnable_states(self):
        rest = _RestProxyForTest()
        adam_objects = AdamObjects(rest, 'MyType')

        # Empty return value
        rest.expect_get("/adam_object/runnable_state/by_project/MyType/project_uuid", 200, {
            'items': []
        })
        runnable_states = adam_objects.get_runnable_states('project_uuid')
        self.assertEqual(0, len(runnable_states))

        rest.expect_get("/adam_object/runnable_state/by_project/MyType/project_uuid", 200, {
            'items': [{
                'uuid': 'uuid1',
                'calculationState': 'PENDING',
            }, {
                'uuid': 'uuid2',
                'calculationState': 'FAILED',
                'error': 'some error'
            }]
        })
        runnable_states = adam_objects.get_runnable_states('project_uuid')
        self.assertEqual(2, len(runnable_states))
        self.assertEqual('uuid1', runnable_states[0].get_uuid())
        self.assertEqual('PENDING', runnable_states[0].get_calc_state())
        self.assertIsNone(runnable_states[0].get_error())
        self.assertEqual('uuid2', runnable_states[1].get_uuid())
        self.assertEqual('FAILED', runnable_states[1].get_calc_state())
        self.assertEqual('some error', runnable_states[1].get_error())

        rest.expect_get(
            "/adam_object/runnable_state/by_project/MyType/project_uuid", 404, {})
        runnable_states = adam_objects.get_runnable_states('project_uuid')
        self.assertEqual(runnable_states, [])

        rest.expect_get(
            "/adam_object/runnable_state/by_project/MyType/project_uuid", 403, {})
        with self.assertRaises(RuntimeError):
            adam_objects.get_runnable_states('project_uuid')

    def test_get_json(self):
        rest = _RestProxyForTest()
        adam_objects = AdamObjects(rest, 'MyType')

        rest.expect_get("/adam_object/single/MyType/uuid1",
                        200, {'anyKey': 'anyVal'})
        json = adam_objects._get_json('uuid1')
        self.assertEqual({'anyKey': 'anyVal'}, json)

        rest.expect_get("/adam_object/single/MyType/uuid1", 404, {})
        json = adam_objects._get_json('uuid1')
        self.assertEqual(json, None)

        rest.expect_get("/adam_object/single/MyType/uuid1", 403, {})
        with self.assertRaises(RuntimeError):
            adam_objects._get_json('uuid1')

    def test_get_in_project_json(self):
        rest = _RestProxyForTest()
        adam_objects = AdamObjects(rest, 'MyType')

        rest.expect_get(
            "/adam_object/by_project/MyType/project_uuid", 200, {'items': []})
        json = adam_objects._get_in_project_json('project_uuid')
        self.assertEqual(0, len(json))

        rest.expect_get("/adam_object/by_project/MyType/project_uuid", 200,
                        {'items': [{'anyKey': 'anyVal'}, {'anyKey': 'anyOtherVal'}]})
        json = adam_objects._get_in_project_json('project_uuid')
        self.assertEqual(2, len(json))
        self.assertEqual({'anyKey': 'anyVal'}, json[0])
        self.assertEqual({'anyKey': 'anyOtherVal'}, json[1])

        rest.expect_get("/adam_object/by_project/MyType/project_uuid", 404, {})
        json = adam_objects._get_in_project_json('project_uuid')
        self.assertEqual(json, [])

        rest.expect_get("/adam_object/by_project/MyType/project_uuid", 403, {})
        with self.assertRaises(RuntimeError):
            adam_objects._get_in_project_json('project_uuid')

    def test_get_children_json(self):
        rest = _RestProxyForTest()
        adam_objects = AdamObjects(rest, 'MyType')

        rest.expect_get("/adam_object/by_parent/MyType/uuid1", 200,
                        {'childTypes': ['ChildType'], 'childUuids': ['childUuid1']})
        rest.expect_get(
            "/adam_object/single/ChildType/childUuid1", 200, {'anyJson': 5})
        rest.expect_get("/adam_object/runnable_state/single/ChildType/childUuid1", 200,
                        {'uuid': 'childUuid1', 'calculationState': 'COMPLETED'})
        children_json = adam_objects._get_children_json('uuid1')
        self.assertEqual(1, len(children_json))
        child_json, child_runnable_state, child_type = children_json[0]
        self.assertEqual({'anyJson': 5}, child_json)
        self.assertEqual('childUuid1', child_runnable_state.get_uuid())
        self.assertEqual('COMPLETED', child_runnable_state.get_calc_state())
        self.assertIsNone(child_runnable_state.get_error())
        self.assertEqual('ChildType', child_type)

        rest.expect_get("/adam_object/by_parent/MyType/uuid1", 404, {})
        json = adam_objects._get_children_json('uuid1')
        self.assertEqual([], json)

        rest.expect_get("/adam_object/by_parent/MyType/uuid1", 403, {})
        with self.assertRaises(RuntimeError):
            adam_objects._get_children_json('uuid1')

    def test_delete(self):
        rest = _RestProxyForTest()
        adam_objects = AdamObjects(rest, 'MyType')

        rest.expect_delete("/adam_object/single/MyType/uuid1", 204)
        adam_objects.delete('uuid1')

        # 200 isn't a valid return value for delete calls right now
        rest.expect_delete("/adam_object/single/MyType/uuid1", 200)
        with self.assertRaises(RuntimeError):
            adam_objects.delete('uuid1')

        rest.expect_delete("/adam_object/single/MyType/uuid1", 404)
        with self.assertRaises(RuntimeError):
            adam_objects.delete('uuid1')


if __name__ == '__main__':
    unittest.main()
