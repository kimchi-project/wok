## REST API Specification for Logs

### Collection: Logs

**URI:** /logs

**Methods:**

* **GET**: Retrieve a list of entries from User Request Log
    * Parameters:
        * app: Filter entries by application that received the request.
               Use "wok" or any plugin installed, like "kimchi".
        * req: Filter entries by type of request: "DELETE", "POST", "PUT".
               "GET" requests are not logged.
        * status: Filter entries by HTTP response status: 200, 404, 500, etc.
        * user: Filter entries by user that performed the request.
        * ip: Filter entries by user IP address, i.e. 127.0.0.1
        * date: Filter entries by date of record in the format "YYYY-MM-DD"
        * download: Generate text file for download of search results.

#### Examples
GET /logs?download=True
{'records': [{entry-record1}, {entry-record2}, {entry-record3}, ...],
'uri': "/data/logs/tmpbnOzP2.txt"}

GET /logs?user=dev&app=ginger
{'records': [{entry-record1}, {entry-record2}, {entry-record3}, ...],
'uri': None}

