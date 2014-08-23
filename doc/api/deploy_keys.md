## Deploy Keys

### List deploy keys

Get a list of a project's deploy keys.

```
GET /projects/:id/keys
```

Parameters:

+ `id` (required) - The ID of the project

```json
[
  {
    "id": 1,
    "title" : "Public key"
    "key": "ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAIEAiPWx6WM4lhHNedGfBpPJNPpZ7yKu+dnn1SJejgt4
      596k6YjzGGphH2TUxwKzxcKDKKezwkpfnxPkSMkuEspGRt/aZZ9wa++Oi7Qkr8prgHc4
      soW6NUlfDzpvZK2H5E7eQaSeP3SAwGmQKUFHCddNaP0L+hM7zhFNzjFvpaMgJw0=",
  },
  {
    "id": 3,
    "title" : "Another Public key"
    "key": "ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAIEAiPWx6WM4lhHNedGfBpPJNPpZ7yKu+dnn1SJejgt4
      596k6YjzGGphH2TUxwKzxcKDKKezwkpfnxPkSMkuEspGRt/aZZ9wa++Oi7Qkr8prgHc4
      soW6NUlfDzpvZK2H5E7eQaSeP3SAwGmQKUFHCddNaP0L+hM7zhFNzjFvpaMgJw0="
  }
]
```


### Single deploy key

Get a single key.

```
GET /projects/:id/keys/:key_id
```

Parameters:

+ `id` (required) - The ID of the project
+ `key_id` (required) - The ID of the deploy key

```json
{
  "id": 1,
  "title" : "Public key"
  "key": "ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAIEAiPWx6WM4lhHNedGfBpPJNPpZ7yKu+dnn1SJejgt4
      596k6YjzGGphH2TUxwKzxcKDKKezwkpfnxPkSMkuEspGRt/aZZ9wa++Oi7Qkr8prgHc4
      soW6NUlfDzpvZK2H5E7eQaSeP3SAwGmQKUFHCddNaP0L+hM7zhFNzjFvpaMgJw0="
}
```


### Add deploy key

Creates a new deploy key for a project.
If deploy key already exists in another project - it will be joined to project but only if original one was is accessible by same user

```
POST /projects/:id/keys
```

Parameters:

+ `id` (required) - The ID of the project
+ `title` (required) - New deploy key's title
+ `key` (required) - New deploy key


### Delete deploy key

Delete a deploy key from a project

```
DELETE /projects/:id/keys/:key_id
```

Parameters:

+ `id` (required) - The ID of the project
+ `key_id` (required) - The ID of the deploy key

