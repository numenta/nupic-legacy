class TeamMembersController < ProjectResourceController
  # Authorize
  before_filter :authorize_read_project!
  before_filter :authorize_admin_project!, except: [:index, :show]

  def index
    @team = @project.users_projects.scoped
    @team = @team.send(params[:type]) if %w(masters developers reporters guests).include?(params[:type])
    @team = @team.sort_by(&:project_access).reverse.group_by(&:project_access)

    @assigned_teams = @project.user_team_project_relationships
  end

  def new
    @user_project_relation = project.users_projects.new
  end

  def create
    users = User.where(id: params[:user_ids].split(','))

    @project.team << [users, params[:project_access]]

    if params[:redirect_to]
      redirect_to params[:redirect_to]
    else
      redirect_to project_team_index_path(@project)
    end
  end

  def update
    @user_project_relation = project.users_projects.find_by_user_id(member)
    @user_project_relation.update_attributes(params[:team_member])

    unless @user_project_relation.valid?
      flash[:alert] = "User should have at least one role"
    end
    redirect_to project_team_index_path(@project)
  end

  def destroy
    @user_project_relation = project.users_projects.find_by_user_id(member)
    @user_project_relation.destroy

    respond_to do |format|
      format.html { redirect_to project_team_index_path(@project) }
      format.js { render nothing: true }
    end
  end

  def apply_import
    giver = Project.find(params[:source_project_id])
    status = @project.team.import(giver)
    notice = status ? "Succesfully imported" : "Import failed"

    redirect_to project_team_index_path(project), notice: notice
  end

  protected

  def member
    @member ||= User.find_by_username(params[:id])
  end
end
