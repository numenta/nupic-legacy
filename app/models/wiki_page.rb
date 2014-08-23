class WikiPage
  include ActiveModel::Validations
  include ActiveModel::Conversion
  include StaticModel
  extend ActiveModel::Naming

  def self.primary_key
    'slug'
  end

  def self.model_name
    ActiveModel::Name.new(self, nil, 'wiki')
  end

  def to_key
    [:slug]
  end

  validates :title, presence: true
  validates :content, presence: true

  # The Gitlab GollumWiki instance.
  attr_reader :wiki

  # The raw Gollum::Page instance.
  attr_reader :page

  # The attributes Hash used for storing and validating
  # new Page values before writing to the Gollum repository.
  attr_accessor :attributes

  def initialize(wiki, page = nil, persisted = false)
    @wiki       = wiki
    @page       = page
    @persisted  = persisted
    @attributes = {}.with_indifferent_access

    set_attributes if persisted?
  end

  # The escaped URL path of this page.
  def slug
    @attributes[:slug]
  end

  alias :to_param :slug

  # The formatted title of this page.
  def title
    @attributes[:title] || ""
  end

  # Sets the title of this page.
  def title=(new_title)
    @attributes[:title] = new_title
  end

  # The raw content of this page.
  def content
    @attributes[:content]
  end

  # The processed/formatted content of this page.
  def formatted_content
    @attributes[:formatted_content]
  end

  # The markup format for the page.
  def format
    @attributes[:format] || :markdown
  end

  # The commit message for this page version.
  def message
    version.try(:message)
  end

  # The Gitlab Commit instance for this page.
  def version
    return nil unless persisted?

    @version ||= Commit.new(Gitlab::Git::Commit.new(@page.version))
  end

  # Returns an array of Gitlab Commit instances.
  def versions
    return [] unless persisted?

    @page.versions.map { |v| Commit.new(Gitlab::Git::Commit.new(v)) }
  end

  # Returns the Date that this latest version was
  # created on.
  def created_at
    @page.version.date
  end

  # Returns boolean True or False if this instance
  # is an old version of the page.
  def historical?
    @page.historical?
  end

  # Returns boolean True or False if this instance
  # has been fully saved to disk or not.
  def persisted?
    @persisted == true
  end

  # Creates a new Wiki Page.
  #
  # attr - Hash of attributes to set on the new page.
  #       :title   - The title for the new page.
  #       :content - The raw markup content.
  #       :format  - Optional symbol representing the
  #                  content format. Can be any type
  #                  listed in the GollumWiki::MARKUPS
  #                  Hash.
  #       :message - Optional commit message to set on
  #                  the new page.
  #
  # Returns the String SHA1 of the newly created page
  # or False if the save was unsuccessful.
  def create(attr = {})
    @attributes.merge!(attr)

    save :create_page, title, content, format, message
  end

  # Updates an existing Wiki Page, creating a new version.
  #
  # new_content - The raw markup content to replace the existing.
  # format      - Optional symbol representing the content format.
  #               See GollumWiki::MARKUPS Hash for available formats.
  # message     - Optional commit message to set on the new version.
  #
  # Returns the String SHA1 of the newly created page
  # or False if the save was unsuccessful.
  def update(new_content = "", format = :markdown, message = nil)
    @attributes[:content] = new_content
    @attributes[:format] = format

    save :update_page, @page, content, format, message
  end

  # Destroys the WIki Page.
  #
  # Returns boolean True or False.
  def delete
    if wiki.delete_page(@page)
      true
    else
      false
    end
  end

  private

  def set_attributes
    attributes[:slug] = @page.escaped_url_path
    attributes[:title] = @page.title
    attributes[:content] = @page.raw_data
    attributes[:formatted_content] = @page.formatted_data
    attributes[:format] = @page.format
  end

  def save(method, *args)
    if valid? && wiki.send(method, *args)
      @page = wiki.wiki.paged(title)

      set_attributes

      @persisted = true
    else
      errors.add(:base, wiki.error_message) if wiki.error_message
      @persisted = false
    end
    @persisted
  end

end
