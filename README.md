# pypeloton
Peloton API Client

## Installation

### Use pip

`pip install pypeloton`

### Build locally

```
$ git clone https://github.com/raman325/pypeloton.git
$ pip install -I pypeloton
```

## Usage

There are synchronous (`Peloton`) and asynchronous (`PelotonAsync`) classes available with the same methods available. For the purpose of demonstration we will talk about the synchronous `Peloton` class.

```
from pypeloton import Peloton

client = Peloton("my_username_or_email", "my_password")
user_id = client.get_user_id("raman325")
print(client.get_user_achievements(user_id))
print(client.get_user_workouts(user_id))
```

Most functions will return the full payload received, so it is up to you to figure out how to get the data you need from a given method. As of now you will have to look at the source to see what functions are available, better documentation to come later.

## Acknowledgements
- @geudrik made some helpful [API docs](https://github.com/geudrik/peloton-client-library/blob/master/API_DOCS.md)
- @

