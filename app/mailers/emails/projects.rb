module Emails
  module Projects
    def project_access_granted_email(user_project_id)
      @users_project = UsersProject.find user_project_id
      @project = @users_project.project
      mail(to: @users_project.user.email,
           subject: subject("access to project was granted"))
    end


    def project_was_moved_email(user_project_id)
      @users_project = UsersProject.find user_project_id
      @project = @users_project.project
      mail(to: @users_project.user.email,
           subject: subject("project was moved"))
    end
  end
end
