## REST API Specification for Notifications

### Collection: Notifications

**URI:** /notifications

**Methods:**

* **GET**: Retrieve a summarized list of current Notifications

#### Examples
GET /notifications
[{Notification1}, {Notification2}, ...]

### Resource: Notification

**URI:** /notifications/*:id*

A notification represents an asynchronous warning message sent to the web UI.

**Methods:**

* **GET**: Retrieve the full description of the Notification
    * code: message ID
    * message: message text already translated
    * timestamp: first time notification was emitted

* **DELETE**: Delete the Notification

#### Examples
GET /notifications/KCHLIBVIRT0001W
{
 code: "KCHLIBVIRT0001W",
 message: "KCHLIBVIRT0001W: Lack of storage space in guest vm-1",
 timestamp: first time notification was emitted
}
