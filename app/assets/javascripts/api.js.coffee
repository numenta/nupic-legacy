@Api =
  users_path: "/api/:version/users.json"
  user_path: "/api/:version/users/:id.json"
  notes_path: "/api/:version/projects/:id/notes.json"

  # Get 20 (depends on api) recent notes 
  # and sort the ascending from oldest to newest
  notes: (project_id, callback) ->
    url = Api.buildUrl(Api.notes_path)
    url = url.replace(':id', project_id)
    
    $.ajax(
      url: url,
      data:
        private_token: gon.api_token
        gfm: true
        recent: true
      dataType: "json"
    ).done (notes) ->
      notes.sort (a, b) ->
        return a.id - b.id
      callback(notes)

  user: (user_id, callback) ->
    url = Api.buildUrl(Api.user_path)
    url = url.replace(':id', user_id)

    $.ajax(
      url: url
      data:
        private_token: gon.api_token
      dataType: "json"
    ).done (user) ->
      callback(user)

  # Return users list. Filtered by query
  # Only active users retrieved
  users: (query, callback) ->
    url = Api.buildUrl(Api.users_path)
    
    $.ajax(
      url: url
      data:
        private_token: gon.api_token
        search: query
        per_page: 20
        active: true
      dataType: "json"
    ).done (users) ->
      callback(users)

  buildUrl: (url) ->
    url = gon.relative_url_root + url if gon.relative_url_root.present?
    return url.replace(':version', gon.api_version)
