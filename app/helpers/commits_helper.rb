module CommitsHelper
  # Returns a link to the commit author. If the author has a matching user and
  # is a member of the current @project it will link to the team member page.
  # Otherwise it will link to the author email as specified in the commit.
  #
  # options:
  #  avatar: true will prepend the avatar image
  #  size:   size of the avatar image in px
  def commit_author_link(commit, options = {})
    commit_person_link(commit, options.merge(source: :author))
  end

  # Just like #author_link but for the committer.
  def commit_committer_link(commit, options = {})
    commit_person_link(commit, options.merge(source: :committer))
  end

  def identification_type(line)
    if line[0] == "+"
      "new"
    elsif line[0] == "-"
      "old"
    else
      nil
    end
  end

  def build_line_anchor(diff, line_new, line_old)
    "#{hexdigest(diff.new_path)}_#{line_old}_#{line_new}"
  end

  def each_diff_line(diff, index)
    diff_arr = diff.diff.lines.to_a

    line_old = 1
    line_new = 1
    type = nil

    lines_arr = ::Gitlab::InlineDiff.processing diff_arr
    lines_arr.each do |line|
      next if line.match(/^\-\-\- \/dev\/null/)
      next if line.match(/^\+\+\+ \/dev\/null/)
      next if line.match(/^\-\-\- a/)
      next if line.match(/^\+\+\+ b/)

      full_line = html_escape(line.gsub(/\n/, ''))
      full_line = ::Gitlab::InlineDiff.replace_markers full_line

      if line.match(/^@@ -/)
        type = "match"

        line_old = line.match(/\-[0-9]*/)[0].to_i.abs rescue 0
        line_new = line.match(/\+[0-9]*/)[0].to_i.abs rescue 0

        next if line_old == 1 && line_new == 1 #top of file
        yield(full_line, type, nil, nil, nil)
        next
      else
        type = identification_type(line)
        line_code = build_line_anchor(diff, line_new, line_old)
        yield(full_line, type, line_code, line_new, line_old)
      end


      if line[0] == "+"
        line_new += 1
      elsif line[0] == "-"
        line_old += 1
      else
        line_new += 1
        line_old += 1
      end
    end
  end

  def each_diff_line_near(diff, index, expected_line_code)
    max_number_of_lines = 16

    prev_match_line = nil
    prev_lines = []

    each_diff_line(diff, index) do |full_line, type, line_code, line_new, line_old|
      line = [full_line, type, line_code, line_new, line_old]
      if line_code != expected_line_code
        if type == "match"
          prev_lines.clear
          prev_match_line = line
        else
          prev_lines.push(line)
          prev_lines.shift if prev_lines.length >= max_number_of_lines
        end
      else
        yield(prev_match_line) if !prev_match_line.nil?
        prev_lines.each { |ln| yield(ln) }
        yield(line)
        break
      end
    end
  end

  def image_diff_class(diff)
    if diff.deleted_file
      "deleted"
    elsif diff.new_file
      "added"
    else
      nil
    end
  end

  def commit_to_html commit
    escape_javascript(render 'commits/commit', commit: commit)
  end

  def diff_line_content(line)
    if line.blank?
      " &nbsp;"
    else
      line
    end
  end

  # Breadcrumb links for a Project and, if applicable, a tree path
  def commits_breadcrumbs
    return unless @project && @ref

    # Add the root project link and the arrow icon
    crumbs = content_tag(:li) do
      content_tag(:span, nil, class: 'arrow') +
      link_to(@project.name, project_commits_path(@project, @ref))
    end

    if @path
      parts = @path.split('/')

      parts.each_with_index do |part, i|
        crumbs += content_tag(:span, '/', class: 'divider')
        crumbs += content_tag(:li) do
          # The text is just the individual part, but the link needs all the parts before it
          link_to part, project_commits_path(@project, tree_join(@ref, parts[0..i].join('/')))
        end
      end
    end

    crumbs.html_safe
  end

  protected

  # Private: Returns a link to a person. If the person has a matching user and
  # is a member of the current @project it will link to the team member page.
  # Otherwise it will link to the person email as specified in the commit.
  #
  # options:
  #  source: one of :author or :committer
  #  avatar: true will prepend the avatar image
  #  size:   size of the avatar image in px
  def commit_person_link(commit, options = {})
    source_name = commit.send "#{options[:source]}_name".to_sym
    source_email = commit.send "#{options[:source]}_email".to_sym
    text = if options[:avatar]
            avatar = image_tag(gravatar_icon(source_email, options[:size]), class: "avatar #{"s#{options[:size]}" if options[:size]}", width: options[:size], alt: "")
            %Q{#{avatar} <span class="commit-#{options[:source]}-name">#{source_name}</span>}
          else
            source_name
          end

    user = User.where('name like ? or email like ?', source_name, source_email).first

    if user.nil?
      mail_to(source_email, text.html_safe, class: "commit-#{options[:source]}-link")
    else
      link_to(text.html_safe, user_path(user), class: "commit-#{options[:source]}-link")
    end
  end
end
