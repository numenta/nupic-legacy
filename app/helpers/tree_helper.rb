module TreeHelper
  # Sorts a repository's tree so that folders are before files and renders
  # their corresponding partials
  #
  # contents - A Grit::Tree object for the current tree
  def render_tree(tree)
    # Render Folders before Files/Submodules
    folders, files, submodules = tree.trees, tree.blobs, tree.submodules

    tree = ""

    # Render folders if we have any
    tree += render partial: 'tree/tree_item', collection: folders, locals: {type: 'folder'} if folders.present?

    # Render files if we have any
    tree += render partial: 'tree/blob_item', collection: files, locals: {type: 'file'} if files.present?

    # Render submodules if we have any
    tree += render partial: 'tree/submodule_item', collection: submodules if submodules.present?

    tree.html_safe
  end

  # Return an image icon depending on the file type
  #
  # type - String type of the tree item; either 'folder' or 'file'
  def tree_icon(type)
    image = type == 'folder' ? 'file_dir.png' : 'file_txt.png'
    image_tag(image, size: '16x16')
  end

  def tree_hex_class(content)
    "file_#{hexdigest(content.name)}"
  end

  # Public: Determines if a given filename is compatible with GitHub::Markup.
  #
  # filename - Filename string to check
  #
  # Returns boolean
  def markup?(filename)
    filename.end_with?(*%w(.textile .rdoc .org .creole
                           .mediawiki .rst .asciidoc .pod))
  end

  def gitlab_markdown?(filename)
    filename.end_with?(*%w(.mdown .md .markdown))
  end

  def plain_text_readme? filename
    filename == 'README'
  end

  # Simple shortcut to File.join
  def tree_join(*args)
    File.join(*args)
  end

  def allowed_tree_edit?
    if @project.protected_branch? @ref
      can?(current_user, :push_code_to_protected_branches, @project)
    else
      can?(current_user, :push_code, @project)
    end
  end

  def tree_breadcrumbs(tree, max_links = 2)
    if tree.path
      part_path = ""
      parts = tree.path.split("\/")

      yield('..', nil) if parts.count > max_links

      parts.each do |part|
        part_path = File.join(part_path, part) unless part_path.empty?
        part_path = part if part_path.empty?

        next unless parts.last(2).include?(part) if parts.count > max_links
        yield(part, tree_join(tree.ref, part_path))
      end
    end
  end

  def up_dir_path tree
    file = File.join(tree.path, "..")
    tree_join(tree.ref, file)
  end

  def leave_edit_message
    "Leave edit mode?\nAll unsaved changes will be lost."
  end
end
