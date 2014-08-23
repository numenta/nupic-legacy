module Gitlab
  # Custom parser for GitLab-flavored Markdown
  #
  # It replaces references in the text with links to the appropriate items in
  # GitLab.
  #
  # Supported reference formats are:
  #   * @foo for team members
  #   * #123 for issues
  #   * #JIRA-123 for Jira issues
  #   * !123 for merge requests
  #   * $123 for snippets
  #   * 123456 for commits
  #
  # It also parses Emoji codes to insert images. See
  # http://www.emoji-cheat-sheet.com/ for a list of the supported icons.
  #
  # Examples
  #
  #   >> gfm("Hey @david, can you fix this?")
  #   => "Hey <a href="/u/david">@david</a>, can you fix this?"
  #
  #   >> gfm("Commit 35d5f7c closes #1234")
  #   => "Commit <a href="/gitlab/commits/35d5f7c">35d5f7c</a> closes <a href="/gitlab/issues/1234">#1234</a>"
  #
  #   >> gfm(":trollface:")
  #   => "<img alt=\":trollface:\" class=\"emoji\" src=\"/images/trollface.png" title=\":trollface:\" />
  module Markdown
    include IssuesHelper

    attr_reader :html_options

    # Public: Parse the provided text with GitLab-Flavored Markdown
    #
    # text         - the source text
    # html_options - extra options for the reference links as given to link_to
    #
    # Note: reference links will only be generated if @project is set
    def gfm(text, html_options = {})
      return text if text.nil?

      # Duplicate the string so we don't alter the original, then call to_str
      # to cast it back to a String instead of a SafeBuffer. This is required
      # for gsub calls to work as we need them to.
      text = text.dup.to_str

      @html_options = html_options

      # Extract pre blocks so they are not altered
      # from http://github.github.com/github-flavored-markdown/
      text.gsub!(%r{<pre>.*?</pre>|<code>.*?</code>}m) { |match| extract_piece(match) }
      # Extract links with probably parsable hrefs
      text.gsub!(%r{<a.*?>.*?</a>}m) { |match| extract_piece(match) }
      # Extract images with probably parsable src
      text.gsub!(%r{<img.*?>}m) { |match| extract_piece(match) }

      # TODO: add popups with additional information

      text = parse(text)

      # Insert pre block extractions
      text.gsub!(/\{gfm-extraction-(\h{32})\}/) do
        insert_piece($1)
      end

      sanitize text.html_safe, attributes: ActionView::Base.sanitized_allowed_attributes + %w(id class)
    end

    private

    def extract_piece(text)
      @extractions ||= {}

      md5 = Digest::MD5.hexdigest(text)
      @extractions[md5] = text
      "{gfm-extraction-#{md5}}"
    end

    def insert_piece(id)
      @extractions[id]
    end

    # Private: Parses text for references and emoji
    #
    # text - Text to parse
    #
    # Note: reference links will only be generated if @project is set
    #
    # Returns parsed text
    def parse(text)
      parse_references(text) if @project
      parse_emoji(text)

      text
    end

    REFERENCE_PATTERN = %r{
      (?<prefix>\W)?                         # Prefix
      (                                      # Reference
         @(?<user>[a-zA-Z][a-zA-Z0-9_\-\.]*) # User name
        |\#(?<issue>([a-zA-Z]+-)?\d+)        # Issue ID
        |!(?<merge_request>\d+)              # MR ID
        |\$(?<snippet>\d+)                   # Snippet ID
        |(?<commit>[\h]{6,40})               # Commit ID
        |(?<skip>gfm-extraction-[\h]{6,40})  # Skip gfm extractions. Otherwise will be parsed as commit
      )
      (?<suffix>\W)?                         # Suffix
    }x.freeze

    TYPES = [:user, :issue, :merge_request, :snippet, :commit].freeze

    def parse_references(text)
      # parse reference links
      text.gsub!(REFERENCE_PATTERN) do |match|
        prefix     = $~[:prefix]
        suffix     = $~[:suffix]
        type       = TYPES.select{|t| !$~[t].nil?}.first

        if type
          identifier = $~[type]

          # Avoid HTML entities
          if prefix && suffix && prefix[0] == '&' && suffix[-1] == ';'
            match
          elsif ref_link = reference_link(type, identifier)
            "#{prefix}#{ref_link}#{suffix}"
          else
            match
          end
        else
          match
        end
      end
    end

    EMOJI_PATTERN = %r{(:(\S+):)}.freeze

    def parse_emoji(text)
      # parse emoji
      text.gsub!(EMOJI_PATTERN) do |match|
        if valid_emoji?($2)
          image_tag(url_to_image("emoji/#{$2}.png"), class: 'emoji', title: $1, alt: $1, size: "20x20")
        else
          match
        end
      end
    end

    # Private: Checks if an emoji icon exists in the image asset directory
    #
    # emoji - Identifier of the emoji as a string (e.g., "+1", "heart")
    #
    # Returns boolean
    def valid_emoji?(emoji)
      Emoji.names.include? emoji
    end

    # Private: Dispatches to a dedicated processing method based on reference
    #
    # reference  - Object reference ("@1234", "!567", etc.)
    # identifier - Object identifier (Issue ID, SHA hash, etc.)
    #
    # Returns string rendered by the processing method
    def reference_link(type, identifier)
      send("reference_#{type}", identifier)
    end

    def reference_user(identifier)
      if member = @project.users_projects.joins(:user).where(users: { username: identifier }).first
        link_to("@#{identifier}", user_path(identifier), html_options.merge(class: "gfm gfm-team_member #{html_options[:class]}")) if member
      end
    end

    def reference_issue(identifier)
      if @project.issue_exists? identifier
        url = url_for_issue(identifier)
        title = title_for_issue(identifier)

        link_to("##{identifier}", url, html_options.merge(title: "Issue: #{title}", class: "gfm gfm-issue #{html_options[:class]}"))
      end
    end

    def reference_merge_request(identifier)
      if merge_request = @project.merge_requests.where(id: identifier).first
        link_to("!#{identifier}", project_merge_request_url(@project, merge_request), html_options.merge(title: "Merge Request: #{merge_request.title}", class: "gfm gfm-merge_request #{html_options[:class]}"))
      end
    end

    def reference_snippet(identifier)
      if snippet = @project.snippets.where(id: identifier).first
        link_to("$#{identifier}", project_snippet_url(@project, snippet), html_options.merge(title: "Snippet: #{snippet.title}", class: "gfm gfm-snippet #{html_options[:class]}"))
      end
    end

    def reference_commit(identifier)
      if @project.valid_repo? && commit = @project.repository.commit(identifier)
        link_to(identifier, project_commit_url(@project, commit), html_options.merge(title: commit.link_title, class: "gfm gfm-commit #{html_options[:class]}"))
      end
    end
  end
end
