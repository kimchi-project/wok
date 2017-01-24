## REST API Specification for Config

### Resource: Config

**URI:** /config

Contains information about the application environment and configuration.

**Methods:**

* **GET**: Retrieve configuration information
    * proxy_port: SSL port to list on
    * websockets_port: Port for websocket proxy to listen on
    * auth: Authentication method used to log in to Wok
    * version: Wok version
* **POST**: *See Task Actions*

**Actions (POST):**

* reload: reloads WoK configuration. This process will drop all existing WoK connections, reloading WoK and all its enabled plug-ins.

#### Examples
GET /config
{
 proxy_port: 8001,
 websockets_port: 64667,
 version: 2.0
}
