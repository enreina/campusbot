# -*- coding: utf-8 -*-
SELECT_TASK_INSTRUCTION = '''You can select a task by tapping on the task number. 

In *Enrich* task: you would be presented with a picture and asked to add detailed information about it.
In *Validate*: you would be asked to assess the already available information.

You can also 
- /refresh the task list or 
- /create a new *{canonicalName}*'''
NO_TASK_INSTANCES_AVAILABLE = '''There is no task for *{canonicalName}* right now 🙁. You can:

- try other commands or
- /create a new *{canonicalName}*'''