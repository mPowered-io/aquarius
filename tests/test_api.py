#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0
import copy
import json

from plecos import plecos

from aquarius.app.assets import validate_date_format
from aquarius.constants import BaseURLs
from aquarius.run import get_status, get_version
from tests.ddo_samples_invalid import json_dict_no_metadata, json_dict_no_valid_metadata
from tests.ddos.ddo_sample1 import json_dict
from tests.ddos.ddo_sample2 import json_dict2
from tests.ddos.ddo_sample_algorithm import algorithm_ddo_sample
from tests.ddos.ddo_sample_updates import json_before, json_update, json_valid
from eth_account.messages import encode_defunct
from eth_account import Account


def run_request_get_data(client_method, url, data=None):
    _response = run_request(client_method, url, data)
    if _response and _response.data:
        return json.loads(_response.data.decode('utf-8'))

    return None


def run_request(client_method, url, data=None):
    if data is None:
        _response = client_method(url, content_type='application/json')
    else:
        _response = client_method(
            url, data=json.dumps(data), content_type='application/json'
        )

    return _response


def test_version(client):
    """Test version in root endpoint"""
    rv = client.get('/')
    assert json.loads(rv.data.decode('utf-8'))['software'] == 'Aquarius'
    assert json.loads(rv.data.decode('utf-8'))['version'] == get_version()


def test_health(client):
    """Test health check endpoint"""
    rv = client.get('/health')
    assert rv.data.decode('utf-8') == get_status()[0]


def test_create_ddo(client, base_ddo_url):
    """Test creation of asset"""
    rv = run_request_get_data(
        client.get, base_ddo_url + '/%s' % json_dict['id'])
    assert json_dict['id'] in rv['id']
    assert json_dict['@context'] in rv['@context']
    assert json_dict['service'][2]['type'] in rv['service'][0]['type']


def test_upsert_ddo(client_with_no_data, base_ddo_url):
    """Test creation of asset"""
    put = client_with_no_data.put(base_ddo_url + '/%s' % json_dict['id'],
                                  data=json.dumps(json_dict2),
                                  content_type='application/json')
    assert put.status_code in (200, 201), 'Failed to register/update asset.'

    rv = run_request_get_data(
        client_with_no_data.get,
        base_ddo_url + '/%s' % json.loads(put.data.decode('utf-8'))['id']
    )
    assert 201 == put.status_code
    assert json_dict['id'] in rv['id']
    assert json_dict['@context'] in rv['@context']
    assert json_dict['service'][2]['type'] in rv['service'][0]['type']
    client_with_no_data.delete(
        base_ddo_url + '/%s' % json.loads(put.data.decode('utf-8'))['id'])


def test_post_with_no_ddo(client, base_ddo_url):
    post = client.post(base_ddo_url,
                       data=json.dumps(json_dict_no_metadata),
                       content_type='application/json')
    assert 400 == post.status_code


def test_post_with_no_valid_ddo(client, base_ddo_url):
    post = client.post(base_ddo_url,
                       data=json.dumps(json_dict_no_valid_metadata),
                       content_type='application/json')
    assert 400 == post.status_code


def test_update_ddo(client_with_no_data, base_ddo_url):
    client = client_with_no_data
    post = run_request_get_data(client.post, base_ddo_url, data=json_before)
    put = client.put(
        base_ddo_url + '/%s' % post['id'],
        data=json.dumps(json_update),
        content_type='application/json')
    assert 200 == put.status_code, 'Failed to update asset'
    rv = client.get(
        base_ddo_url + '/%s' % post['id'],
        content_type='application/json')
    fetched_ddo = json.loads(rv.data.decode('utf-8'))
    assert json_update['service'][2]['attributes']['curation']['numVotes'] == \
        fetched_ddo['service'][0]['attributes']['curation']['numVotes']

    put = client.put(
        base_ddo_url + '/%s' % post['id'],
        data=json.dumps(fetched_ddo),
        content_type='application/json')
    assert 200 == put.status_code, 'Failed to update asset without changes.'

    client.delete(
        base_ddo_url + '/%s' % post['id'])


