class ProjectTeam
  attr_accessor :project

  def initialize(project)
    @project = project
  end

  # Shortcut to add users
  #
  # Use:
  #   @team << [@user, :master]
  #   @team << [@users, :master]
  #
  def << args
    users = args.first

    if users.respond_to?(:each)
      add_users(users, args.second)
    else
      add_user(users, args.second)
    end
  end

  def get_tm user_id
    project.users_projects.find_by_user_id(user_id)
  end

  def add_user(user, access)
    add_users_ids([user.id], access)
  end

  def add_users(users, access)
    add_users_ids(users.map(&:id), access)
  end

  def add_users_ids(user_ids, access)
    UsersProject.add_users_into_projects(
      [project.id],
      user_ids,
      access
    )
  end

  # Remove all users from project team
  def truncate
    UsersProject.truncate_team(project)
  end

  def members
    project.users_projects
  end

  def guests
    members.guests.map(&:user)
  end

  def reporters
    members.reporters.map(&:user)
  end

  def developers
    members.developers.map(&:user)
  end

  def masters
    members.masters.map(&:user)
  end

  def import(source_project)
    target_project = project

    source_team = source_project.users_projects.all
    target_team = target_project.users_projects.all
    target_user_ids = target_team.map(&:user_id)

    source_team.reject! do |tm|
      # Skip if user already present in team
      target_user_ids.include?(tm.user_id)
    end

    source_team.map! do |tm|
      new_tm = tm.dup
      new_tm.id = nil
      new_tm.project_id = target_project.id
      new_tm.skip_git = true
      new_tm
    end

    UsersProject.transaction do
      source_team.each do |tm|
        tm.save
      end
    end

    true
  rescue
    false
  end
end
