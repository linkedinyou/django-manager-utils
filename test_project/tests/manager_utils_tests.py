from django.test import TestCase
from django_dynamic_fixture import G
from manager_utils import post_bulk_operation

from test_project.models import TestModel, TestForeignKeyModel


class BulkUpsertTest(TestCase):
    """
    Tests the bulk_upsert function.
    """
    def test_wo_unique_fields(self):
        """
        Tests bulk_upsert with no unique fields. A ValueError should be raised since it is required to provide a
        list of unique_fields.
        """
        with self.assertRaises(ValueError):
            TestModel.objects.bulk_upsert([], [], ['field'])

    def test_wo_update_fields(self):
        """
        Tests bulk_upsert with no update fields. A ValueError should be raised since it is required to provide a
        list of update_fields.
        """
        with self.assertRaises(ValueError):
            TestModel.objects.bulk_upsert([], ['field'], [])

    def test_w_blank_arguments(self):
        """
        Tests using required arguments and using blank arguments for everything else.
        """
        TestModel.objects.bulk_upsert([], ['field'], ['field'])
        self.assertEquals(TestModel.objects.count(), 0)

    def test_no_updates(self):
        """
        Tests the case when no updates were previously stored (i.e objects are only created)
        """
        TestModel.objects.bulk_upsert([
            TestModel(int_field=0, char_field='0', float_field=0),
            TestModel(int_field=1, char_field='1', float_field=1),
            TestModel(int_field=2, char_field='2', float_field=2),
        ], ['int_field'], ['char_field', 'float_field'])

        for i, model_obj in enumerate(TestModel.objects.order_by('int_field')):
            self.assertEqual(model_obj.int_field, i)
            self.assertEqual(model_obj.char_field, str(i))
            self.assertAlmostEqual(model_obj.float_field, i)

    def test_all_updates_unique_int_field(self):
        """
        Tests the case when all updates were previously stored and the int field is used as a uniqueness
        constraint.
        """
        # Create previously stored test models with a unique int field and -1 for all other fields
        for i in range(3):
            G(TestModel, int_field=i, char_field='-1', float_field=-1)

        # Update using the int field as a uniqueness constraint
        TestModel.objects.bulk_upsert([
            TestModel(int_field=0, char_field='0', float_field=0),
            TestModel(int_field=1, char_field='1', float_field=1),
            TestModel(int_field=2, char_field='2', float_field=2),
        ], ['int_field'], ['char_field', 'float_field'])

        # Verify that the fields were updated
        self.assertEquals(TestModel.objects.count(), 3)
        for i, model_obj in enumerate(TestModel.objects.order_by('int_field')):
            self.assertEqual(model_obj.int_field, i)
            self.assertEqual(model_obj.char_field, str(i))
            self.assertAlmostEqual(model_obj.float_field, i)

    def test_all_updates_unique_int_field_update_float_field(self):
        """
        Tests the case when all updates were previously stored and the int field is used as a uniqueness
        constraint. Only updates the float field
        """
        # Create previously stored test models with a unique int field and -1 for all other fields
        for i in range(3):
            G(TestModel, int_field=i, char_field='-1', float_field=-1)

        # Update using the int field as a uniqueness constraint
        TestModel.objects.bulk_upsert([
            TestModel(int_field=0, char_field='0', float_field=0),
            TestModel(int_field=1, char_field='1', float_field=1),
            TestModel(int_field=2, char_field='2', float_field=2),
        ], ['int_field'], update_fields=['float_field'])

        # Verify that the float field was updated
        self.assertEquals(TestModel.objects.count(), 3)
        for i, model_obj in enumerate(TestModel.objects.order_by('int_field')):
            self.assertEqual(model_obj.int_field, i)
            self.assertEqual(model_obj.char_field, '-1')
            self.assertAlmostEqual(model_obj.float_field, i)

    def test_some_updates_unique_int_field_update_float_field(self):
        """
        Tests the case when some updates were previously stored and the int field is used as a uniqueness
        constraint. Only updates the float field.
        """
        # Create previously stored test models with a unique int field and -1 for all other fields
        for i in range(2):
            G(TestModel, int_field=i, char_field='-1', float_field=-1)

        # Update using the int field as a uniqueness constraint. The first two are updated while the third is created
        TestModel.objects.bulk_upsert([
            TestModel(int_field=0, char_field='0', float_field=0),
            TestModel(int_field=1, char_field='1', float_field=1),
            TestModel(int_field=2, char_field='2', float_field=2),
        ], ['int_field'], ['float_field'])

        # Verify that the float field was updated for the first two models and the char field was not updated for
        # the first two. The char field, however, should be '2' for the third model since it was created
        self.assertEquals(TestModel.objects.count(), 3)
        for i, model_obj in enumerate(TestModel.objects.order_by('int_field')):
            self.assertEqual(model_obj.int_field, i)
            self.assertEqual(model_obj.char_field, '-1' if i < 2 else '2')
            self.assertAlmostEqual(model_obj.float_field, i)

    def test_some_updates_unique_int_char_field_update_float_field(self):
        """
        Tests the case when some updates were previously stored and the int and char fields are used as a uniqueness
        constraint. Only updates the float field.
        """
        # Create previously stored test models with a unique int and char field
        for i in range(2):
            G(TestModel, int_field=i, char_field=str(i), float_field=-1)

        # Update using the int field as a uniqueness constraint. The first two are updated while the third is created
        TestModel.objects.bulk_upsert([
            TestModel(int_field=0, char_field='0', float_field=0),
            TestModel(int_field=1, char_field='1', float_field=1),
            TestModel(int_field=2, char_field='2', float_field=2),
        ], ['int_field', 'char_field'], ['float_field'])

        # Verify that the float field was updated for the first two models and the char field was not updated for
        # the first two. The char field, however, should be '2' for the third model since it was created
        self.assertEquals(TestModel.objects.count(), 3)
        for i, model_obj in enumerate(TestModel.objects.order_by('int_field')):
            self.assertEqual(model_obj.int_field, i)
            self.assertEqual(model_obj.char_field, str(i))
            self.assertAlmostEqual(model_obj.float_field, i)

    def test_no_updates_unique_int_char_field(self):
        """
        Tests the case when no updates were previously stored and the int and char fields are used as a uniqueness
        constraint. In this case, there is data previously stored, but the uniqueness constraints dont match.
        """
        # Create previously stored test models with a unique int field and -1 for all other fields
        for i in range(3):
            G(TestModel, int_field=i, char_field='-1', float_field=-1)

        # Update using the int and char field as a uniqueness constraint. All three objects are created
        TestModel.objects.bulk_upsert([
            TestModel(int_field=0, char_field='0', float_field=0),
            TestModel(int_field=1, char_field='1', float_field=1),
            TestModel(int_field=2, char_field='2', float_field=2),
        ], ['int_field', 'char_field'], ['float_field'])

        # Verify that no updates occured
        self.assertEquals(TestModel.objects.count(), 6)
        self.assertEquals(TestModel.objects.filter(char_field='-1').count(), 3)
        for i, model_obj in enumerate(TestModel.objects.filter(char_field='-1').order_by('int_field')):
            self.assertEqual(model_obj.int_field, i)
            self.assertEqual(model_obj.char_field, '-1')
            self.assertAlmostEqual(model_obj.float_field, -1)
        self.assertEquals(TestModel.objects.exclude(char_field='-1').count(), 3)
        for i, model_obj in enumerate(TestModel.objects.exclude(char_field='-1').order_by('int_field')):
            self.assertEqual(model_obj.int_field, i)
            self.assertEqual(model_obj.char_field, str(i))
            self.assertAlmostEqual(model_obj.float_field, i)

    def test_some_updates_unique_int_char_field_queryset(self):
        """
        Tests the case when some updates were previously stored and a queryset is used on the bulk upsert.
        """
        # Create previously stored test models with a unique int field and -1 for all other fields
        for i in range(3):
            G(TestModel, int_field=i, char_field='-1', float_field=-1)

        # Update using the int field as a uniqueness constraint on a queryset. Only one object should be updated.
        TestModel.objects.filter(int_field=0).bulk_upsert([
            TestModel(int_field=0, char_field='0', float_field=0),
            TestModel(int_field=1, char_field='1', float_field=1),
            TestModel(int_field=2, char_field='2', float_field=2),
        ], ['int_field'], ['float_field'])

        # Verify that two new objecs were inserted
        self.assertEquals(TestModel.objects.count(), 5)
        self.assertEquals(TestModel.objects.filter(char_field='-1').count(), 3)
        for i, model_obj in enumerate(TestModel.objects.filter(char_field='-1').order_by('int_field')):
            self.assertEqual(model_obj.int_field, i)
            self.assertEqual(model_obj.char_field, '-1')


