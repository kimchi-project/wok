## REST API Specification for Tasks

### Collection: Tasks

**URI:** /tasks

**Methods:**

* **GET**: Retrieve a summarized list of current Tasks

#### Examples
GET /tasks
[{task-resource1}, {task-resource2}, {task-resource3}, ...]

### Resource: Task

**URI:** /tasks/*:id*

A task represents an asynchronous operation that is being performed by the
server.

**Methods:**

* **GET**: Retrieve the full description of the Task
    * id: The Task ID is used to identify this Task in the API.
    * status: The current status of the Task
        * running: The task is running
        * finished: The task has finished successfully
        * failed: The task failed
    * message: Human-readable details about the Task status
    * target_uri: Resource URI related to the Task
* **POST**: *See Task Actions*

**Actions (POST):**

*No actions defined*

#### Examples
GET /tasks/1
{
 id: 1,
 status: running,
 message: "Clonning guest",
 target_uri: "/plugins/kimchi/vms/my-vm/clone"
}
