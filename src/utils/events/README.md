## [filesys_subscriber.py](/src/events/filesys_subscriber.py)

Subscribes to file upload progress events.

`filesys_save_error` and `filesys_save_success` events are published to the event bus when a file upload fails or succeeds, respectively. This subscriber listens to those events and updates the file upload status in the database.