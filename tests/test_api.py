#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0
import copy
import json
import logging

from plecos import plecos

from aquarius.app.util import validate_date_format
from aquarius.app.auth_util import get_signer_address
from aquarius.constants import BaseURLs
from aquarius.run import get_status, get_version
from tests.ddo_samples_invalid import json_dict_no_metadata, json_dict_no_valid_metadata
from tests.ddos.ddo_sample1 import json_dict
from tests.ddos.ddo_sample2 import json_dict2
from tests.ddos.ddo_sample_algorithm import algorithm_ddo_sample
from tests.ddos.ddo_sample_updates import json_before, json_update, json_valid
from eth_account.messages import encode_defunct
from eth_account import Account


ACC_1_ENTROPY = 'KEYSMASH FJAFJKLDSKF7JKFDJ 1530'
ACC_2_ENTROPY = 'KEYSMASH FJAFJKLDSKF7JKFDJ 1531'


def sign_message(account, message_str):
    msg_hash = encode_defunct(text=message_str)
    full_signature = account.sign_message(msg_hash)
    return full_signature.signature.hex()


def create_account(extra_entropy):
    return Account.create(extra_entropy=extra_entropy)


def get_new_accounts():
    return create_account(ACC_1_ENTROPY), create_account(ACC_2_ENTROPY)


def get_ddo(client, base_ddo_url, did):
    rv = client.get(
        base_ddo_url + f'/{did}',
        content_type='application/json'
    )
    fetched_ddo = json.loads(rv.data.decode('utf-8'))
    return fetched_ddo


def run_request_get_data(client_method, url, data=None):
    _response = run_request(client_method, url, data)
    print(f'response: {_response}')
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
    assert json_dict['service'][1]['type'] in rv['service'][0]['type']


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
    assert json_dict['service'][1]['type'] in rv['service'][0]['type']
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
    fetched_ddo = get_ddo(client, base_ddo_url, post['id'])
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
        client.post, base_ddo_url + '/query', {"query": {}})['results']) > 0

    assert len(run_request_get_data(
        client.post, base_ddo_url + '/query', {"query": {'text': ["UK"]}})['results']) > 0

    assert len(run_request_get_data(
        client.post, base_ddo_url + '/query', {"query": {'text': ["weather"]}})['results']) > 0
    assert len(run_request_get_data(
        client.post, base_ddo_url + '/query', {"query": {'text': ["uK"]}})['results']) > 0
    assert len(run_request_get_data(
        client.post, base_ddo_url + '/query', {"query": {'text': ["UK", "temperature"]}})['results']) > 0
    assert len(run_request_get_data(
        client.post, base_ddo_url + '/query', {"query": {'text': ["ocean protocol", "Vision", "paper"]}})['results']) > 0
    assert len(run_request_get_data(
        client.post, base_ddo_url + '/query', {"query": {'text': ["UK", "oceAN"]}})['results']) > 0

    assert len(
        run_request_get_data(client.post, base_ddo_url + '/query',
                             {"query": {"cost": ["1", "16"]}}
                             )['results']
    ) > 0
    assert len(
        run_request_get_data(client.get, base_ddo_url + '/query?text=Office'
                             )['results']
    ) > 0
    assert len(
        run_request_get_data(client.get,
                             base_ddo_url + '/query?text=112233445566778899')['results']
    ) > 0

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
                                    BaseURLs.BASE_AQUARIUS_URL + '/assets')['ids']) > 0
    client_with_no_data.delete(base_ddo_url)
    assert len(run_request_get_data(client_with_no_data.get,
                                    BaseURLs.BASE_AQUARIUS_URL + '/assets')['ids']) == 0


def test_validate(client_with_no_data, base_ddo_url):
    post = run_request(
        client_with_no_data.post,
        base_ddo_url + '/validate', data={}
    )
    assert post.status_code == 200
    assert post.data == b'[{"message":"\'main\' is a required property","path":""}]\n'
    post = run_request(
        client_with_no_data.post,
        base_ddo_url + '/validate',
        data=json_valid
    )
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
    post = client.post(
        base_ddo_url,
        data=json.dumps(_algorithm_ddo_sample),
        content_type='application/json'
    )
    assert post.status_code in (200, 201)


