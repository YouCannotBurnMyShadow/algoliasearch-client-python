# -*- coding: utf-8 -*-

import unittest
from decimal import Decimal

from algoliasearch import algoliasearch

from .helpers import (get_api_client, safe_index_name, wait_key,
                      wait_missing_key)


class ClientTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index_name = safe_index_name(u"àlgol?à-python")
        cls.index_name2 = safe_index_name(u"àlgol?à2-python")
        cls.nameObj = u"à/go/?à2-python"

        cls.client = get_api_client()
        cls.index = cls.client.initIndex(cls.index_name)
        cls.index2 = cls.client.initIndex(cls.index_name2)

    @classmethod
    def tearDownClass(cls):
        cls.client.deleteIndex(cls.index_name)
        cls.client.deleteIndex(cls.index_name2)

    def setUp(self):
        self.client.deleteIndex(self.index_name)
        self.client.deleteIndex(self.index_name2)

    def test_addObject(self):
        task = self.index.addObject({'name': 'Paris'}, self.nameObj)
        self.index.waitTask(task['taskID'])
        results = self.index.search('pa')
        self.assertEquals(len(results['hits']), 1)
        self.assertEquals('Paris', results['hits'][0]['name'])

        task = self.index.addObjects([{'name': 'Los Angeles'},
                                      {'name': 'Los Gatos'}])
        self.index.waitTask(task['taskID'])
        results = self.index.search('los')
        self.assertEquals(len(results['hits']), 2)

        task = self.index.partialUpdateObjects([{
            'name': 'San Francisco',
            'objectID': results['hits'][0]['objectID']
        }, {'name': 'San Marina',
            'objectID': results['hits'][1]['objectID']}])
        self.index.waitTask(task['taskID'])
        results = self.index.search(
            'san', {"attributesToRetrieve": ["name"],
                    "hitsPerPage": 20})
        self.assertEquals(len(results['hits']), 2)

    def test_getObject(self):
        task = self.index.saveObject(
            {"name": "San Francisco",
             "objectID": self.nameObj})
        self.index.waitTask(task['taskID'])

        obj = self.index.getObject(self.nameObj, 'name')
        self.assertEquals(obj['name'], 'San Francisco')

        task = self.index.partialUpdateObject(
            {"name": "San Diego",
             "objectID": self.nameObj})
        self.index.waitTask(task['taskID'])
        obj = self.index.getObject(self.nameObj)
        self.assertEquals(obj['name'], 'San Diego')

        task = self.index.saveObjects(
            [{"name": "Los Angeles",
              "objectID": self.nameObj}])
        self.index.waitTask(task['taskID'])

        obj = self.index.getObject(self.nameObj)
        self.assertEquals(obj['name'], 'Los Angeles')

    def test_getObjects(self):

        task = self.index.addObjects(
            [{"name": "San Francisco",
              "objectID": "1"}, {"name": "Los Angeles",
                                 "objectID": "2"}])
        self.index.waitTask(task['taskID'])

        objs = self.index.getObjects(["1", "2"])
        self.assertEquals(objs["results"][0]['name'], 'San Francisco')
        self.assertEquals(objs["results"][1]['name'], 'Los Angeles')

    def test_deleteObject(self):
        task = self.index.addObject({'name': 'San Francisco'})
        self.index.waitTask(task['taskID'])
        results = self.index.search('')
        self.assertEquals(len(results['hits']), 1)
        res = self.index.deleteObject(results['hits'][0]['objectID'])
        self.index.waitTask(res['taskID'])
        results = self.index.search('')
        self.assertEquals(len(results['hits']), 0)

    def test_listIndexes(self):
        task = self.index.addObject({'name': 'San Francisco'})
        self.index.waitTask(task['taskID'])
        resAfter = self.client.listIndexes()
        is_present = False
        for it in resAfter['items']:
            is_present = is_present or it['name'] == self.index_name
        self.assertEquals(is_present, True)

    def test_clearIndex(self):
        task = self.index.addObject({'name': 'San Francisco'})
        self.index.waitTask(task['taskID'])
        results = self.index.search('')
        self.assertEquals(len(results['hits']), 1)
        task = self.index.clearIndex()
        self.index.waitTask(task['taskID'])
        results = self.index.search('')
        self.assertEquals(len(results['hits']), 0)

    def test_copy(self):
        task = self.index.addObject({'name': 'San Francisco'})
        self.index.waitTask(task['taskID'])
        task = self.client.copyIndex(self.index_name, self.index_name2)
        self.index.waitTask(task['taskID'])
        results = self.index2.search('')
        self.assertEquals(len(results['hits']), 1)
        self.assertEquals(results['hits'][0]['name'], 'San Francisco')

    def test_move(self):
        task = self.index.addObject({'name': 'San Francisco'})
        self.index.waitTask(task['taskID'])
        task = self.client.moveIndex(self.index_name, self.index_name2)
        self.index.waitTask(task['taskID'])
        results = self.index2.search('')
        self.assertEquals(len(results['hits']), 1)
        self.assertEquals(results['hits'][0]['name'], 'San Francisco')

    def test_browse(self):
        try:
            task = self.index.clearIndex()
            self.index.waitTask(task['taskID'])
        except algoliasearch.AlgoliaException:
            pass
        task = self.index.addObject({'name': 'San Francisco'})
        self.index.waitTask(task['taskID'])
        res = self.index.browse()
        self.assertEquals(len(res['hits']), 1)
        self.assertEquals(res['hits'][0]['name'], 'San Francisco')

    def test_log(self):
        res = self.client.getLogs()
        self.assertTrue(len(res['logs']) > 0)

    def test_batch(self):
        task = self.index.batch([
            {'action': 'addObject', 'body': {'name': 'San Francisco'}},
            {'action': 'addObject', 'body': {'name': 'Los Angeles'}},
            {'action': 'updateObject', 'body': {'name': 'San Diego'}, 'objectID': '42'},
            {'action': 'updateObject', 'body': {'name': 'Los Gatos'}, 'objectID': self.nameObj}
        ])
        self.index.waitTask(task['taskID'])
        obj = self.index.getObject("42")
        self.assertEquals(obj['name'], 'San Diego')

        res = self.index.search('')
        self.assertEquals(len(res['hits']), 4)

    def test_batchDelete(self):
        task = self.index.batch([
            {'action': 'addObject', 'body': {'name': 'San Francisco', 'objectID': '40'}},
            {'action': 'addObject', 'body': {'name': 'Los Angeles', 'objectID': '41'}},
            {'action': 'updateObject', 'body': {'name': 'San Diego'}, 'objectID': '42'},
            {'action': 'updateObject', 'body': {'name': 'Los Gatos'}, 'objectID': self.nameObj}
        ])
        self.index.waitTask(task['taskID'])
        task = self.index.deleteObjects(['40', '41', '42', self.nameObj])
        self.index.waitTask(task['taskID'])

        res = self.index.search('')
        self.assertEquals(len(res['hits']), 0)

    def test_deleteByQuery(self):
        task = self.index.batch([
            {'action': 'addObject', 'body': {'name': 'San Francisco', 'objectID': '40'}},
            {'action': 'addObject', 'body': {'name': 'San Francisco', 'objectID': '41'}},
            {'action': 'addObject', 'body': {'name': 'Los Angeles', 'objectID': '42'}}
        ])
        self.index.waitTask(task['taskID'])

        task = self.index.deleteByQuery("San Francisco")
        self.index.waitTask(task['taskID'])

        res = self.index.search('')
        self.assertEquals(len(res['hits']), 1)

    def test_user_key(self):
        task = self.index.addObject({'name': 'Paris'}, self.nameObj)
        self.index.waitTask(task['taskID'])
        newKey = self.index.addUserKey(['search'])
        wait_key(self.index, newKey['key'])
        self.assertTrue(newKey['key'] != "")
        resAfter = self.index.listUserKeys()
        is_present = False
        for it in resAfter['keys']:
            is_present = is_present or it['value'] == newKey['key']
        self.assertTrue(is_present)
        key = self.index.getUserKeyACL(newKey['key'])
        self.assertEquals(key['acl'][0], 'search')
        task = self.index.deleteUserKey(newKey['key'])
        wait_missing_key(self.index, newKey['key'])
        resEnd = self.index.listUserKeys()
        is_present = False
        for it in resEnd['keys']:
            is_present = is_present or it['value'] == newKey['key']
        self.assertTrue(not is_present)

        newKey = self.client.addUserKey(['search'])
        wait_key(self.client, newKey['key'])
        self.assertTrue(newKey['key'] != "")
        resAfter = self.client.listUserKeys()
        is_present = False
        for it in resAfter['keys']:
            is_present = is_present or it['value'] == newKey['key']
        self.assertTrue(is_present)
        key = self.client.getUserKeyACL(newKey['key'])
        self.assertEquals(key['acl'][0], 'search')
        task = self.client.deleteUserKey(newKey['key'])
        wait_missing_key(self.client, newKey['key'])
        resEnd = self.client.listUserKeys()
        is_present = False
        for it in resEnd['keys']:
            is_present = is_present or it['value'] == newKey['key']
        self.assertTrue(not is_present)

    def test_settings(self):
        task = self.index.setSettings({'attributesToRetrieve': ['name']})
        self.index.waitTask(task['taskID'])
        settings = self.index.getSettings()
        self.assertEquals(len(settings['attributesToRetrieve']), 1)
        self.assertEquals(settings['attributesToRetrieve'][0], 'name')

    def test_URLEncode(self):

        task = self.index.saveObject(
            {"name": "San Francisco",
             "objectID": self.nameObj})
        self.index.waitTask(task['taskID'])

        obj = self.index.getObject(self.nameObj, 'name')
        self.assertEquals(obj['name'], 'San Francisco')

        task = self.index.partialUpdateObject(
            {"name": "San Diego",
             "objectID": self.nameObj})
        self.index.waitTask(task['taskID'])
        obj = self.index.getObject(self.nameObj)
        self.assertEquals(obj['name'], 'San Diego')

        task = self.index.saveObjects(
            [{"name": "Los Angeles",
              "objectID": self.nameObj}])
        self.index.waitTask(task['taskID'])

        obj = self.index.getObject(self.nameObj)
        self.assertEquals(obj['name'], 'Los Angeles')

    def test_multipleQueries(self):
        task = self.index.addObject({'name': 'Paris'}, self.nameObj)
        self.index.waitTask(task['taskID'])
        results = self.client.multipleQueries([{"indexName": self.index_name, "query": ""}])
        self.assertEquals(len(results['results']), 1)
        self.assertEquals(len(results['results'][0]['hits']), 1)
        self.assertEquals('Paris', results['results'][0]['hits'][0]['name'])

    def test_decimal(self):
        value = Decimal('3.14')
        task = self.index.save_object({
            'value': value,
            'objectID': self.nameObj
        })
        self.index.wait_task(task['taskID'])

        obj = self.index.get_object(self.nameObj)
        self.assertEquals(obj['value'], float(value))

    def test_float(self):
        value = float('3.14')
        task = self.index.saveObject(
            {"value": value,
             "objectID": self.nameObj})
        self.index.waitTask(task['taskID'])

        obj = self.index.getObject(self.nameObj)
        self.assertEquals(obj['value'], value)

    def test_disjunctive_faceting(self):
        self.index.setSettings(
            {"attributesForFacetting": ['city', 'stars', 'facilities']})
        task = self.index.addObjects([{
            "name": 'Hotel A',
            "stars": '*',
            "facilities": ['wifi', 'bath', 'spa'],
            "city": 'Paris'
        }, {
            "name": 'Hotel B',
            "stars": '*',
            "facilities": ['wifi'],
            "city": 'Paris'
        }, {
            "name": 'Hotel C',
            "stars": '**',
            "facilities": ['bath'],
            "city": 'San Francisco'
        }, {
            "name": 'Hotel D',
            "stars": '****',
            "facilities": ['spa'],
            "city": 'Paris'
        }, {
            "name": 'Hotel E',
            "stars": '****',
            "facilities": ['spa'],
            "city": 'New York'
        }])
        self.index.waitTask(task['taskID'])

        answer = self.index.searchDisjunctiveFaceting(
            'h', ['stars', 'facilities'], {"facets": "city"})
        self.assertEquals(answer['nbHits'], 5)
        self.assertEquals(len(answer['facets']), 1)
        self.assertEquals(len(answer['disjunctiveFacets']), 2)

        answer = self.index.searchDisjunctiveFaceting('h', [
            'stars', 'facilities'
        ], {"facets": "city"}, {"stars": ["*"]})
        self.assertEquals(answer['nbHits'], 2)
        self.assertEquals(len(answer['facets']), 1)
        self.assertEquals(len(answer['disjunctiveFacets']), 2)
        self.assertEquals(answer['disjunctiveFacets']['stars']['*'], 2)
        self.assertEquals(answer['disjunctiveFacets']['stars']['**'], 1)
        self.assertEquals(answer['disjunctiveFacets']['stars']['****'], 2)

        answer = self.index.searchDisjunctiveFaceting('h', [
            'stars', 'facilities'
        ], {"facets": "city"}, {"stars": ['*'],
                                "city": ["Paris"]})
        self.assertEquals(answer['nbHits'], 2)
        self.assertEquals(len(answer['facets']), 1)
        self.assertEquals(len(answer['disjunctiveFacets']), 2)
        self.assertEquals(answer['disjunctiveFacets']['stars']['*'], 2)
        self.assertEquals(answer['disjunctiveFacets']['stars']['****'], 1)

        answer = self.index.searchDisjunctiveFaceting('h', [
            'stars', 'facilities'
        ], {"facets": "city"}, {"stars": ['*', '****'],
                                "city": ["Paris"]})
        self.assertEquals(answer['nbHits'], 3)
        self.assertEquals(len(answer['facets']), 1)
        self.assertEquals(len(answer['disjunctiveFacets']), 2)
        self.assertEquals(answer['disjunctiveFacets']['stars']['*'], 2)
        self.assertEquals(answer['disjunctiveFacets']['stars']['****'], 1)

    def test_encodeBoolean(self):
        task = self.index.addObject({'score': 3525}, self.nameObj)
        self.index.waitTask(task['taskID'])
        results = self.index.search('353',
                                    {"allowTyposOnNumericTokens": False})
        self.assertEquals(len(results['hits']), 0)

    def test_attributeToRetrieve(self):
        task = self.index.addObject({'name': 'Paris',
                                     'short_name': 'Pa'}, self.nameObj)
        self.index.waitTask(task['taskID'])
        results = self.index.search(
            '', {'attributesToRetrieve': ['name', 'short_name']})
        self.assertEquals(len(results['hits']), 1)
        self.assertEquals('Paris', results['hits'][0]['name'])
        self.assertEquals('Pa', results['hits'][0]['short_name'])

        results = self.index.search(
            '', {'attributesToRetrieve': "name,short_name"})
        self.assertEquals(len(results['hits']), 1)
        self.assertEquals('Paris', results['hits'][0]['name'])
        self.assertEquals('Pa', results['hits'][0]['short_name'])
