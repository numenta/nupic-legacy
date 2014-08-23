## List users

Get a list of users.
This function takes pagination parameters `page` and `per_page` to restrict the list of users.

```
GET /users
```

```json
[
  {
    "id": 1,
    "username": "john_smith",
    "email": "john@example.com",
    "name": "John Smith",
    "state": "active",
    "created_at": "2012-05-23T08:00:58Z",
    "bio": null,
    "skype": "",
    "linkedin": "",
    "twitter": "",
    "extern_uid": "john.smith",
    "provider": "provider_name",
    "theme_id": 1
    "color_scheme_id": 2
  },
  {
    "id": 2,
    "username": "jack_smith",
    "email": "jack@example.com",
    "name": "Jack Smith",
    "state": "blocked",
    "created_at": "2012-05-23T08:01:01Z",
    "bio": null,
    "skype": "",
    "linkedin": "",
    "twitter": "",
    "extern_uid": "jack.smith",
    "provider": "provider_name",
    "theme_id": 1
    "color_scheme_id": 3
  }
]
```


## Single user

Get a single user.

```
GET /users/:id
```

Parameters:

+ `id` (required) - The ID of a user

```json
{
  "id": 1,
  "username": "john_smith",
  "email": "john@example.com",
  "name": "John Smith",
  "state": "active",
  "created_at": "2012-05-23T08:00:58Z",
  "bio": null,
  "skype": "",
  "linkedin": "",
  "twitter": "",
  "extern_uid": "john.smith",
  "provider": "provider_name",
  "theme_id": 1
  "color_scheme_id": 2
}
```


## User creation

Creates a new user. Note only administrators can create new users.

```
POST /users
```

Parameters:

+ `email` (required)          - Email
+ `password` (required)       - Password
+ `username` (required)       - Username
+ `name` (required)           - Name
+ `skype` (optional)          - Skype ID
+ `linkedin` (optional)       - Linkedin
+ `twitter` (optional)        - Twitter account
+ `projects_limit` (optional) - Number of projects user can create
+ `extern_uid` (optional)     - External UID
+ `provider` (optional)       - External provider name
+ `bio` (optional)            - User's bio


## User modification

Modifies an existing user. Only administrators can change attributes of a user.

```
PUT /users/:id
```

Parameters:

+ `email`                             - Email
+ `username`                          - Username
+ `name`                              - Name
+ `password`                          - Password
+ `skype`                             - Skype ID
+ `linkedin`                          - Linkedin
+ `twitter`                           - Twitter account
+ `projects_limit`                    - Limit projects each user can create
+ `extern_uid`                        - External UID
+ `provider`                          - External provider name
+ `bio`                               - User's bio

Note, at the moment this method does only return a 404 error, even in cases where a 409 (Conflict) would
be more appropriate, e.g. when renaming the email address to some exsisting one.


## User deletion

Deletes a user. Available only for administrators. This is an idempotent function, calling this function
for a non-existent user id still returns a status code `200 Ok`. The JSON response differs if the user
was actually deleted or not. In the former the user is returned and in the latter not.

```
DELETE /users/:id
```

Parameters:

+ `id` (required) - The ID of the user


## Current user

Gets currently authenticated user.

```
GET /user
```

```json
{
  "id": 1,
  "username": "john_smith",
  "email": "john@example.com",
  "name": "John Smith",
  "private_token": "dd34asd13as",
  "state": "active",
  "created_at": "2012-05-23T08:00:58Z",
  "bio": null,
  "skype": "",
  "linkedin": "",
  "twitter": "",
  "theme_id": 1
  "color_scheme_id": 2
  "is_admin": false,
  "can_create_group" : true,
  "can_create_team" : true,
  "can_create_project" : true
}
```


## List SSH keys

Get a list of currently authenticated user's SSH keys.

```
GET /user/keys
```

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

Parameters:

+ **none**


## Single SSH key

Get a single key.

```
GET /user/keys/:id
```

Parameters:

+ `id` (required) - The ID of an SSH key

```json
{
  "id": 1,
  "title" : "Public key"
  "key": "ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAIEAiPWx6WM4lhHNedGfBpPJNPpZ7yKu+dnn1SJejgt4
      596k6YjzGGphH2TUxwKzxcKDKKezwkpfnxPkSMkuEspGRt/aZZ9wa++Oi7Qkr8prgHc4
      soW6NUlfDzpvZK2H5E7eQaSeP3SAwGmQKUFHCddNaP0L+hM7zhFNzjFvpaMgJw0="
}
```


## Add SSH key

Creates a new key owned by the currently authenticated user.

```
POST /user/keys
```

Parameters:

+ `title` (required) - new SSH Key's title
+ `key` (required) - new SSH key


## Add SSH key for user

Create new key owned by specified user. Available only for admin

```
POST /users/:id/keys
```

Parameters:

+ `id` (required) - id of specified user
+ `title` (required) - new SSH Key's title
+ `key` (required) - new SSH key

Will return created key with status `201 Created` on success, or `404 Not
found` on fail.

## Delete SSH key

Deletes key owned by currently authenticated user. This is an idempotent function and calling it on a key that is already
deleted or not available results in `200 Ok`.

```
DELETE /user/keys/:id
```

Parameters:

+ `id` (required) - SSH key ID

