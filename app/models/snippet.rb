# == Schema Information
#
# Table name: snippets
#
#  id         :integer          not null, primary key
#  title      :string(255)
#  content    :text
#  author_id  :integer          not null
#  project_id :integer          not null
#  created_at :datetime         not null
#  updated_at :datetime         not null
#  file_name  :string(255)
#  expires_at :datetime
#  type       :string(255)
#  private    :boolean

class Snippet < ActiveRecord::Base
  include Linguist::BlobHelper

  attr_accessible :title, :content, :file_name, :expires_at, :private

  belongs_to :author, class_name: "User"

  has_many :notes, as: :noteable, dependent: :destroy

  delegate :name, :email, to: :author, prefix: true, allow_nil: true

  validates :author, presence: true
  validates :title, presence: true, length: { within: 0..255 }
  validates :file_name, presence: true, length: { within: 0..255 }
  validates :content, presence: true

  # Scopes
  scope :public,  -> { where(private: false) }
  scope :private, -> { where(private: true) }
  scope :fresh,   -> { order("created_at DESC") }
  scope :expired, -> { where(["expires_at IS NOT NULL AND expires_at < ?", Time.current]) }
  scope :non_expired, -> { where(["expires_at IS NULL OR expires_at > ?", Time.current]) }

  def self.content_types
    [
      ".rb", ".py", ".pl", ".scala", ".c", ".cpp", ".java",
      ".haml", ".html", ".sass", ".scss", ".xml", ".php", ".erb",
      ".js", ".sh", ".coffee", ".yml", ".md"
    ]
  end

  def data
    content
  end

  def size
    0
  end

  def name
    file_name
  end

  def mode
    nil
  end

  def expired?
    expires_at && expires_at < Time.current
  end
end
