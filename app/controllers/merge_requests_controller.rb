require 'gitlab/satellite/satellite'

class MergeRequestsController < ProjectResourceController
  before_filter :module_enabled
  before_filter :merge_request, only: [:edit, :update, :show, :commits, :diffs, :automerge, :automerge_check, :ci_status]
  before_filter :validates_merge_request, only: [:show, :diffs]
  before_filter :define_show_vars, only: [:show, :diffs]

  # Allow read any merge_request
  before_filter :authorize_read_merge_request!

  # Allow write(create) merge_request
  before_filter :authorize_write_merge_request!, only: [:new, :create]

  # Allow modify merge_request
  before_filter :authorize_modify_merge_request!, only: [:close, :edit, :update, :sort]

  def index
    @merge_requests = MergeRequestsLoadContext.new(project, current_user, params).execute
  end

  def show
    respond_to do |format|
      format.html
      format.js

      format.diff  { render text: @merge_request.to_diff }
      format.patch { render text: @merge_request.to_patch }
    end
  end

  def diffs
    @diffs = @merge_request.diffs
    @commit = @merge_request.last_commit

    @comments_allowed = @reply_allowed = true
    @comments_target  = { noteable_type: 'MergeRequest',
                          noteable_id: @merge_request.id }
    @line_notes = @merge_request.notes.where("line_code is not null")
  end

  def new
    @merge_request = @project.merge_requests.new(params[:merge_request])
  end

  def edit
  end

  def create
    @merge_request = @project.merge_requests.new(params[:merge_request])
    @merge_request.author = current_user

    if @merge_request.save
      @merge_request.reload_code
      redirect_to [@project, @merge_request], notice: 'Merge request was successfully created.'
    else
      render action: "new"
    end
  end

  def update
    if @merge_request.update_attributes(params[:merge_request].merge(author_id_of_changes: current_user.id))
      @merge_request.reload_code
      @merge_request.mark_as_unchecked
      redirect_to [@project, @merge_request], notice: 'Merge request was successfully updated.'
    else
      render action: "edit"
    end
  end

  def automerge_check
    if @merge_request.unchecked?
      @merge_request.check_if_can_be_merged
    end
    render json: {merge_status: @merge_request.merge_status_name}
  rescue Gitlab::SatelliteNotExistError
    render json: {merge_status: :no_satellite}
  end

  def automerge
    return access_denied! unless allowed_to_merge?

    if @merge_request.opened? && @merge_request.can_be_merged?
      @merge_request.should_remove_source_branch = params[:should_remove_source_branch]
      @merge_request.automerge!(current_user)
      @status = true
    else
      @status = false
    end
  end

  def branch_from
    @commit = @repository.commit(params[:ref])
  end

  def branch_to
    @commit = @repository.commit(params[:ref])
  end

  def ci_status
    status = project.gitlab_ci_service.commit_status(merge_request.last_commit.sha)
    response = { status: status }

    render json: response
  end

  protected

  def merge_request
    @merge_request ||= @project.merge_requests.find(params[:id])
  end

  def authorize_modify_merge_request!
    return render_404 unless can?(current_user, :modify_merge_request, @merge_request)
  end

  def authorize_admin_merge_request!
    return render_404 unless can?(current_user, :admin_merge_request, @merge_request)
  end

  def module_enabled
    return render_404 unless @project.merge_requests_enabled
  end

  def validates_merge_request
    # Show git not found page if target branch doesn't exist
    return invalid_mr unless @project.repository.branch_names.include?(@merge_request.target_branch)

    # Show git not found page if source branch doesn't exist
    # and there is no saved commits between source & target branch
    return invalid_mr if !@project.repository.branch_names.include?(@merge_request.source_branch) && @merge_request.commits.blank?
  end

  def define_show_vars
    # Build a note object for comment form
    @note = @project.notes.new(noteable: @merge_request)

    # Get commits from repository
    # or from cache if already merged
    @commits = @merge_request.commits

    @allowed_to_merge = allowed_to_merge?
    @show_merge_controls = @merge_request.opened? && @commits.any? && @allowed_to_merge

    @target_type = :merge_request
    @target_id = @merge_request.id
  end

  def allowed_to_merge?
    action = if project.protected_branch?(@merge_request.target_branch)
               :push_code_to_protected_branches
             else
               :push_code
             end

    can?(current_user, action, @project)
  end

  def invalid_mr
    # Render special view for MR with removed source or target branch
    render 'invalid'
  end
end
