require 'spec_helper'

describe DeployKeysProject do
  describe "Associations" do
    it { should belong_to(:deploy_key) }
    it { should belong_to(:project) }
  end

  describe "Validation" do
    it { should validate_presence_of(:project_id) }
    it { should validate_presence_of(:deploy_key_id) }
  end
end
