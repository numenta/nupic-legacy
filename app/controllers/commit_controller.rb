# Controller for a specific Commit
#
# Not to be confused with CommitsController, plural.
class CommitController < ProjectResourceController
  # Authorize
  before_filter :authorize_read_project!
  before_filter :authorize_code_access!
  before_filter :require_non_empty_project

  def show
    result = CommitLoadContext.new(project, current_user, params).execute

    @commit = result[:commit]
    git_not_found! unless @commit

    @suppress_diff = result[:suppress_diff]

    @note        = result[:note]
    @line_notes  = result[:line_notes]
    @notes_count = result[:notes_count]
    @target_type = :commit
    @target_id   = @commit.id

    @comments_allowed = @reply_allowed = true
    @comments_target  = { noteable_type: 'Commit',
                          commit_id: @commit.id }

    respond_to do |format|
      format.html do
        if result[:status] == :huge_commit
          render "huge_commit" and return
        end
      end

      format.diff  { render text: @commit.to_diff }
      format.patch { render text: @commit.to_patch }
    end
  end
end
