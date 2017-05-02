## REST API Specification for Peers

### Collection: Peers

**URI:** /peers

Return a list of Wok peers in the same network.
(It uses openSLP for discovering)

**Methods:**

* **GET**: Retrieve a list peers URLs.

#### Examples
GET /peers
[
 https://wok-peer0:8001,
 https://wok-peer1:8001,
 https://wok-peer2:8001,
]