class PostBulkOperationSignalTest(TestCase):
    """
    Tests that the post_bulk_operation signal is emitted on all functions that emit the signal.
    """
    def setUp(self):
        """
        Defines a siangl handler that collects information about fired signals
        """
        class SignalHandler(object):
            num_times_called = 0
            model = None

            def __call__(self, *args, **kwargs):
                self.num_times_called += 1
                self.model = kwargs['model']

        self.signal_handler = SignalHandler()
        post_bulk_operation.connect(self.signal_handler)

    def tearDown(self):
        """
        Disconnect the siangl to make sure it doesn't get connected multiple times.
        """
        post_bulk_operation.disconnect(self.signal_handler)

    def test_post_bulk_operation_queryset_update(self):
        """
        Tests that the update operation on a queryset emits the post_bulk_operation signal.
        """
        TestModel.objects.all().update(int_field=1)

        self.assertEquals(self.signal_handler.model, TestModel)
        self.assertEquals(self.signal_handler.num_times_called, 1)

    def test_post_bulk_operation_manager_update(self):
        """
        Tests that the update operation on a manager emits the post_bulk_operation signal.
        """
        TestModel.objects.update(int_field=1)

        self.assertEquals(self.signal_handler.model, TestModel)
        self.assertEquals(self.signal_handler.num_times_called, 1)

    def test_post_bulk_operation_bulk_update(self):
        """
        Tests that the bulk_update operation emits the post_bulk_operation signal.
        """
        model_obj = TestModel.objects.create(int_field=2)
        TestModel.objects.bulk_update([model_obj], ['int_field'])

        self.assertEquals(self.signal_handler.model, TestModel)
        self.assertEquals(self.signal_handler.num_times_called, 1)

    def test_post_bulk_operation_bulk_create(self):
        """
        Tests that the bulk_create operation emits the post_bulk_operation signal.
        """
        TestModel.objects.bulk_create([TestModel(int_field=2)])

        self.assertEquals(self.signal_handler.model, TestModel)
        self.assertEquals(self.signal_handler.num_times_called, 1)

    def test_save_doesnt_emit_signal(self):
        """
        Tests that a non-bulk operation doesn't emit the signal.
        """
        model_obj = TestModel.objects.create(int_field=2)
        model_obj.save()

        self.assertEquals(self.signal_handler.num_times_called, 0)


