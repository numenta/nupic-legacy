namespace :gitlab do
  namespace :env do
    desc "GITLAB | Show information about GitLab and its environment"
    task info: :environment  do

      # check if there is an RVM environment
      rvm_version = run_and_match("rvm --version", /[\d\.]+/).try(:to_s)
      # check Ruby version
      ruby_version = run_and_match("ruby --version", /[\d\.p]+/).try(:to_s)
      # check Gem version
      gem_version = run("gem --version")
      # check Bundler version
      bunder_version = run_and_match("bundle --version", /[\d\.]+/).try(:to_s)
      # check Bundler version
      rake_version = run_and_match("rake --version", /[\d\.]+/).try(:to_s)

      puts ""
      puts "System information".yellow
      puts "System:\t\t#{os_name || "unknown".red}"
      puts "Current User:\t#{`whoami`}"
      puts "Using RVM:\t#{rvm_version.present? ? "yes".green : "no"}"
      puts "RVM Version:\t#{rvm_version}" if rvm_version.present?
      puts "Ruby Version:\t#{ruby_version || "unknown".red}"
      puts "Gem Version:\t#{gem_version || "unknown".red}"
      puts "Bundler Version:#{bunder_version || "unknown".red}"
      puts "Rake Version:\t#{rake_version || "unknown".red}"


      # check database adapter
      database_adapter = ActiveRecord::Base.connection.adapter_name.downcase

      project = Project.new(path: "some-project")
      project.path = "some-project"
      # construct clone URLs
      http_clone_url = project.http_url_to_repo
      ssh_clone_url  = project.ssh_url_to_repo

      omniauth_providers = Gitlab.config.omniauth.providers
      omniauth_providers.map! { |provider| provider['name'] }

      puts ""
      puts "GitLab information".yellow
      puts "Version:\t#{Gitlab::VERSION}"
      puts "Revision:\t#{Gitlab::REVISION}"
      puts "Directory:\t#{Rails.root}"
      puts "DB Adapter:\t#{database_adapter}"
      puts "URL:\t\t#{Gitlab.config.gitlab.url}"
      puts "HTTP Clone URL:\t#{http_clone_url}"
      puts "SSH Clone URL:\t#{ssh_clone_url}"
      puts "Using LDAP:\t#{Gitlab.config.ldap.enabled ? "yes".green : "no"}"
      puts "Using Omniauth:\t#{Gitlab.config.omniauth.enabled ? "yes".green : "no"}"
      puts "Omniauth Providers: #{omniauth_providers.map(&:magenta).join(', ')}" if Gitlab.config.omniauth.enabled



      # check Gitolite version
      gitlab_shell_version_file = "#{Gitlab.config.gitlab_shell.repos_path}/../gitlab-shell/VERSION"
      if File.readable?(gitlab_shell_version_file)
        gitlab_shell_version = File.read(gitlab_shell_version_file)
      end

      puts ""
      puts "GitLab Shell".yellow
      puts "Version:\t#{gitlab_shell_version || "unknown".red}"
      puts "Repositories:\t#{Gitlab.config.gitlab_shell.repos_path}"
      puts "Hooks:\t\t#{Gitlab.config.gitlab_shell.hooks_path}"
      puts "Git:\t\t#{Gitlab.config.git.bin_path}"

    end
  end
end
