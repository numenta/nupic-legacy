module IssuesHelper
  def project_issues_filter_path project, params = {}
    params[:f] ||= cookies['issue_filter']
    project_issues_path project, params
  end

  def issue_css_classes issue
    classes = "issue"
    classes << " closed" if issue.closed?
    classes << " today" if issue.today?
    classes
  end

  # Returns an OpenStruct object suitable for use by <tt>options_from_collection_for_select</tt>
  # to allow filtering issues by an unassigned User or Milestone
  def unassigned_filter
    # Milestone uses :title, Issue uses :name
    OpenStruct.new(id: 0, title: 'Unspecified', name: 'Unassigned')
  end

  def issues_filter
    {
      all: "all",
      closed: "closed",
      to_me: "assigned-to-me",
      by_me: "created-by-me",
      open: "open"
    }
  end

  def issues_active_milestones
    @project.milestones.active.order("id desc").all
  end

  def url_for_project_issues
    return "" if @project.nil?

    if @project.used_default_issues_tracker?
      project_issues_filter_path(@project)
    else
      url = Gitlab.config.issues_tracker[@project.issues_tracker]["project_url"]
      url.gsub(':project_id', @project.id.to_s)
         .gsub(':issues_tracker_id', @project.issues_tracker_id.to_s)
    end
  end

  def url_for_new_issue
    return "" if @project.nil?

    if @project.used_default_issues_tracker?
      url = new_project_issue_path project_id: @project
    else
      url = Gitlab.config.issues_tracker[@project.issues_tracker]["new_issue_url"]
      url.gsub(':project_id', @project.id.to_s)
        .gsub(':issues_tracker_id', @project.issues_tracker_id.to_s)
    end
  end

  def url_for_issue(issue_id)
    return "" if @project.nil?

    if @project.used_default_issues_tracker?
      url = project_issue_url project_id: @project, id: issue_id
    else
      url = Gitlab.config.issues_tracker[@project.issues_tracker]["issues_url"]
      url.gsub(':id', issue_id.to_s)
        .gsub(':project_id', @project.id.to_s)
        .gsub(':issues_tracker_id', @project.issues_tracker_id.to_s)
    end
  end

  def title_for_issue(issue_id)
    return "" if @project.nil?

    if @project.used_default_issues_tracker? && issue = @project.issues.where(id: issue_id).first
      issue.title
    else
      ""
    end
  end

  def project_issues_with_filter_path(project, opts)
    default_opts = {
      status: params[:status],
      label_name: params[:label_name],
      milestone_id: params[:milestone_id],
      assignee_id: params[:assignee_id],
    }

    project_issues_path(@project, default_opts.merge(opts))
  end
end