def test_owner_update(client_with_no_data, base_ddo_url):
    client = client_with_no_data
    acct_1, acct_2 = get_new_accounts()
    json_before['publicKey'][0]['owner'] = acct_1.address
    post = run_request_get_data(client.post, base_ddo_url, data=json_before)
    _id = post['id']

    # get the ddo
    fetched_ddo = get_ddo(client, base_ddo_url, post['id'])

    data = dict()
    data['newOwner'] = acct_2.address
    data['updated'] = fetched_ddo['updated']
    # create signtaure
    data['signature'] = sign_message(acct_1, data['updated'])

    # put
    put = client.put(
        base_ddo_url + f'/owner/update/{_id}',
        data=json.dumps(data),
        content_type='application/json'
    )
    assert 200 == put.status_code, 'Failed to update ownership asset'
    fetched_ddo = get_ddo(client, base_ddo_url, post['id'])
    assert acct_2.address == fetched_ddo['publicKey'][0]['owner'], 'Owner was not updated'


def test_ratings_update(client_with_no_data, base_ddo_url):
    client = client_with_no_data
    acct_1 = Account.from_key(
        private_key='0xb25c7db31feed9122727bf0939dc769a96564b2de4c4726d035b36ecf1e5b364'
    )
    print(f'account address: {acct_1.address}')
    post = run_request_get_data(client.post, base_ddo_url, data=json_before)
    _id = post['id']

    # get the ddo
    fetched_ddo = get_ddo(client, base_ddo_url, post['id'])

    data = dict()
    data['updated'] = fetched_ddo['updated']
    rating = 2.3
    num_votes = 26
    data['rating'] = rating
    data['numVotes'] = num_votes

    # create signtaure
    data['signature'] = sign_message(acct_1, data['updated'])

    # post
    put = client.put(
        base_ddo_url + f'/ratings/update/{_id}',
        data=json.dumps(data),
        content_type='application/json'
    )
    assert 200 == put.status_code, 'Failed to update ratings'

    fetched_ddo = get_ddo(client, base_ddo_url, post['id'])
    assert rating == fetched_ddo['service'][0]['attributes']['curation']['rating'], 'Rating was not updated'
    assert num_votes == fetched_ddo['service'][0]['attributes']['curation']['numVotes'], 'NumVotes was not updated'


def test_metadata_update(client_with_no_data, base_ddo_url):
    client = client_with_no_data
    acct_1 = create_account(ACC_1_ENTROPY)
    json_before['publicKey'][0]['owner'] = acct_1.address
    post = run_request_get_data(client.post, base_ddo_url, data=json_before)
    _id = post['id']

    # get the ddo
    fetched_ddo = get_ddo(client, base_ddo_url, post['id'])

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
    one_price = dict()
    one_price['serviceIndex'] = 0
    one_price['cost'] = '134'
    prices.append(one_price)
    second_price = dict()
    second_price['serviceIndex'] = 1
    second_price['cost'] = '144'
    prices.append(second_price)
    data['servicePrices'] = prices
    # create signature
    data['signature'] = sign_message(acct_1, data['updated'])

    # post
    put = client.put(
        base_ddo_url + f'/metadata/{_id}',
        data=json.dumps(data),
        content_type='application/json'
    )
    assert 200 == put.status_code, 'Failed to update ownership asset'

    fetched_ddo = get_ddo(client, base_ddo_url, post['id'])
    assert data['title'] == fetched_ddo['service'][0]['attributes']['main']['name']
    assert data['description'] == fetched_ddo['service'][0]['attributes']['additionalInformation']['description']
    assert data['links'] == fetched_ddo['service'][0]['attributes']['additionalInformation']['links']
    index = 0
    for service in fetched_ddo['service']:
        if service['type'] == 'access':
            access_service = fetched_ddo['service'][index]
        if service['type'] == 'compute':
            compute_service = fetched_ddo['service'][index]
        index = index+1
    assert '134' == access_service['attributes']['main']['cost']
    assert '144' == compute_service['attributes']['main']['cost']


def test_publish_with_access_list(client_with_no_data, base_ddo_url):
    client = client_with_no_data

    acct_1, acct_2 = get_new_accounts()
    access_list = [acct_1.address, acct_2.address]
    json_before['accesssWhiteList'] = access_list
    post = run_request_get_data(client.post, base_ddo_url, data=json_before)

    # get the ddo
    fetched_ddo = get_ddo(client, base_ddo_url, post['id'])
    assert access_list == fetched_ddo['accesssWhiteList'], 'accesssWhiteList was not added'