class IdDictTest(TestCase):
    """
    Tests the id_dict function.
    """
    def test_no_objects_manager(self):
        """
        Tests the output when no objects are present in the manager.
        """
        self.assertEquals(TestModel.objects.id_dict(), {})

    def test_objects_manager(self):
        """
        Tests retrieving a dict of objects keyed on their ID from the manager.
        """
        model_obj1 = G(TestModel, int_field=1)
        model_obj2 = G(TestModel, int_field=2)
        self.assertEquals(TestModel.objects.id_dict(), {model_obj1.id: model_obj1, model_obj2.id: model_obj2})

    def test_no_objects_queryset(self):
        """
        Tests the case when no objects are returned via a queryset.
        """
        G(TestModel, int_field=1)
        G(TestModel, int_field=2)
        self.assertEquals(TestModel.objects.filter(int_field__gte=3).id_dict(), {})

    def test_objects_queryset(self):
        """
        Tests the case when objects are returned via a queryset.
        """
        G(TestModel, int_field=1)
        model_obj = G(TestModel, int_field=2)
        self.assertEquals(TestModel.objects.filter(int_field__gte=2).id_dict(), {model_obj.id: model_obj})


class GetOrNoneTest(TestCase):
    """
    Tests the get_or_none function in the manager utils
    """
    def test_existing_using_objects(self):
        """
        Tests get_or_none on an existing object from Model.objects.
        """
        # Create an existing model
        model_obj = G(TestModel)
        # Verify that get_or_none on objects returns the test model
        self.assertEquals(model_obj, TestModel.objects.get_or_none(id=model_obj.id))

    def test_multiple_error_using_objects(self):
        """
        Tests get_or_none on multiple existing objects from Model.objects.
        """
        # Create an existing model
        model_obj = G(TestModel, char_field='hi')
        model_obj = G(TestModel, char_field='hi')
        # Verify that get_or_none on objects returns the test model
        with self.assertRaises(TestModel.MultipleObjectsReturned):
            self.assertEquals(model_obj, TestModel.objects.get_or_none(char_field='hi'))

    def test_existing_using_queryset(self):
        """
        Tests get_or_none on an existing object from a queryst.
        """
        # Create an existing model
        model_obj = G(TestModel)
        # Verify that get_or_none on objects returns the test model
        self.assertEquals(model_obj, TestModel.objects.filter(id=model_obj.id).get_or_none(id=model_obj.id))

    def test_none_using_objects(self):
        """
        Tests when no object exists when using Model.objects.
        """
        # Verify that get_or_none on objects returns the test model
        self.assertIsNone(TestModel.objects.get_or_none(id=1))

    def test_none_using_queryset(self):
        """
        Tests when no object exists when using a queryset.
        """
        # Verify that get_or_none on objects returns the test model
        self.assertIsNone(TestModel.objects.filter(id=1).get_or_none(id=1))


