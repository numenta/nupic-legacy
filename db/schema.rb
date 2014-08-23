# encoding: UTF-8
# This file is auto-generated from the current state of the database. Instead
# of editing this file, please use the migrations feature of Active Record to
# incrementally modify your database, and then regenerate this schema definition.
#
# Note that this schema.rb definition is the authoritative source for your
# database schema. If you need to create the application database on another
# system, you should be using db:schema:load, not running all the migrations
# from scratch. The latter is a flawed and unsustainable approach (the more migrations
# you'll amass, the slower it'll run and the greater likelihood for issues).
#
# It's strongly recommended to check this file into your version control system.

ActiveRecord::Schema.define(:version => 20130522141856) do

  create_table "deploy_keys_projects", :force => true do |t|
    t.integer  "deploy_key_id", :null => false
    t.integer  "project_id",    :null => false
    t.datetime "created_at",    :null => false
    t.datetime "updated_at",    :null => false
  end

  create_table "events", :force => true do |t|
    t.string   "target_type"
    t.integer  "target_id"
    t.string   "title"
    t.text     "data"
    t.integer  "project_id"
    t.datetime "created_at",  :null => false
    t.datetime "updated_at",  :null => false
    t.integer  "action"
    t.integer  "author_id"
  end

  add_index "events", ["action"], :name => "index_events_on_action"
  add_index "events", ["author_id"], :name => "index_events_on_author_id"
  add_index "events", ["created_at"], :name => "index_events_on_created_at"
  add_index "events", ["project_id"], :name => "index_events_on_project_id"
  add_index "events", ["target_id"], :name => "index_events_on_target_id"
  add_index "events", ["target_type"], :name => "index_events_on_target_type"

  create_table "forked_project_links", :force => true do |t|
    t.integer  "forked_to_project_id",   :null => false
    t.integer  "forked_from_project_id", :null => false
    t.datetime "created_at",             :null => false
    t.datetime "updated_at",             :null => false
  end

  add_index "forked_project_links", ["forked_to_project_id"], :name => "index_forked_project_links_on_forked_to_project_id", :unique => true

  create_table "issues", :force => true do |t|
    t.string   "title"
    t.integer  "assignee_id"
    t.integer  "author_id"
    t.integer  "project_id"
    t.datetime "created_at",                  :null => false
    t.datetime "updated_at",                  :null => false
    t.integer  "position",     :default => 0
    t.string   "branch_name"
    t.text     "description"
    t.integer  "milestone_id"
    t.string   "state"
  end

  add_index "issues", ["assignee_id"], :name => "index_issues_on_assignee_id"
  add_index "issues", ["author_id"], :name => "index_issues_on_author_id"
  add_index "issues", ["created_at"], :name => "index_issues_on_created_at"
  add_index "issues", ["milestone_id"], :name => "index_issues_on_milestone_id"
  add_index "issues", ["project_id"], :name => "index_issues_on_project_id"
  add_index "issues", ["title"], :name => "index_issues_on_title"

  create_table "keys", :force => true do |t|
    t.integer  "user_id"
    t.datetime "created_at", :null => false
    t.datetime "updated_at", :null => false
    t.text     "key"
    t.string   "title"
    t.string   "identifier"
    t.string   "type"
  end

  add_index "keys", ["identifier"], :name => "index_keys_on_identifier"
  add_index "keys", ["user_id"], :name => "index_keys_on_user_id"

  create_table "merge_requests", :force => true do |t|
    t.string   "target_branch",                       :null => false
    t.string   "source_branch",                       :null => false
    t.integer  "project_id",                          :null => false
    t.integer  "author_id"
    t.integer  "assignee_id"
    t.string   "title"
    t.datetime "created_at",                          :null => false
    t.datetime "updated_at",                          :null => false
    t.text     "st_commits",    :limit => 2147483647
    t.text     "st_diffs",      :limit => 2147483647
    t.integer  "milestone_id"
    t.string   "state"
    t.string   "merge_status"
  end

  add_index "merge_requests", ["assignee_id"], :name => "index_merge_requests_on_assignee_id"
  add_index "merge_requests", ["author_id"], :name => "index_merge_requests_on_author_id"
  add_index "merge_requests", ["created_at"], :name => "index_merge_requests_on_created_at"
  add_index "merge_requests", ["milestone_id"], :name => "index_merge_requests_on_milestone_id"
  add_index "merge_requests", ["project_id"], :name => "index_merge_requests_on_project_id"
  add_index "merge_requests", ["source_branch"], :name => "index_merge_requests_on_source_branch"
  add_index "merge_requests", ["target_branch"], :name => "index_merge_requests_on_target_branch"
  add_index "merge_requests", ["title"], :name => "index_merge_requests_on_title"

  create_table "milestones", :force => true do |t|
    t.string   "title",       :null => false
    t.integer  "project_id",  :null => false
    t.text     "description"
    t.date     "due_date"
    t.datetime "created_at",  :null => false
    t.datetime "updated_at",  :null => false
    t.string   "state"
  end

  add_index "milestones", ["due_date"], :name => "index_milestones_on_due_date"
  add_index "milestones", ["project_id"], :name => "index_milestones_on_project_id"

  create_table "namespaces", :force => true do |t|
    t.string   "name",                        :null => false
    t.string   "path",                        :null => false
    t.integer  "owner_id",                    :null => false
    t.datetime "created_at",                  :null => false
    t.datetime "updated_at",                  :null => false
    t.string   "type"
    t.string   "description", :default => "", :null => false
  end

  add_index "namespaces", ["name"], :name => "index_namespaces_on_name"
  add_index "namespaces", ["owner_id"], :name => "index_namespaces_on_owner_id"
  add_index "namespaces", ["path"], :name => "index_namespaces_on_path"
  add_index "namespaces", ["type"], :name => "index_namespaces_on_type"

  create_table "notes", :force => true do |t|
    t.text     "note"
    t.string   "noteable_type"
    t.integer  "author_id"
    t.datetime "created_at",    :null => false
    t.datetime "updated_at",    :null => false
    t.integer  "project_id"
    t.string   "attachment"
    t.string   "line_code"
    t.string   "commit_id"
    t.integer  "noteable_id"
  end

  add_index "notes", ["commit_id"], :name => "index_notes_on_commit_id"
  add_index "notes", ["created_at"], :name => "index_notes_on_created_at"
  add_index "notes", ["noteable_type"], :name => "index_notes_on_noteable_type"
  add_index "notes", ["project_id", "noteable_type"], :name => "index_notes_on_project_id_and_noteable_type"
  add_index "notes", ["project_id"], :name => "index_notes_on_project_id"

  create_table "projects", :force => true do |t|
    t.string   "name"
    t.string   "path"
    t.text     "description"
    t.datetime "created_at",                                   :null => false
    t.datetime "updated_at",                                   :null => false
    t.integer  "creator_id"
    t.string   "default_branch"
    t.boolean  "issues_enabled",         :default => true,     :null => false
    t.boolean  "wall_enabled",           :default => true,     :null => false
    t.boolean  "merge_requests_enabled", :default => true,     :null => false
    t.boolean  "wiki_enabled",           :default => true,     :null => false
    t.integer  "namespace_id"
    t.boolean  "public",                 :default => false,    :null => false
    t.string   "issues_tracker",         :default => "gitlab", :null => false
    t.string   "issues_tracker_id"
    t.boolean  "snippets_enabled",       :default => true,     :null => false
    t.datetime "last_activity_at"
  end

  add_index "projects", ["creator_id"], :name => "index_projects_on_owner_id"
  add_index "projects", ["last_activity_at"], :name => "index_projects_on_last_activity_at"
  add_index "projects", ["namespace_id"], :name => "index_projects_on_namespace_id"

  create_table "protected_branches", :force => true do |t|
    t.integer  "project_id", :null => false
    t.string   "name",       :null => false
    t.datetime "created_at", :null => false
    t.datetime "updated_at", :null => false
  end

  create_table "services", :force => true do |t|
    t.string   "type"
    t.string   "title"
    t.string   "token"
    t.integer  "project_id",                     :null => false
    t.datetime "created_at",                     :null => false
    t.datetime "updated_at",                     :null => false
    t.boolean  "active",      :default => false, :null => false
    t.string   "project_url"
    t.string   "subdomain"
    t.string   "room"
  end

  add_index "services", ["project_id"], :name => "index_services_on_project_id"

  create_table "snippets", :force => true do |t|
    t.string   "title"
    t.text     "content"
    t.integer  "author_id",                    :null => false
    t.integer  "project_id"
    t.datetime "created_at",                   :null => false
    t.datetime "updated_at",                   :null => false
    t.string   "file_name"
    t.datetime "expires_at"
    t.boolean  "private",    :default => true, :null => false
    t.string   "type"
  end

  add_index "snippets", ["created_at"], :name => "index_snippets_on_created_at"
  add_index "snippets", ["expires_at"], :name => "index_snippets_on_expires_at"
  add_index "snippets", ["project_id"], :name => "index_snippets_on_project_id"

  create_table "taggings", :force => true do |t|
    t.integer  "tag_id"
    t.integer  "taggable_id"
    t.string   "taggable_type"
    t.integer  "tagger_id"
    t.string   "tagger_type"
    t.string   "context"
    t.datetime "created_at"
  end

  add_index "taggings", ["tag_id"], :name => "index_taggings_on_tag_id"
  add_index "taggings", ["taggable_id", "taggable_type", "context"], :name => "index_taggings_on_taggable_id_and_taggable_type_and_context"

  create_table "tags", :force => true do |t|
    t.string "name"
  end

  create_table "user_team_project_relationships", :force => true do |t|
    t.integer  "project_id"
    t.integer  "user_team_id"
    t.integer  "greatest_access"
    t.datetime "created_at",      :null => false
    t.datetime "updated_at",      :null => false
  end

  create_table "user_team_user_relationships", :force => true do |t|
    t.integer  "user_id"
    t.integer  "user_team_id"
    t.boolean  "group_admin"
    t.integer  "permission"
    t.datetime "created_at",   :null => false
    t.datetime "updated_at",   :null => false
  end

  create_table "user_teams", :force => true do |t|
    t.string   "name"
    t.string   "path"
    t.integer  "owner_id"
    t.datetime "created_at",                  :null => false
    t.datetime "updated_at",                  :null => false
    t.string   "description", :default => "", :null => false
  end

  create_table "users", :force => true do |t|
    t.string   "email",                  :default => "",    :null => false
    t.string   "encrypted_password",     :default => "",    :null => false
    t.string   "reset_password_token"
    t.datetime "reset_password_sent_at"
    t.datetime "remember_created_at"
    t.integer  "sign_in_count",          :default => 0
    t.datetime "current_sign_in_at"
    t.datetime "last_sign_in_at"
    t.string   "current_sign_in_ip"
    t.string   "last_sign_in_ip"
    t.datetime "created_at",                                :null => false
    t.datetime "updated_at",                                :null => false
    t.string   "name"
    t.boolean  "admin",                  :default => false, :null => false
    t.integer  "projects_limit",         :default => 10
    t.string   "skype",                  :default => "",    :null => false
    t.string   "linkedin",               :default => "",    :null => false
    t.string   "twitter",                :default => "",    :null => false
    t.string   "authentication_token"
    t.integer  "theme_id",               :default => 1,     :null => false
    t.string   "bio"
    t.integer  "failed_attempts",        :default => 0
    t.datetime "locked_at"
    t.string   "extern_uid"
    t.string   "provider"
    t.string   "username"
    t.boolean  "can_create_group",       :default => true,  :null => false
    t.boolean  "can_create_team",        :default => true,  :null => false
    t.string   "state"
    t.integer  "color_scheme_id",        :default => 1,     :null => false
    t.integer  "notification_level",     :default => 1,     :null => false
  end

  add_index "users", ["admin"], :name => "index_users_on_admin"
  add_index "users", ["email"], :name => "index_users_on_email", :unique => true
  add_index "users", ["extern_uid", "provider"], :name => "index_users_on_extern_uid_and_provider", :unique => true
  add_index "users", ["name"], :name => "index_users_on_name"
  add_index "users", ["reset_password_token"], :name => "index_users_on_reset_password_token", :unique => true
  add_index "users", ["username"], :name => "index_users_on_username"

  create_table "users_projects", :force => true do |t|
    t.integer  "user_id",                           :null => false
    t.integer  "project_id",                        :null => false
    t.datetime "created_at",                        :null => false
    t.datetime "updated_at",                        :null => false
    t.integer  "project_access",     :default => 0, :null => false
    t.integer  "notification_level", :default => 3, :null => false
  end

  add_index "users_projects", ["project_access"], :name => "index_users_projects_on_project_access"
  add_index "users_projects", ["project_id"], :name => "index_users_projects_on_project_id"
  add_index "users_projects", ["user_id"], :name => "index_users_projects_on_user_id"

  create_table "web_hooks", :force => true do |t|
    t.string   "url"
    t.integer  "project_id"
    t.datetime "created_at",                            :null => false
    t.datetime "updated_at",                            :null => false
    t.string   "type",       :default => "ProjectHook"
    t.integer  "service_id"
  end

end