def test_query_metadata(client, base_ddo_url, test_assets):

    assert len(run_request_get_data(
        client.post, base_ddo_url + '/query', {"query": {}})['results']) == 2

    assert len(run_request_get_data(
        client.post, base_ddo_url + '/query', {"query": {'text': "UK"}})['results']) == 1

    assert len(run_request_get_data(
        client.post, base_ddo_url + '/query', {"query": {'text': "weather"}})['results']) == 1
    assert len(run_request_get_data(
        client.post, base_ddo_url + '/query', {"query": {'text': ["UK"]}})['results']) == 1
    assert len(run_request_get_data(
        client.post, base_ddo_url + '/query', {"query": {'text': "uK"}})['results']) == 1
    assert len(run_request_get_data(
        client.post, base_ddo_url + '/query', {"query": {'text': ["UK", "temperature"]}})['results']) == 1
    assert len(run_request_get_data(
        client.post, base_ddo_url + '/query', {"query": {'text': ["ocean protocol", "Vision", "paper"]}})['results']) == 1
    assert len(run_request_get_data(
        client.post, base_ddo_url + '/query', {"query": {'text': ["UK", "oceAN"]}})['results']) == 2

    assert len(
        run_request_get_data(client.post, base_ddo_url + '/query',
                             {"query": {"price": ["14", "16"]}}
                             )['results']
    ) == 1
    assert len(
        run_request_get_data(client.get, base_ddo_url + '/query?text=Office'
                             )['results']
    ) == 1
    assert len(
        run_request_get_data(client.get,
                             base_ddo_url + '/query?text=112233445566778899')['results']
    ) == 1

    try:
        num_assets = len(test_assets) + 2
        for a in test_assets:
            client.post(base_ddo_url,
                        data=json.dumps(a),
                        content_type='application/json')

        response = run_request_get_data(
            client.get, base_ddo_url + '/query?text=white&page=1&offset=5')
        assert response['page'] == 1
        assert response['total_pages'] == int(
            num_assets / 5) + int(num_assets % 5 > 0)
        assert response['total_results'] == num_assets
        assert len(response['results']) == 5

        response = run_request_get_data(
            client.get, base_ddo_url + '/query?text=white&page=3&offset=5')
        assert response['page'] == 3
        assert response['total_pages'] == int(
            num_assets / 5) + int(num_assets % 5 > 0)
        assert response['total_results'] == num_assets
        assert len(response['results']) == num_assets - \
            (5 * (response['total_pages'] - 1))

        response = run_request_get_data(
            client.get, base_ddo_url + '/query?text=white&page=4&offset=5')
        assert response['page'] == 4
        assert response['total_pages'] == int(
            num_assets / 5) + int(num_assets % 5 > 0)
        assert response['total_results'] == num_assets
        assert len(response['results']) == 0

    finally:
        for a in test_assets:
            client.delete(BaseURLs.BASE_AQUARIUS_URL +
                          '/assets/ddo/%s' % a['id'])


def test_delete_all(client_with_no_data, base_ddo_url):
    run_request(client_with_no_data.post, base_ddo_url, data=json_dict)
    run_request(client_with_no_data.post, base_ddo_url, data=json_update)
    assert len(run_request_get_data(client_with_no_data.get,
                                    BaseURLs.BASE_AQUARIUS_URL + '/assets')['ids']) == 2
    client_with_no_data.delete(base_ddo_url)
    assert len(run_request_get_data(client_with_no_data.get,
                                    BaseURLs.BASE_AQUARIUS_URL + '/assets')['ids']) == 0


def test_is_listed(client, base_ddo_url):
    assert len(run_request_get_data(
        client.get, BaseURLs.BASE_AQUARIUS_URL + '/assets')['ids']) == 2

    run_request(client.put, base_ddo_url + '/%s' %
                json_dict['id'], data=json_dict2)
    assert len(run_request_get_data(
        client.get, BaseURLs.BASE_AQUARIUS_URL + '/assets')['ids']) == 1
    assert len(run_request_get_data(client.post, base_ddo_url + '/query',
                                    data={"query": {"price": ["14", "16"]}})['results']) == 1


def test_validate(client_with_no_data, base_ddo_url):
    post = run_request(client_with_no_data.post,
                       base_ddo_url + '/validate', data={})
    assert post.status_code == 200
    assert post.data == b'[{"message":"\'main\' is a required property","path":""}]\n'
    post = run_request(client_with_no_data.post,
                       base_ddo_url + '/validate', data=json_valid)
    assert post.data == b'true\n'