class SingleTest(TestCase):
    """
    Tests the single function in the manager utils.
    """
    def test_none_using_objects(self):
        """
        Tests when there are no objects using Model.objects.
        """
        with self.assertRaises(TestModel.DoesNotExist):
            TestModel.objects.single()

    def test_multiple_using_objects(self):
        """
        Tests when there are multiple objects using Model.objects.
        """
        G(TestModel)
        G(TestModel)
        with self.assertRaises(TestModel.MultipleObjectsReturned):
            TestModel.objects.single()

    def test_none_using_queryset(self):
        """
        Tests when there are no objects using a queryset.
        """
        with self.assertRaises(TestModel.DoesNotExist):
            TestModel.objects.filter(id__gte=0).single()

    def test_multiple_using_queryset(self):
        """
        Tests when there are multiple objects using a queryset.
        """
        G(TestModel)
        G(TestModel)
        with self.assertRaises(TestModel.MultipleObjectsReturned):
            TestModel.objects.filter(id__gte=0).single()

    def test_single_using_objects(self):
        """
        Tests accessing a single object using Model.objects.
        """
        model_obj = G(TestModel)
        self.assertEquals(model_obj, TestModel.objects.single())

    def test_single_using_queryset(self):
        """
        Tests accessing a single object using a queryset.
        """
        model_obj = G(TestModel)
        self.assertEquals(model_obj, TestModel.objects.filter(id__gte=0).single())

    def test_mutliple_to_single_using_queryset(self):
        """
        Tests accessing a single object using a queryset. The queryset is what filters it
        down to a single object.
        """
        model_obj = G(TestModel)
        G(TestModel)
        self.assertEquals(model_obj, TestModel.objects.filter(id=model_obj.id).single())


