# == Schema Information
#
# Table name: keys
#
#  id         :integer          not null, primary key
#  user_id    :integer
#  created_at :datetime         not null
#  updated_at :datetime         not null
#  key        :text
#  title      :string(255)
#  identifier :string(255)
#  project_id :integer
#

require 'spec_helper'

describe Key do
  describe "Associations" do
    it { should belong_to(:user) }
  end

  describe "Mass assignment" do
    it { should_not allow_mass_assignment_of(:project_id) }
    it { should_not allow_mass_assignment_of(:user_id) }
  end

  describe "Validation" do
    it { should validate_presence_of(:title) }
    it { should validate_presence_of(:key) }
    it { should ensure_length_of(:title).is_within(0..255) }
    it { should ensure_length_of(:key).is_within(0..5000) }
  end

  describe "Methods" do
    it { should respond_to :projects }
  end

  context "validation of uniqueness" do
    let(:user) { create(:user) }

    it "accepts the key once" do
      build(:key, user: user).should be_valid
    end

    it "does not accepts the key twice" do
      create(:key, user: user)
      build(:key, user: user).should_not be_valid
    end
  end

  context "validate it is a fingerprintable key" do
    let(:user) { create(:user) }

    it "accepts the fingerprintable key" do
      build(:key, user: user).should be_valid
    end

    it "rejects the unfingerprintable key (contains space in middle)" do
      build(:key_with_a_space_in_the_middle).should_not be_valid
    end

    it "rejects the unfingerprintable key (not a key)" do
      build(:invalid_key).should_not be_valid
    end
  end
end
