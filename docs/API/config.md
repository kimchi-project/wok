## REST API Specification for Config

### Resource: Config

**URI:** /config

Contains information about the application environment and configuration.

**Methods:**

* **GET**: Retrieve configuration information
    * ssl_port: SSL port to list on
    * websockets_port: Port for websocket proxy to listen on
    * version: Wok version
* **POST**: *See Task Actions*

**Actions (POST):**

*No actions defined*

#### Examples
GET /config
{
 ssl_port: 8001,
 websockets_port: 64667,
 version: 2.0
}