def test_add_access_list(client_with_no_data, base_ddo_url):
    client = client_with_no_data
    acct_1, acct_2 = get_new_accounts()

    json_before['publicKey'][0]['owner'] = acct_1.address
    post = run_request_get_data(client.post, base_ddo_url, data=json_before)
    _id = post['id']

    # get the ddo
    fetched_ddo = get_ddo(client, base_ddo_url, post['id'])

    data = dict()
    data['address'] = acct_2.address
    data['updated'] = fetched_ddo['updated']
    # create signtaure
    data['signature'] = sign_message(acct_1, data['updated'])

    # post
    put = client.post(
        base_ddo_url + f'/accesssWhiteList/{_id}',
        data=json.dumps(data),
        content_type='application/json'
    )
    assert 200 == put.status_code, 'Failed to add address to accessWhiteList'

    fetched_ddo = get_ddo(client, base_ddo_url, post['id'])
    print(f'AccessList: {fetched_ddo["accesssWhiteList"]}')
    assert fetched_ddo['accesssWhiteList'].count(
        acct_2.address) > 0, 'Address was not added'


def test_delete_from_access_list(client_with_no_data, base_ddo_url):
    client = client_with_no_data
    acct_1, acct_2 = get_new_accounts()

    json_before['publicKey'][0]['owner'] = acct_1.address
    access_list = [acct_2.address]
    json_before['accesssWhiteList'] = access_list
    post = run_request_get_data(client.post, base_ddo_url, data=json_before)
    _id = post['id']

    # get the ddo
    fetched_ddo = get_ddo(client, base_ddo_url, post['id'])

    data = dict()
    data['address'] = acct_2.address
    data['updated'] = fetched_ddo['updated']
    # create signtaure
    data['signature'] = sign_message(acct_1, data['updated'])

    # post
    put = client.delete(
        base_ddo_url + f'/accesssWhiteList/{_id}',
        data=json.dumps(data),
        content_type='application/json'
    )
    assert 200 == put.status_code, 'Failed to delete address from accessWhiteList'

    fetched_ddo = get_ddo(client, base_ddo_url, post['id'])
    assert fetched_ddo['accesssWhiteList'].count(
        acct_2.address) < 1, 'Address was not removed'


def test_computePrivacy_update(client_with_no_data, base_ddo_url):
    client = client_with_no_data

    acct_1, acct_2 = get_new_accounts()
    json_before['publicKey'][0]['owner'] = acct_1.address
    post = run_request_get_data(client.post, base_ddo_url, data=json_before)
    _id = post['id']

    # get the ddo
    fetched_ddo = get_ddo(client, base_ddo_url, post['id'])

    data = dict()
    data['updated'] = fetched_ddo['updated']
    data['allowRawAlgorithm'] = True
    data['allowNetworkAccess'] = False
    data['trustedAlgorithms'] = ['did:op:123', 'did:op:1234']
    data['serviceIndex'] = 1

    # create signtaure
    data['signature'] = sign_message(acct_1, data['updated'])

    # post
    put = client.put(
        base_ddo_url + f'/computePrivacy/update/{_id}',
        data=json.dumps(data),
        content_type='application/json'
    )
    assert 200 == put.status_code, 'Failed to update computePrivacy'

    fetched_ddo = get_ddo(client, base_ddo_url, post['id'])
    index = 0
    compute_service_index = -1
    for service in fetched_ddo['service']:
        if service['index'] == data['serviceIndex']:
            compute_service_index = index
        index = index + 1

    assert compute_service_index > - \
        1, f'Cannot find compute service {compute_service_index}'

    assert data['allowRawAlgorithm'] == fetched_ddo['service'][compute_service_index
                                                               ]['attributes']['main']['privacy']['allowRawAlgorithm'], 'allowRawAlgorithm was not updated'
    assert data['allowNetworkAccess'] == fetched_ddo['service'][compute_service_index
                                                                ]['attributes']['main']['privacy']['allowNetworkAccess'], 'allowNetworkAccess was not updated'
    assert data['trustedAlgorithms'] == fetched_ddo['service'][compute_service_index
                                                               ]['attributes']['main']['privacy']['trustedAlgorithms'], 'trustedAlgorithms was not updated'

def test_resolveByDtAddress(client_with_no_data, base_ddo_url):
    client = client_with_no_data

    acct_1, acct_2 = get_new_accounts()
    json_before['publicKey'][0]['owner'] = acct_1.address
    post = run_request_get_data(client.post, base_ddo_url, data=json_before)
    assert len(
        run_request_get_data(client.post, base_ddo_url + '/query',
                             {"query": {"dataToken": ["0xC7EC1970B09224B317c52d92f37F5e1E4fF6B687"]}}
                             )['results']
    ) > 0