def test_date_format_validator():
    date = '2016-02-08T16:02:20Z'
    assert validate_date_format(date) == (None, None)


def test_invalid_date():
    date = 'XXXX'
    assert validate_date_format(date) == (
        "Incorrect data format, should be '%Y-%m-%dT%H:%M:%SZ'", 400)


def test_algorithm_ddo(client, base_ddo_url):
    _algorithm_ddo_sample = copy.deepcopy(algorithm_ddo_sample)
    metadata = _algorithm_ddo_sample['service'][0]['attributes']
    if not plecos.is_valid_dict_local(metadata):
        print(
            f'algorithm ddo is not valid: {plecos.list_errors_dict_local(metadata)}')
        raise AssertionError('algorithm ddo failed to validate.')

    metadata['main']['files'][0].pop('url')
    post = client.post(base_ddo_url,
                       data=json.dumps(_algorithm_ddo_sample),
                       content_type='application/json')
    assert post.status_code in (200, 201)


# TODO

def test_owner_update(client_with_no_data, base_ddo_url):
    client = client_with_no_data
    acct1 = Account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530')
    acct2 = Account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1531')
    json_before['publicKey'][0]['owner'] = acct1.address
    post = run_request_get_data(client.post, base_ddo_url, data=json_before)
    # get the ddo
    rv = client.get(
        base_ddo_url + '/%s' % post['id'],
        content_type='application/json')
    fetched_ddo = json.loads(rv.data.decode('utf-8'))
    data = dict()
    data['newOwner'] = acct2.address
    data['updated'] = fetched_ddo['updated']
    # create signtaure
    msghash = encode_defunct(text=data['updated'])
    fullsignature = acct1.sign_message(msghash)
    data['signature'] = fullsignature.signature.hex()
    # post
    put = client.put(
        base_ddo_url + '/owner/update/%s' % post['id'],
        data=json.dumps(data),
        content_type='application/json')
    assert 200 == put.status_code, 'Failed to update ownership asset'
    rv = client.get(
        base_ddo_url + '/%s' % post['id'],
        content_type='application/json')
    fetched_ddo = json.loads(rv.data.decode('utf-8'))
    assert acct2.address == fetched_ddo['publicKey'][0]['owner'], 'Owner was not updated'


def test_ratings_update(client_with_no_data, base_ddo_url):
    client = client_with_no_data
    acct1 = Account.from_key(
        0xb25c7db31feed9122727bf0939dc769a96564b2de4c4726d035b36ecf1e5b364)
    print(f'account address: {acct1.address}')
    post = run_request_get_data(client.post, base_ddo_url, data=json_before)

    # get the ddo
    rv = client.get(
        base_ddo_url + '/%s' % post['id'],
        content_type='application/json')
    fetched_ddo = json.loads(rv.data.decode('utf-8'))

    data = dict()
    data['updated'] = fetched_ddo['updated']
    rating = 2.3
    numVotes = 26
    data['rating'] = rating
    data['numVotes'] = numVotes

    # create signtaure
    msghash = encode_defunct(text=data['updated'])
    fullsignature = acct1.sign_message(msghash)
    data['signature'] = fullsignature.signature.hex()
    # post
    put = client.put(
        base_ddo_url + '/ratings/update/%s' % post['id'],
        data=json.dumps(data),
        content_type='application/json')
    assert 200 == put.status_code, 'Failed to update ratings'
    rv = client.get(
        base_ddo_url + '/%s' % post['id'],
        content_type='application/json')
    fetched_ddo = json.loads(rv.data.decode('utf-8'))
    assert rating == fetched_ddo['service'][0]['attributes']['curation']['rating'], 'Rating was not updated'
    assert numVotes == fetched_ddo['service'][0]['attributes']['curation']['numVotes'], 'NumVotes was not updated'


