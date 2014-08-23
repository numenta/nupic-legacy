module API
  # MergeRequest API
  class MergeRequests < Grape::API
    before { authenticate! }

    resource :projects do
      helpers do
        def handle_merge_request_errors!(errors)
          if errors[:project_access].any?
            error!(errors[:project_access], 422)
          elsif errors[:branch_conflict].any?
            error!(errors[:branch_conflict], 422)
          end
          not_found!
        end
      end

      # List merge requests
      #
      # Parameters:
      #   id (required) - The ID of a project
      #
      # Example:
      #   GET /projects/:id/merge_requests
      #
      get ":id/merge_requests" do
        authorize! :read_merge_request, user_project

        present paginate(user_project.merge_requests), with: Entities::MergeRequest
      end

      # Show MR
      #
      # Parameters:
      #   id (required)               - The ID of a project
      #   merge_request_id (required) - The ID of MR
      #
      # Example:
      #   GET /projects/:id/merge_request/:merge_request_id
      #
      get ":id/merge_request/:merge_request_id" do
        merge_request = user_project.merge_requests.find(params[:merge_request_id])

        authorize! :read_merge_request, merge_request

        present merge_request, with: Entities::MergeRequest
      end

      # Create MR
      #
      # Parameters:
      #
      #   id (required)            - The ID of a project
      #   source_branch (required) - The source branch
      #   target_branch (required) - The target branch
      #   assignee_id              - Assignee user ID
      #   title (required)         - Title of MR
      #
      # Example:
      #   POST /projects/:id/merge_requests
      #
      post ":id/merge_requests" do
        authorize! :write_merge_request, user_project
        required_attributes! [:source_branch, :target_branch, :title]

        attrs = attributes_for_keys [:source_branch, :target_branch, :assignee_id, :title]
        merge_request = user_project.merge_requests.new(attrs)
        merge_request.author = current_user

        if merge_request.save
          merge_request.reload_code
          present merge_request, with: Entities::MergeRequest
        else
          handle_merge_request_errors! merge_request.errors
        end
      end

      # Update MR
      #
      # Parameters:
      #   id (required)               - The ID of a project
      #   merge_request_id (required) - ID of MR
      #   source_branch               - The source branch
      #   target_branch               - The target branch
      #   assignee_id                 - Assignee user ID
      #   title                       - Title of MR
      #   state_event                 - Status of MR. (close|reopen|merge)
      # Example:
      #   PUT /projects/:id/merge_request/:merge_request_id
      #
      put ":id/merge_request/:merge_request_id" do
        attrs = attributes_for_keys [:source_branch, :target_branch, :assignee_id, :title, :state_event]
        merge_request = user_project.merge_requests.find(params[:merge_request_id])

        authorize! :modify_merge_request, merge_request

        MergeRequestObserver.current_user = current_user

        if merge_request.update_attributes attrs
          merge_request.reload_code
          merge_request.mark_as_unchecked
          present merge_request, with: Entities::MergeRequest
        else
          handle_merge_request_errors! merge_request.errors
        end
      end

      # Post comment to merge request
      #
      # Parameters:
      #   id (required) - The ID of a project
      #   merge_request_id (required) - ID of MR
      #   note (required) - Text of comment
      # Examples:
      #   POST /projects/:id/merge_request/:merge_request_id/comments
      #
      post ":id/merge_request/:merge_request_id/comments" do
        required_attributes! [:note]

        merge_request = user_project.merge_requests.find(params[:merge_request_id])
        note = merge_request.notes.new(note: params[:note], project_id: user_project.id)
        note.author = current_user

        if note.save
          present note, with: Entities::MRNote
        else
          not_found!
        end
      end

    end
  end
end
