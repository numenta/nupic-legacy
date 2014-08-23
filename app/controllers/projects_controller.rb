class ProjectsController < ProjectResourceController
  skip_before_filter :project, only: [:new, :create]
  skip_before_filter :repository, only: [:new, :create]

  # Authorize
  before_filter :authorize_read_project!, except: [:index, :new, :create]
  before_filter :authorize_admin_project!, only: [:edit, :update, :destroy, :transfer]
  before_filter :require_non_empty_project, only: [:blob, :tree, :graph]

  layout 'navless', only: [:new, :create]
  before_filter :set_title, only: [:new, :create]

  def new
    @project = Project.new
  end

  def edit
  end

  def create
    @project = ::Projects::CreateContext.new(current_user, params[:project]).execute

    respond_to do |format|
      flash[:notice] = 'Project was successfully created.' if @project.saved?
      format.html do
        if @project.saved?
          redirect_to @project
        else
          render action: "new"
        end
      end
      format.js
    end
  end

  def update
    status = ::Projects::UpdateContext.new(@project, current_user, params).execute

    respond_to do |format|
      if status
        flash[:notice] = 'Project was successfully updated.'
        format.html { redirect_to edit_project_path(@project), notice: 'Project was successfully updated.' }
        format.js
      else
        format.html { render action: "edit" }
        format.js
      end
    end
  end

  def transfer
    ::Projects::TransferContext.new(project, current_user, params).execute
  end

  def show
    limit = (params[:limit] || 20).to_i
    @events = @project.events.recent.limit(limit).offset(params[:offset] || 0)

    respond_to do |format|
      format.html do
        if @project.empty_repo?
          render "projects/empty"
        else
          @last_push = current_user.recent_push(@project.id)
          render :show
        end
      end
      format.js
    end
  end

  def destroy
    return access_denied! unless can?(current_user, :remove_project, project)

    project.team.truncate
    project.destroy

    respond_to do |format|
      format.html { redirect_to root_path }
    end
  end

  def fork
    @project = ::Projects::ForkContext.new(project, current_user).execute

    respond_to do |format|
      format.html do
        if @project.saved? && @project.forked?
          redirect_to(@project, notice: 'Project was successfully forked.')
        else
          render action: "new"
        end
      end
      format.js
    end
  end

  def autocomplete_sources
    @suggestions = {
      emojis: Emoji.names,
      issues: @project.issues.select([:id, :title, :description]),
      members: @project.users.select([:username, :name]).order(:username)
    }

    respond_to do |format|
      format.json { render :json => @suggestions }
    end
  end

  private

  def set_title
    @title = 'New Project'
  end
end