def test_metadata_update(client_with_no_data, base_ddo_url):
    client = client_with_no_data
    acct1 = Account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530')
    json_before['publicKey'][0]['owner'] = acct1.address
    post = run_request_get_data(client.post, base_ddo_url, data=json_before)

    # get the ddo
    rv = client.get(
        base_ddo_url + '/%s' % post['id'],
        content_type='application/json')
    fetched_ddo = json.loads(rv.data.decode('utf-8'))

    data = dict()
    data['title'] = 'New title'
    data['description'] = 'New description'
    data['updated'] = fetched_ddo['updated']
    links = []
    alink = dict()
    alink['url'] = 'http://example.net'
    alink['name'] = 'Link name'
    alink['type'] = 'sample'
    links.append(alink)
    data['links'] = links

    prices = []
    onePrice = dict()
    onePrice['serviceIndex'] = 0
    onePrice['price'] = '134'
    prices.append(onePrice)
    secondPrice = dict()
    secondPrice['serviceIndex'] = 1
    secondPrice['price'] = '144'
    prices.append(secondPrice)
    data['servicePrices'] = prices
    # create signature
    msghash = encode_defunct(text=data['updated'])
    fullsignature = acct1.sign_message(msghash)
    data['signature'] = fullsignature.signature.hex()
    # post
    put = client.put(
        base_ddo_url + '/metadata/update/%s' % post['id'],
        data=json.dumps(data),
        content_type='application/json')
    assert 200 == put.status_code, 'Failed to update ownership asset'
    rv = client.get(
        base_ddo_url + '/%s' % post['id'],
        content_type='application/json')
    fetched_ddo = json.loads(rv.data.decode('utf-8'))
    assert data['title'] == fetched_ddo['service'][0]['attributes']['main']['name']
    assert data['description'] == fetched_ddo['service'][0]['attributes']['additionalInformation']['description']
    assert data['links'] == fetched_ddo['service'][0]['attributes']['additionalInformation']['links']
    assert '134' == fetched_ddo['service'][0]['attributes']['main']['price']


def test_publish_with_access_list(client_with_no_data, base_ddo_url):
    client = client_with_no_data

    acct1 = Account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530')
    acct2 = Account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1531')
    accessList = [acct1.address, acct2.address]
    json_before['accesssWhiteList'] = accessList
    post = run_request_get_data(client.post, base_ddo_url, data=json_before)

    # get the ddo
    rv = client.get(
        base_ddo_url + '/%s' % post['id'],
        content_type='application/json')
    fetched_ddo = json.loads(rv.data.decode('utf-8'))
    assert accessList == fetched_ddo['accesssWhiteList'], 'accesssWhiteList was not added'


def test_add_access_list(client_with_no_data, base_ddo_url):
    client = client_with_no_data
    acct1 = Account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530')
    json_before['publicKey'][0]['owner'] = acct1.address
    post = run_request_get_data(client.post, base_ddo_url, data=json_before)

    # get the ddo
    rv = client.get(
        base_ddo_url + '/%s' % post['id'],
        content_type='application/json')
    fetched_ddo = json.loads(rv.data.decode('utf-8'))

    data = dict()
    acct2 = Account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1531')
    data['address'] = acct2.address
    data['updated'] = fetched_ddo['updated']
    # create signtaure
    msghash = encode_defunct(text=data['updated'])
    fullsignature = acct1.sign_message(msghash)

    data['signature'] = fullsignature.signature.hex()
    # post
    put = client.post(
        base_ddo_url + '/accesssWhiteList/%s' % post['id'],
        data=json.dumps(data),
        content_type='application/json')
    assert 200 == put.status_code, 'Failed to add address to accessWhiteList'
    rv = client.get(
        base_ddo_url + '/%s' % post['id'],
        content_type='application/json')
    fetched_ddo = json.loads(rv.data.decode('utf-8'))
    print(f'AccessList:%s' % fetched_ddo['accesssWhiteList'])
    assert fetched_ddo['accesssWhiteList'].count(
        acct2.address) > 0, 'Address was not added'


