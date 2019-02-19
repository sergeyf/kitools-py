# kitools


## Usage

Create a new Project with an existing Synapse Project and add two files:
```text
project = Project('/path/to/my/project')

Creating new Project...
Project Name (required): My New Project
Project Description (optional): My example project.

Remote Project: [C]reate or Use [E]xisting [c/e]: e 
Remote Project URI (required): syn:syn001

Checking Synapse connectivity...
Connected to Synapse.

Checking remote project...
Remote project exists and accessible.

Project successfully setup and ready to use.

project.data_pull('syn:syn0020', data_type='core')
project.data_pull('syn:syn0021', data_type='core', version='2')
```

Create a new Project, create a new Synapse Project and add two files:
```text
project = Project('/path/to/my/project')

Creating new Project...
Project Name (required): My New Project
Project Description (optional): My example project.

Remote Project: [C]reate or Use [E]xisting [c/e]: c
 
Data Providers:
  1. Synapse
Enter the number of the data provider to use (required): 1

Checking Synapse connectivity...
Connected to Synapse.

Creating remote project...
Remote project created.

Project successfully setup and ready to use.

project.data_pull('syn:syn0020', data_type='core')
project.data_pull('syn:syn0021', data_type='core', version='2')
```

Use data from an existing Project:
```python
project = Project('/path/to/my/project')
a = project.data_load('syn:syn001')
b = project.data_load('syn:syn002')
```

Pull all the data for an existing Project:
```python
project = Project('/path/to/my/project')
project.data_pull()
```

Save data to a local file:
```python
project = Project('/path/to/my/project')
my_data = {...some data...}
project.data_save('my-data.csv', my_data, data_type='core')
```

Push Data to the remote Project:
```python
project = Project('/path/to/my/project')
project.data_push('core/my-data.csv')
```

Push All Data to the remote Project:
```python
project = Project('/path/to/my/project')
project.data_push()
```

## Project Configuration File

Example File:
```json
{
  "title": "My Project",
  "description": "My Project Description",
  "project_uri": "syn:syn001",
  "files": [
    {
      "remote_uri": "syn:syn002",
      "local_path": "data/core/file1.csv",
      "version": "1.2"
    },
    {
      "remote_uri": "syn:syn003",
      "local_path": "data/core/study1",
      "version": null
    }
  ]
}
```