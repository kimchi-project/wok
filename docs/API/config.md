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

### Collection: Plugins

**URI:** /config/plugins

**Methods:**

* **GET**: Retrieve a summarized list of all UI Plugins.

#### Examples
GET /plugins
[{'name': 'pluginA', 'enabled': True, "depends":['pluginB'], "is_dependency_of":[]},
 {'name': 'pluginB', 'enabled': False, "depends":[], "is_dependency_of":['pluginA']}]

### Resource: Plugins

**URI:** /config/plugins/*:name*

Represents the current state of a given WoK plug-in.

**Methods:**

* **GET**: Retrieve the state of the plug-in.
    * name: The name of the plug-in.
    * enabled: True if the plug-in is currently enabled in WoK, False otherwise.
    * depends: The plug-ins that are dependencies for this plug-in.
    * is_dependency_of: The plug-ins that rely on this plug-in to work properly.

* **POST**: *See Plugin Actions*

**Actions (POST):**

* enable: Enables the plug-in.
* disable: Disables the plug-in.

'enable' and 'disable' changes the plug-in configuration file attribute 'enable'
to either 'True' or 'False' respectively. It also enables or disables the plug-in
on the fly by adding/removing it from the mounted cherrypy tree. The plug-in
dependencies are taken into account and are enabled/disabled in the process
when applicable.