def test_delete_from_access_list(client_with_no_data, base_ddo_url):
    client = client_with_no_data
    acct1 = Account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530')
    json_before['publicKey'][0]['owner'] = acct1.address
    acct2 = Account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1531')
    accessList = [acct2.address]
    json_before['accesssWhiteList'] = accessList
    post = run_request_get_data(client.post, base_ddo_url, data=json_before)

    # get the ddo
    rv = client.get(
        base_ddo_url + '/%s' % post['id'],
        content_type='application/json')
    fetched_ddo = json.loads(rv.data.decode('utf-8'))

    data = dict()
    data['address'] = acct2.address
    data['updated'] = fetched_ddo['updated']
    # create signtaure
    msghash = encode_defunct(text=data['updated'])
    fullsignature = acct1.sign_message(msghash)

    data['signature'] = fullsignature.signature.hex()
    # post
    put = client.delete(
        base_ddo_url + '/accesssWhiteList/%s' % post['id'],
        data=json.dumps(data),
        content_type='application/json')
    assert 200 == put.status_code, 'Failed to delete address from accessWhiteList'
    rv = client.get(
        base_ddo_url + '/%s' % post['id'],
        content_type='application/json')
    fetched_ddo = json.loads(rv.data.decode('utf-8'))
    assert fetched_ddo['accesssWhiteList'].count(
        acct2.address) < 1, 'Address was not removed'


def test_publish_with_free_list(client_with_no_data, base_ddo_url):
    client = client_with_no_data

    acct1 = Account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530')
    acct2 = Account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1531')
    accessList = [acct1.address, acct2.address]
    json_before['freeWhiteList'] = accessList
    post = run_request_get_data(client.post, base_ddo_url, data=json_before)

    # get the ddo
    rv = client.get(
        base_ddo_url + '/%s' % post['id'],
        content_type='application/json')
    fetched_ddo = json.loads(rv.data.decode('utf-8'))
    assert accessList == fetched_ddo['freeWhiteList'], 'freeWhiteList was not added'


def test_add_free_list(client_with_no_data, base_ddo_url):
    client = client_with_no_data
    acct1 = Account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530')
    json_before['publicKey'][0]['owner'] = acct1.address
    post = run_request_get_data(client.post, base_ddo_url, data=json_before)

    # get the ddo
    rv = client.get(
        base_ddo_url + '/%s' % post['id'],
        content_type='application/json')
    fetched_ddo = json.loads(rv.data.decode('utf-8'))

    data = dict()
    acct2 = Account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1531')
    data['address'] = acct2.address
    data['updated'] = fetched_ddo['updated']
    # create signtaure
    msghash = encode_defunct(text=data['updated'])
    fullsignature = acct1.sign_message(msghash)

    data['signature'] = fullsignature.signature.hex()
    # post
    put = client.post(
        base_ddo_url + '/freeWhiteList/%s' % post['id'],
        data=json.dumps(data),
        content_type='application/json')
    assert 200 == put.status_code, 'Failed to add address to freeWhiteList'
    rv = client.get(
        base_ddo_url + '/%s' % post['id'],
        content_type='application/json')
    fetched_ddo = json.loads(rv.data.decode('utf-8'))
    print(f'freeList:%s' % fetched_ddo['freeWhiteList'])
    assert fetched_ddo['freeWhiteList'].count(
        acct2.address) > 0, 'Address was not added'


def test_delete_from_free_list(client_with_no_data, base_ddo_url):
    client = client_with_no_data
    acct1 = Account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530')
    json_before['publicKey'][0]['owner'] = acct1.address
    acct2 = Account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1531')
    accessList = [acct2.address]
    json_before['freeWhiteList'] = accessList
    post = run_request_get_data(client.post, base_ddo_url, data=json_before)

    # get the ddo
    rv = client.get(
        base_ddo_url + '/%s' % post['id'],
        content_type='application/json')
    fetched_ddo = json.loads(rv.data.decode('utf-8'))

    data = dict()
    data['address'] = acct2.address
    data['updated'] = fetched_ddo['updated']
    # create signtaure
    msghash = encode_defunct(text=data['updated'])
    fullsignature = acct1.sign_message(msghash)

    data['signature'] = fullsignature.signature.hex()
    # post
    put = client.delete(
        base_ddo_url + '/freeWhiteList/%s' % post['id'],
        data=json.dumps(data),
        content_type='application/json')
    assert 200 == put.status_code, 'Failed to delete address from freeWhiteList'
    rv = client.get(
        base_ddo_url + '/%s' % post['id'],
        content_type='application/json')
    fetched_ddo = json.loads(rv.data.decode('utf-8'))
    assert fetched_ddo['freeWhiteList'].count(
        acct2.address) < 1, 'Address was not removed'
