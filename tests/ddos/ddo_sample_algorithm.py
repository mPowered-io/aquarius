#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
algorithm_ddo_sample = {
    "@context": "https://w3id.org/did/v1",
    "authentication": [
        {
            "type": "RsaSignatureAuthentication2018",
            "publicKey": "did:op:0ebed8226ada17fde24b6bf2b95d27f8f05fcce09139ff5cec31f6d81a7cd2ea",
        }
    ],
    "created": "2019-02-08T08:13:49Z",
    "id": "did:op:0bc278fee025464f8012b811d1bce8e22094d0984e4e49139df5d5ff7a028bdf",
    "dataToken": "0xC7EC1970B09224B317c52d92f37F5e1E4fF6B687",
    "proof": {
        "created": "2019-02-08T08:13:41Z",
        "creator": "0x37BB53e3d293494DE59fBe1FF78500423dcFd43B",
        "signatureValue": "did:op:0bc278fee025464f8012b811d1bce8e22094d0984e4e49139df5d5ff7a028bdf",
        "type": "DDOIntegritySignature",
        "checksum": {
            "0": "0x52b5c93b82dd9e7ecc3d9fdf4755f7f69a54484941897dc517b4adfe3bbc3377",
            "1": "0x999999952b5c93b82dd9e7ecc3d9fdf4755f7f69a54484941897dc517b4adfe3",
        },
    },
    "publicKey": [
        {
            "id": "did:op:b6e2eb5eff1a093ced9826315d5a4ef6c5b5c8bd3c49890ee284231d7e1d0aaa#keys-1",
            "type": "RsaVerificationKey2018",
            "owner": "did:op:6027c1e7cbae06a91fce0557ee53195284825f56a7100be0c53cbf4391aa26cc",
            "publicKeyPem": "-----BEGIN PUBLIC KEY...END PUBLIC KEY-----\r\n",
        },
        {
            "id": "did:op:b6e2eb5eff1a093ced9826315d5a4ef6c5b5c8bd3c49890ee284231d7e1d0aaa#keys-2",
            "type": "Ed25519VerificationKey2018",
            "owner": "did:op:4c27a254e607cdf91a1206480e7eb8c74856102316c1a462277d4f21c02373b6",
            "publicKeyBase58": "H3C2AVvLMv6gmMNam3uVAjZpfkcJCwDwnZn6z3wXmqPV",
        },
        {
            "id": "did:op:b6e2eb5eff1a093ced9826315d5a4ef6c5b5c8bd3c49890ee284231d7e1d0aaa#keys-3",
            "type": "RsaPublicKeyExchangeKey2018",
            "owner": "did:op:5f6b885202ffb9643874be529302eb00d55e226959f1fbacaeda592c5b5c9484",
            "publicKeyPem": "-----BEGIN PUBLIC KEY...END PUBLIC KEY-----\r\n",
        },
    ],
    "verifiableCredential": [
        {
            "@context": [
                "https://www.w3.org/2018/credentials/v1",
                "https://www.w3.org/2018/credentials/examples/v1",
            ],
            "id": "1872",
            "type": ["read", "update", "deactivate"],
            "issuer": "0x610D9314EDF2ced7681BA1633C33fdb8cF365a12",
            "issuanceDate": "2019-01-01T19:73:24Z",
            "credentialSubject": {"id": "0x89328493849328493284932"},
            "proof": {
                "type": "RsaSignature2018",
                "created": "2019-01-01T19:73:24Z",
                "proofPurpose": "assertionMethod",
                "signatureValue": "ABCJSDAO23...1tzjn4w==",
            },
        }
    ],
    "service": [
        {
            "index": 0,
            "serviceEndpoint": "http://localhost:5000/api/v1/aquarius/assets/ddo/{did}",
            "type": "metadata",
            "attributes": {
                "main": {
                    "author": "John Doe",
                    "dateCreated": "2019-02-08T08:13:49Z",
                    "license": "CC-BY",
                    "name": "My super algorithm",
                    "type": "algorithm",
                    "algorithm": {
                        "language": "scala",
                        "format": "docker-image",
                        "version": "0.1",
                        "container": {
                            "entrypoint": "node $ALGO",
                            "image": "node",
                            "tag": "10",
                        },
                    },
                    "files": [
                        {
                            "name": "build_model",
                            "url": "https://raw.githubusercontent.com/oceanprotocol/test-algorithm/master/javascript/algo.js",
                            "index": 0,
                            "checksum": "efb2c764274b745f5fc37f97c6b0e761",
                            "contentLength": "4535431",
                            "contentType": "text/plain",
                            "encoding": "UTF-8",
                            "compression": "zip",
                        }
                    ],
                },
                "additionalInformation": {
                    "description": "Workflow to aggregate weather information",
                    "tags": ["weather", "uk", "2011", "workflow", "aggregation"],
                    "copyrightHolder": "John Doe",
                },
            },
        }
    ],
}