class BulkUpdateTest(TestCase):
    """
    Tests the bulk_update function.
    """
    def test_none(self):
        """
        Tests when no values are provided to bulk update.
        """
        TestModel.objects.bulk_update([], [])

    def test_objs_no_fields_to_update(self):
        """
        Tests when objects are given to bulk update with no fields to update. Nothing should change in
        the objects.
        """
        test_obj_1 = G(TestModel, int_field=1)
        test_obj_2 = G(TestModel, int_field=2)
        # Change the int fields on the models
        test_obj_1.int_field = 3
        test_obj_2.int_field = 4
        # Do a bulk update with no update fields
        TestModel.objects.bulk_update([test_obj_1, test_obj_2], [])
        # The test objects int fields should be untouched
        test_obj_1 = TestModel.objects.get(id=test_obj_1.id)
        test_obj_2 = TestModel.objects.get(id=test_obj_2.id)
        self.assertEquals(test_obj_1.int_field, 1)
        self.assertEquals(test_obj_2.int_field, 2)

    def test_objs_one_field_to_update(self):
        """
        Tests when objects are given to bulk update with one field to update.
        """
        test_obj_1 = G(TestModel, int_field=1)
        test_obj_2 = G(TestModel, int_field=2)
        # Change the int fields on the models
        test_obj_1.int_field = 3
        test_obj_2.int_field = 4
        # Do a bulk update with the int fields
        TestModel.objects.bulk_update([test_obj_1, test_obj_2], ['int_field'])
        # The test objects int fields should be untouched
        test_obj_1 = TestModel.objects.get(id=test_obj_1.id)
        test_obj_2 = TestModel.objects.get(id=test_obj_2.id)
        self.assertEquals(test_obj_1.int_field, 3)
        self.assertEquals(test_obj_2.int_field, 4)

    def test_objs_one_field_to_update_ignore_other_field(self):
        """
        Tests when objects are given to bulk update with one field to update. This test changes another field
        not included in the update and verifies it is not updated.
        """
        test_obj_1 = G(TestModel, int_field=1, float_field=1.0)
        test_obj_2 = G(TestModel, int_field=2, float_field=2.0)
        # Change the int and float fields on the models
        test_obj_1.int_field = 3
        test_obj_2.int_field = 4
        test_obj_1.float_field = 3.0
        test_obj_2.float_field = 4.0
        # Do a bulk update with the int fields
        TestModel.objects.bulk_update([test_obj_1, test_obj_2], ['int_field'])
        # The test objects int fields should be untouched
        test_obj_1 = TestModel.objects.get(id=test_obj_1.id)
        test_obj_2 = TestModel.objects.get(id=test_obj_2.id)
        self.assertEquals(test_obj_1.int_field, 3)
        self.assertEquals(test_obj_2.int_field, 4)
        # The float fields should not be updated
        self.assertEquals(test_obj_1.float_field, 1.0)
        self.assertEquals(test_obj_2.float_field, 2.0)

    def test_objs_two_fields_to_update(self):
        """
        Tests when objects are given to bulk update with two fields to update.
        """
        test_obj_1 = G(TestModel, int_field=1, float_field=1.0)
        test_obj_2 = G(TestModel, int_field=2, float_field=2.0)
        # Change the int and float fields on the models
        test_obj_1.int_field = 3
        test_obj_2.int_field = 4
        test_obj_1.float_field = 3.0
        test_obj_2.float_field = 4.0
        # Do a bulk update with the int fields
        TestModel.objects.bulk_update([test_obj_1, test_obj_2], ['int_field', 'float_field'])
        # The test objects int fields should be untouched
        test_obj_1 = TestModel.objects.get(id=test_obj_1.id)
        test_obj_2 = TestModel.objects.get(id=test_obj_2.id)
        self.assertEquals(test_obj_1.int_field, 3)
        self.assertEquals(test_obj_2.int_field, 4)
        # The float fields should be updated
        self.assertEquals(test_obj_1.float_field, 3.0)
        self.assertEquals(test_obj_2.float_field, 4.0)


