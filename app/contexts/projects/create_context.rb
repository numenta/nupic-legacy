module Projects
  class CreateContext < BaseContext
    def initialize(user, params)
      @current_user, @params = user, params.dup
    end

    def execute
      # get namespace id
      namespace_id = params.delete(:namespace_id)

      # Load default feature settings
      default_features = Gitlab.config.gitlab.default_projects_features

      default_opts = {
        issues_enabled: default_features.issues,
        wiki_enabled: default_features.wiki,
        wall_enabled: default_features.wall,
        snippets_enabled: default_features.snippets,
        merge_requests_enabled: default_features.merge_requests
      }

      @project = Project.new(default_opts.merge(params))

      # Parametrize path for project
      #
      # Ex.
      #  'GitLab HQ'.parameterize => "gitlab-hq"
      #
      @project.path = @project.name.dup.parameterize


      if namespace_id
        # Find matching namespace and check if it allowed
        # for current user if namespace_id passed.
        if allowed_namespace?(current_user, namespace_id)
          @project.namespace_id = namespace_id unless namespace_id == Namespace.global_id
        else
          deny_namespace
          return @project
        end
      else
        # Set current user namespace if namespace_id is nil
        @project.namespace_id = current_user.namespace_id
      end

      @project.creator = current_user

      # Import project from cloneable resource
      if @project.valid? && @project.import_url.present?
        shell = Gitlab::Shell.new
        if shell.import_repository(@project.path_with_namespace, @project.import_url)
          # We should create satellite for imported repo
          @project.satellite.create unless @project.satellite.exists?
          true
        else
          @project.errors.add(:import_url, 'cannot clone repo')
        end
      end

      if @project.save
        @project.users_projects.create(project_access: UsersProject::MASTER, user: current_user)
      end

      @project
    rescue => ex
      @project.errors.add(:base, "Can't save project. Please try again later")
      @project
    end

    protected

    def deny_namespace
      @project.errors.add(:namespace, "is not valid")
    end

    def allowed_namespace?(user, namespace_id)
      if namespace_id == Namespace.global_id
        return user.admin
      else
        namespace = Namespace.find_by_id(namespace_id)
        current_user.can?(:manage_namespace, namespace)
      end
    end
  end
end
