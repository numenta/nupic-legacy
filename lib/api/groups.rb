module API
  # groups API
  class Groups < Grape::API
    before { authenticate! }

    resource :groups do
      # Get a groups list
      #
      # Example Request:
      #  GET /groups
      get do
        if current_user.admin
          @groups = paginate Group
        else
          @groups = paginate current_user.groups
        end
        present @groups, with: Entities::Group
      end

      # Create group. Available only for admin
      #
      # Parameters:
      #   name (required) - The name of the group
      #   path (required) - The path of the group
      # Example Request:
      #   POST /groups
      post do
        authenticated_as_admin!
        required_attributes! [:name, :path]

        attrs = attributes_for_keys [:name, :path]
        @group = Group.new(attrs)
        @group.owner = current_user

        if @group.save
          present @group, with: Entities::Group
        else
          not_found!
        end
      end

      # Get a single group, with containing projects
      #
      # Parameters:
      #   id (required) - The ID of a group
      # Example Request:
      #   GET /groups/:id
      get ":id" do
        @group = Group.find(params[:id])
        if current_user.admin or current_user.groups.include? @group
          present @group, with: Entities::GroupDetail
        else
          not_found!
        end
      end

      # Transfer a project to the Group namespace
      #
      # Parameters:
      #   id - group id
      #   project_id  - project id
      # Example Request:
      #   POST /groups/:id/projects/:project_id
      post ":id/projects/:project_id" do
        authenticated_as_admin!
        @group = Group.find(params[:id])
        project = Project.find(params[:project_id])
        if project.transfer(@group)
          present @group
        else
          not_found!
        end
      end
    end
  end
end