class UpsertTest(TestCase):
    """
    Tests the upsert method in the manager utils.
    """
    def test_upsert_creation_no_defaults(self):
        """
        Tests an upsert that results in a created object. Don't use defaults
        """
        model_obj, created = TestModel.objects.upsert(int_field=1)
        self.assertTrue(created)
        self.assertEquals(model_obj.int_field, 1)
        self.assertIsNone(model_obj.float_field)
        self.assertIsNone(model_obj.char_field)

    def test_upsert_creation_defaults(self):
        """
        Tests an upsert that results in a created object. Defaults are used.
        """
        model_obj, created = TestModel.objects.upsert(int_field=1, defaults={'float_field': 1.0})
        self.assertTrue(created)
        self.assertEquals(model_obj.int_field, 1)
        self.assertEquals(model_obj.float_field, 1.0)
        self.assertIsNone(model_obj.char_field)

    def test_upsert_creation_updates(self):
        """
        Tests an upsert that results in a created object. Updates are used.
        """
        model_obj, created = TestModel.objects.upsert(int_field=1, updates={'float_field': 1.0})
        self.assertTrue(created)
        self.assertEquals(model_obj.int_field, 1)
        self.assertEquals(model_obj.float_field, 1.0)
        self.assertIsNone(model_obj.char_field)

    def test_upsert_creation_defaults_updates(self):
        """
        Tests an upsert that results in a created object. Defaults are used and so are updates.
        """
        model_obj, created = TestModel.objects.upsert(
            int_field=1, defaults={'float_field': 1.0}, updates={'char_field': 'Hello'})
        self.assertTrue(created)
        self.assertEquals(model_obj.int_field, 1)
        self.assertEquals(model_obj.float_field, 1.0)
        self.assertEquals(model_obj.char_field, 'Hello')

    def test_upsert_creation_no_defaults_override(self):
        """
        Tests an upsert that results in a created object. Defaults are not used and
        the updates values override the defaults on creation.
        """
	test_model = G(TestModel)
        model_obj, created = TestForeignKeyModel.objects.upsert(int_field=1, updates={
            'test_model': test_model,
        })
        self.assertTrue(created)
        self.assertEquals(model_obj.int_field, 1)
        self.assertEquals(model_obj.test_model, test_model)

    def test_upsert_creation_defaults_updates_override(self):
        """
        Tests an upsert that results in a created object. Defaults are used and so are updates. Updates
        override the defaults.
        """
        model_obj, created = TestModel.objects.upsert(
            int_field=1, defaults={'float_field': 1.0}, updates={'char_field': 'Hello', 'float_field': 2.0})
        self.assertTrue(created)
        self.assertEquals(model_obj.int_field, 1)
        self.assertEquals(model_obj.float_field, 2.0)
        self.assertEquals(model_obj.char_field, 'Hello')

    def test_upsert_no_creation_no_defaults(self):
        """
        Tests an upsert that already exists. Don't use defaults
        """
        G(TestModel, int_field=1, float_field=None, char_field=None)
        model_obj, created = TestModel.objects.upsert(int_field=1)
        self.assertFalse(created)
        self.assertEquals(model_obj.int_field, 1)
        self.assertIsNone(model_obj.float_field)
        self.assertIsNone(model_obj.char_field)

    def test_upsert_no_creation_defaults(self):
        """
        Tests an upsert that already exists. Defaults are used but don't matter since the object already existed.
        """
        G(TestModel, int_field=1, float_field=None, char_field=None)
        model_obj, created = TestModel.objects.upsert(int_field=1, defaults={'float_field': 1.0})
        self.assertFalse(created)
        self.assertEquals(model_obj.int_field, 1)
        self.assertIsNone(model_obj.float_field)
        self.assertIsNone(model_obj.char_field)

    def test_upsert_no_creation_updates(self):
        """
        Tests an upsert that already exists. Updates are used.
        """
        G(TestModel, int_field=1, float_field=2.0, char_field=None)
        model_obj, created = TestModel.objects.upsert(int_field=1, updates={'float_field': 1.0})
        self.assertFalse(created)
        self.assertEquals(model_obj.int_field, 1)
        self.assertEquals(model_obj.float_field, 1.0)
        self.assertIsNone(model_obj.char_field)

    def test_upsert_no_creation_defaults_updates(self):
        """
        Tests an upsert that already exists. Defaults are used and so are updates.
        """
        G(TestModel, int_field=1, float_field=2.0, char_field='Hi')
        model_obj, created = TestModel.objects.upsert(
            int_field=1, defaults={'float_field': 1.0}, updates={'char_field': 'Hello'})
        self.assertFalse(created)
        self.assertEquals(model_obj.int_field, 1)
        self.assertEquals(model_obj.float_field, 2.0)
        self.assertEquals(model_obj.char_field, 'Hello')

    def test_upsert_no_creation_defaults_updates_override(self):
        """
        Tests an upsert that already exists. Defaults are used and so are updates. Updates override the defaults.
        """
        G(TestModel, int_field=1, float_field=3.0, char_field='Hi')
        model_obj, created = TestModel.objects.upsert(
            int_field=1, defaults={'float_field': 1.0}, updates={'char_field': 'Hello', 'float_field': 2.0})
        self.assertFalse(created)
        self.assertEquals(model_obj.int_field, 1)
        self.assertEquals(model_obj.float_field, 2.0)
        self.assertEquals(model_obj.char_field, 'Hello')
